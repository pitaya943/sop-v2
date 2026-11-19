#!/usr/bin/env python3
"""Stack-neutral sop-v2 guards (design doc 10.1). Standard library only.

S0 implements one guard, ``sop-ready``: the repo-level layer (L2) of the
bootstrap gate (design doc 15). Usage::

    python3 scripts/sop/guards.py sop-ready [--root PATH]

Exit code 0 means the gate is open; 1 means it is closed, with one line per
reason. The list of currently disabled guards (customization layer C4) is
always printed, so every reviewer can see it.

Design choice: like the config validator, sop-ready reports *every* failing
condition rather than stopping at the first, so one run shows all the work left.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import config  # scripts/sop/config.py; scripts/sop is on sys.path when run directly

# Shape of .sop/bootstrap.yml, checked with the same validator as the config.
# It lives in code, not in .sop/schema.json, because it is gate state written
# by the bootstrap skill, not a value the user chooses.
CHECK_IDS = ("B1", "B2", "B3", "B4", "B5", "B6", "B7")
_CHECK_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["status", "evidence"],
    "properties": {
        "status": {"type": "string", "enum": ["pending", "passed", "failed", "not_applicable"]},
        "evidence": {"type": "string"},
    },
}
BOOTSTRAP_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["ready", "checks"],
    "properties": {
        "ready": {"type": "boolean"},
        "checks": {
            "type": "object",
            "additionalProperties": False,
            "required": list(CHECK_IDS),
            "properties": {cid: _CHECK_SCHEMA for cid in CHECK_IDS},
        },
    },
}


@dataclass
class GuardResult:
    ok: bool
    problems: list[str] = field(default_factory=list)
    disabled_guards: list[dict[str, Any]] = field(default_factory=list)


def read_path_list(path: Path) -> list[str]:
    """Read a path list file (.sop/template-only.txt, .sop/managed.txt).

    Blank lines and "#" comments are ignored. Anything after the path on a line
    (such as a "module:<name>" tag) is dropped.
    """
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            entries.append(line.split()[0])
    return entries


def read_template_only(path: Path) -> list[tuple[str, str | None]]:
    """Read .sop/template-only.txt as (path, marker) pairs.

    A plain entry must not exist in a project. An entry with
    ``marker:<text>`` may exist as the project's own file (e.g. its README or
    license) but must not still contain <text>, which only the template's
    version has.
    """
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        rel, _, rest = line.partition(" ")
        rest = rest.strip()
        marker = rest[len("marker:"):].strip() if rest.startswith("marker:") else None
        entries.append((rel, marker or None))
    return entries


def decision_recorded(decision_id: str, decisions_text: str) -> bool:
    """True if ``decision_id`` (e.g. D-007) appears as a whole token.

    "D-007" must not match inside "D-0071" or "XD-007", so a typo can't
    accidentally point at a different decision.
    """
    pattern = rf"(?<![A-Za-z0-9-]){re.escape(decision_id)}(?![0-9])"
    return re.search(pattern, decisions_text) is not None


def sop_ready(root: Path) -> GuardResult:
    root = Path(root)
    sop = root / ".sop"
    problems: list[str] = []
    cfg: Any = None

    # 1. The config exists, parses, and satisfies the schema.
    try:
        cfg = config.load_yaml_file(sop / "config.yml")
    except FileNotFoundError:
        problems.append(".sop/config.yml is missing")
    except config.ConfigSyntaxError as exc:
        problems.append(f".sop/config.yml: {exc}")
    if cfg is not None:
        schema = config.load_schema(sop / "schema.json")
        for v in config.validate(cfg, schema):
            problems.append(f".sop/config.yml: {v}")

    # 2. The bootstrap gate was approved: ready is true and every check is done.
    try:
        boot = config.load_yaml_file(sop / "bootstrap.yml")
    except FileNotFoundError:
        boot = None
        problems.append(".sop/bootstrap.yml is missing")
    except config.ConfigSyntaxError as exc:
        boot = None
        problems.append(f".sop/bootstrap.yml: {exc}")
    if boot is not None:
        shape = config.validate(boot, BOOTSTRAP_SCHEMA)
        problems.extend(f".sop/bootstrap.yml: {v}" for v in shape)
        if not shape:
            if boot["ready"] is not True:
                problems.append(
                    ".sop/bootstrap.yml: ready is not true; run the bootstrap-project "
                    "skill and have the Owner merge its pull request"
                )
            # Consistency: ready may only be true when every check is finished
            # and backed by evidence. Blocks a hand edit of just "ready: true".
            for cid in CHECK_IDS:
                check = boot["checks"][cid]
                if check["status"] in ("pending", "failed"):
                    problems.append(f".sop/bootstrap.yml: check {cid} is {check['status']}")
                elif check["status"] == "passed" and not check["evidence"].strip():
                    problems.append(f".sop/bootstrap.yml: check {cid} is passed but has no evidence")

    # 3. Template-only paths are gone (D10, B7).
    try:
        for rel, marker in read_template_only(sop / "template-only.txt"):
            target = root / rel.rstrip("/")
            if not target.exists():
                continue
            if marker is None:
                problems.append(f"template-only path still present: {rel} (bootstrap removes it)")
            elif target.is_file() and marker in target.read_text(encoding="utf-8", errors="replace"):
                problems.append(
                    f"template-only path still present: {rel} (still the template's version; "
                    "bootstrap replaces or removes it)"
                )
    except FileNotFoundError:
        problems.append(".sop/template-only.txt is missing")

    # 4. Every disabled guard is backed by a recorded decision (C4).
    disabled = _disabled_guards(cfg)
    if disabled:
        decisions = root / "docs" / "decisions.md"
        text = decisions.read_text(encoding="utf-8") if decisions.exists() else None
        for item in disabled:
            ref = item.get("decision")
            if not isinstance(ref, str):
                continue  # already reported by the schema
            if text is None:
                problems.append(
                    f"guard {item.get('guard')!r} is disabled with decision {ref}, "
                    "but docs/decisions.md does not exist"
                )
            elif not decision_recorded(ref, text):
                problems.append(
                    f"guard {item.get('guard')!r} is disabled with decision {ref}, "
                    "which is not recorded in docs/decisions.md"
                )

    return GuardResult(ok=not problems, problems=problems, disabled_guards=disabled)


def _disabled_guards(cfg: Any) -> list[dict[str, Any]]:
    """Read overrides.disabled_guards defensively (the config may be invalid)."""
    try:
        items = cfg["overrides"]["disabled_guards"]
    except (TypeError, KeyError):
        return []
    if not isinstance(items, list):
        return []
    return [i for i in items if isinstance(i, dict)]


def format_disabled(disabled: list[dict[str, Any]]) -> str:
    if not disabled:
        return "Disabled guards (C4): none"
    lines = ["Disabled guards (C4):"]
    for item in disabled:
        lines.append(
            f"  - {item.get('guard')}: {item.get('reason')} (decision {item.get('decision')})"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# PR checks (S2). Each check is check_xxx(ctx) -> list[str]: an empty list
# means pass. The CLI below only fills in Ctx; tests call the functions
# directly against a temporary git repository.
#
# Design (following the reference harness):
#   * Tickets and the config are read from the TARGET branch (ctx.base), never
#     from the PR: otherwise a PR could widen its own allowed_paths, or disable
#     a check, and then pass.
#   * Fail-closed: input that can't be understood is a violation.
# ---------------------------------------------------------------------------

import json  # noqa: E402
import subprocess  # noqa: E402

READONLY = (
    "AGENTS.md", "CLAUDE.md", ".sop/**", "docs/sop/**", ".claude/**", ".github/**",
    "docs/board.md", "docs/decisions.md",
)
IN_PROGRESS = ("building", "verifying", "fixing")
CHECKS = (
    "sop-ready", "branch-ticket", "readonly-paths", "path-scope", "append-only",
    "serial-resource", "evidence", "commit-author", "tests", "no-weakened-tests", "done-when",
)


class CheckError(Exception):
    """The check could not run (e.g. no ticket). Always reported as a failure."""


@dataclass
class Ctx:
    root: Path
    base: str = ""  # target-branch commit (SHA or ref)
    head: str = "HEAD"  # PR head commit
    base_ref: str = ""  # target branch name, e.g. milestone/M1
    head_ref: str = ""  # source branch name, e.g. ticket/T-001
    pr_body: str = ""


# --- git helpers -----------------------------------------------------------


def git(ctx: Ctx, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", *args], cwd=ctx.root, capture_output=True, text=True, check=False)
    if check and r.returncode != 0:
        raise CheckError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r


def show(ctx: Ctx, rev: str, path: str) -> str | None:
    """`git show rev:path`, or None if the file doesn't exist there."""
    r = git(ctx, "show", f"{rev}:{path}", check=False)
    return r.stdout if r.returncode == 0 else None


def tree_files(ctx: Ctx, rev: str, path: str) -> list[str]:
    r = git(ctx, "ls-tree", "-r", "--name-only", rev, "--", path, check=False)
    return [line for line in r.stdout.splitlines() if line]


def changed_files(ctx: Ctx) -> list[tuple[str, str]]:
    """(status, path) for what this PR itself changed.

    Three dots = from the merge base to head, so later changes on the target
    branch don't count. Rename detection is off: a rename is a delete plus an
    add, and both paths must pass.
    """
    out = git(ctx, "diff", "--name-status", "--no-renames", "-z", f"{ctx.base}...{ctx.head}").stdout
    parts = out.split("\0")
    return [(parts[i], parts[i + 1]) for i in range(0, len(parts) - 1, 2)]


def path_matches(pattern: str, path: str) -> bool:
    """`**` crosses directories, `*` doesn't, `?` is one character."""
    rx, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**", i):
            rx += ".*"
            i += 2
        elif pattern[i] == "*":
            rx += "[^/]*"
            i += 1
        elif pattern[i] == "?":
            rx += "[^/]"
            i += 1
        else:
            rx += re.escape(pattern[i])
            i += 1
    return re.fullmatch(rx, path) is not None


def has_wildcard(pattern: str) -> bool:
    return any(c in pattern for c in "*?[")


# --- config and tickets (always from the target branch) ---------------------


def base_config(ctx: Ctx) -> dict:
    text = show(ctx, ctx.base, ".sop/config.yml")
    if text is None:
        raise CheckError(f".sop/config.yml not found on {ctx.base_ref or ctx.base}")
    try:
        return config.parse_yaml(text)
    except config.ConfigSyntaxError as exc:
        raise CheckError(f".sop/config.yml on the target branch: {exc}") from None


FRONT_MATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def parse_ticket(text: str) -> dict:
    match = FRONT_MATTER_RE.match(text)
    if not match:
        raise CheckError("the ticket has no front matter")
    try:
        meta = config.parse_yaml(match.group(1))
    except config.ConfigSyntaxError as exc:
        raise CheckError(f"ticket front matter: {exc}") from None
    for key in ("allowed_paths", "append_only", "serial", "done_when", "depends_on"):
        value = meta.get(key, [])
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise CheckError(f"ticket field {key} must be a list of strings")
        meta[key] = value
    return meta


def ticket_id_of(head_ref: str) -> str | None:
    """The source branch must be exactly ticket/T-<digits>."""
    m = re.fullmatch(r"ticket/(T-\d+)", head_ref)
    return m.group(1) if m else None


def is_ticket_pr(ctx: Ctx) -> bool:
    """Every PR into milestone/* is a ticket PR; so is any PR from ticket/*."""
    return ctx.base_ref.startswith("milestone/") or ctx.head_ref.startswith("ticket/")


def ticket_context(ctx: Ctx) -> tuple[str, dict, str] | None:
    """(ticket ID, front matter, full text) for a ticket PR, else None.

    Fail-closed: a ticket PR whose source branch isn't ticket/T-<digits>, or
    whose ticket file is missing on the target branch, raises CheckError.
    """
    if not is_ticket_pr(ctx):
        return None
    tid = ticket_id_of(ctx.head_ref)
    if tid is None:
        raise CheckError(
            f"a PR into {ctx.base_ref or '(unknown)'} must come from ticket/T-<number>, "
            f"not {ctx.head_ref or '(empty)'}"
        )
    path = f"docs/tickets/{tid}.md"
    text = show(ctx, ctx.base, path)
    if text is None:
        raise CheckError(f"{path} not found on the target branch {ctx.base_ref or ctx.base}")
    return tid, parse_ticket(text), text


def check_branch_ticket(ctx: Ctx) -> list[str]:
    """The gate: run before every check; when it fails, every check fails."""
    try:
        ticket_context(ctx)
    except CheckError as exc:
        return [str(exc)]
    return []


# --- readonly-paths, path-scope ---------------------------------------------


def readonly_patterns(ctx: Ctx) -> list[str]:
    """Fixed read-only paths, the project's spec_paths, and every template-managed
    path from .sop/managed.txt (design doc 14.5), all read from the target branch."""
    spec = base_config(ctx).get("spec_paths") or []
    managed_text = show(ctx, ctx.base, ".sop/managed.txt")
    if managed_text is None:
        raise CheckError(".sop/managed.txt not found on the target branch")
    managed = []
    for line in managed_text.splitlines():
        entry = line.split("#", 1)[0].split()
        if entry:
            managed.append(entry[0] + "**" if entry[0].endswith("/") else entry[0])
    return list(READONLY) + [p for p in spec if isinstance(p, str)] + managed


def check_readonly_paths(ctx: Ctx) -> list[str]:
    tc = ticket_context(ctx)
    if tc is None:
        return []  # not a ticket PR (e.g. milestone/Mx -> main)
    tid, meta, _ = tc
    # D25: only an allowed_paths entry naming the exact path (no wildcard) opens it.
    exact = {p for p in meta["allowed_paths"] if not has_wildcard(p)}
    patterns = readonly_patterns(ctx)
    return [
        f"{tid} may not change {path} ({status}): read-only; list it exactly in allowed_paths if the Owner approved"
        for status, path in changed_files(ctx)
        if any(path_matches(p, path) for p in patterns) and path not in exact
    ]


def managed_entries(text: str | None) -> list[tuple[str, bool]]:
    """(glob, is_module_path) for each entry of a managed.txt text."""
    entries = []
    for line in (text or "").splitlines():
        parts = line.split("#", 1)[0].split()
        if parts:
            glob = parts[0] + "**" if parts[0].endswith("/") else parts[0]
            entries.append((glob, any(t.startswith("module:") for t in parts[1:])))
    return entries


def check_special_pr_scope(ctx: Ctx) -> list[str] | None:
    """Bootstrap and sop-sync PRs may change only their own paths (S3).

    * sop/bootstrap: anything the project owns, but no template-owned path,
      except deleting the paths of a disabled module.
    * sop/sync-*: only template-owned paths (old or new version), AGENTS.md
      (its template sections) and .sop/config.yml (new fields).
    Returns None for any other branch.
    """
    if ctx.head_ref == "sop/bootstrap":
        entries = managed_entries(show(ctx, ctx.base, ".sop/managed.txt"))
        bad = []
        for status, path in changed_files(ctx):
            hits = [is_module for glob, is_module in entries if path_matches(glob, path)]
            if hits and not (status == "D" and any(hits)):
                bad.append(f"{path} ({status}): a bootstrap PR may not change template-owned paths "
                           "(it may only delete paths of disabled modules)")
        return bad
    if ctx.head_ref.startswith("sop/sync-"):
        entries = managed_entries(show(ctx, ctx.base, ".sop/managed.txt"))
        entries += managed_entries(show(ctx, ctx.head, ".sop/managed.txt"))
        allowed = {"AGENTS.md", ".sop/config.yml"}
        return [
            f"{path} ({status}): a sop-sync PR may change only template-owned paths, AGENTS.md and .sop/config.yml"
            for status, path in changed_files(ctx)
            if path not in allowed and not any(path_matches(glob, path) for glob, _ in entries)
        ]
    return None


def check_path_scope(ctx: Ctx) -> list[str]:
    special = check_special_pr_scope(ctx)
    if special is not None:
        return special
    tc = ticket_context(ctx)
    if tc is None:
        return []
    tid, meta, _ = tc
    return [
        f"{path} ({status}) is outside {tid}'s allowed_paths"
        for status, path in changed_files(ctx)
        if not any(path_matches(p, path) for p in meta["allowed_paths"])
    ]


# --- append-only -------------------------------------------------------------


def check_append_only(ctx: Ctx) -> list[str]:
    tc = ticket_context(ctx)
    if tc is None:
        return []
    tid, meta, _ = tc
    shared = set(base_config(ctx).get("append_only_files") or [])
    bad = []
    for path in meta["append_only"]:
        if path not in shared:
            bad.append(f"{tid} declares {path} as append-only, but it isn't in append_only_files")
        if not any(path_matches(p, path) for p in meta["allowed_paths"]):
            bad.append(f"{tid} declares {path} as append-only, but it isn't in allowed_paths")
        diff = git(ctx, "diff", "--no-renames", "-U0", f"{ctx.base}...{ctx.head}", "--", path).stdout
        for line in diff.splitlines():
            if line.startswith("-") and not line.startswith("---"):
                bad.append(f"{path} is append-only, but this PR removes or changes a line: {line[1:].strip()!r}")
    return bad


# --- serial-resource ----------------------------------------------------------


BOARD_ROW_RE = re.compile(r"^\|\s*(T-\d+)\s*\|[^|]*\|[^|]*\|\s*([a-z]+)\s*\|")


def in_progress_tickets(board: str) -> list[str]:
    """Ticket IDs whose board state is building, verifying or fixing (D24 layout)."""
    return [m.group(1) for line in board.splitlines()
            if (m := BOARD_ROW_RE.match(line)) and m.group(2) in IN_PROGRESS]


def check_serial_resource(ctx: Ctx) -> list[str]:
    tc = ticket_context(ctx)
    if tc is None:
        return []
    tid, meta, _ = tc
    known = set(base_config(ctx).get("serial_resources") or [])
    bad = [f"{tid} declares serial resource {r!r}, which isn't in serial_resources"
           for r in meta["serial"] if r not in known]
    board = show(ctx, ctx.base, "docs/board.md")
    if board is None:
        return bad + ["docs/board.md not found on the target branch"]
    for other in in_progress_tickets(board):
        if other == tid:
            continue
        text = show(ctx, ctx.base, f"docs/tickets/{other}.md")
        if text is None:
            bad.append(f"{other} is in progress on the board, but its ticket file is missing")
            continue
        for r in sorted(set(meta["serial"]) & set(parse_ticket(text)["serial"])):
            bad.append(f"serial resource {r!r} is also held by {other}, which is in progress")
    return bad


# --- evidence ------------------------------------------------------------------


IMAGE_RE = re.compile(r"\.(png|jpe?g|gif|webp)$", re.I)
FENCE_RE = re.compile(r"(?ms)^[ \t]*(`{3,}|~{3,})[^\n]*\n(.*?)^[ \t]*\1[ \t]*$")


def evidence_section(pr_body: str) -> str | None:
    """The body of the "## 證據" / "## Evidence" section, comments removed."""
    m = re.search(r"^##[ \t]*(?:證據|Evidence)\b[^\n]*\n(.*?)(?=^##[ \t]|\Z)", pr_body, re.S | re.M | re.I)
    if m is None:
        return None
    return re.sub(r"<!--.*?-->", "", m.group(1), flags=re.S).strip()


def evidence_has_proof(section: str, ticket_id: str) -> bool:
    """A non-empty code block, or a link into docs/evidence/<ticket>/."""
    if any(m.group(2).strip() for m in FENCE_RE.finditer(section)):
        return True
    return re.search(rf"(?:\]\(|https?://)[^)\s]*docs/evidence/{re.escape(ticket_id)}/", section) is not None


def check_evidence(ctx: Ctx) -> list[str]:
    tc = ticket_context(ctx)
    if tc is None:
        return []
    tid, meta, _ = tc
    bad = []
    section = evidence_section(ctx.pr_body)
    if section is None:
        bad.append("the PR description has no evidence section (## 證據 / Evidence)")
    elif not evidence_has_proof(section, tid):
        bad.append(f"the evidence section has no code block and no link to docs/evidence/{tid}/")
    screens = meta.get("screens")
    if not isinstance(screens, bool):
        bad.append(f"{tid} has no screens: true / false in its front matter (D25)")
    elif screens and not [p for p in tree_files(ctx, ctx.head, f"docs/evidence/{tid}") if IMAGE_RE.search(p)]:
        bad.append(f"{tid} has screens: true, but docs/evidence/{tid}/ has no screenshot")
    return bad


# --- commit-author ---------------------------------------------------------------


API_PAGE = 100
API_MAX_COMMITS = 250  # GitHub lists at most 250 commits per PR; beyond that we can't check


def check_commit_author(commits: list[dict], bot_login: str) -> list[str]:
    """commits: objects from GET /repos/{repo}/pulls/{n}/commits. Judged by author.login."""
    if not commits:
        return ["the PR has no commits (empty API response); can't check"]
    bad = []
    for c in commits:
        sha = str(c.get("sha", "?"))[:7]
        kind = "merge commit" if len(c.get("parents") or []) > 1 else "commit"
        author = c.get("author")
        if not author or not author.get("login"):
            bad.append(f"{kind} {sha}: the author can't be matched to a GitHub account")
        elif author["login"].lower() != bot_login.lower():
            bad.append(f"{kind} {sha}: author is {author['login']}, must be the machine account (bot.github)")
    if len(commits) >= API_MAX_COMMITS:
        bad.append(f"the PR has {len(commits)}+ commits, more than the API can list; can't check completely")
    return bad


def fetch_pr_commits(repo: str, number: int, token: str, api: str = "https://api.github.com",
                     urlopen=None) -> list[dict]:
    """Read the PR's commits page by page. The token only goes in a header.

    ``urlopen`` can be injected so tests never touch the network.
    """
    import urllib.request

    urlopen = urlopen or urllib.request.urlopen
    commits: list[dict] = []
    for page in range(1, API_MAX_COMMITS // API_PAGE + 2):
        req = urllib.request.Request(
            f"{api.rstrip('/')}/repos/{repo}/pulls/{number}/commits?per_page={API_PAGE}&page={page}",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        )
        try:
            with urlopen(req, timeout=30) as resp:
                batch = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001  network or permission problem: fail closed
            raise CheckError(f"reading the commits of PR #{number} failed: {type(exc).__name__}") from None
        if not isinstance(batch, list):
            raise CheckError("the GitHub API response is not a list of commits")
        commits += batch
        if len(batch) < API_PAGE:
            break
    return commits


# --- CLI -----------------------------------------------------------------------------


def disabled_reason(ctx: Ctx, name: str) -> str | None:
    """C4: a check listed in overrides.disabled_guards on the TARGET branch is skipped."""
    if name == "sop-ready":
        return None  # the gate can't be disabled
    try:
        items = base_config(ctx)["overrides"]["disabled_guards"] or []
    except (CheckError, KeyError, TypeError):
        return None
    for item in items:
        if isinstance(item, dict) and item.get("guard") == name:
            return f"{item.get('reason')} (decision {item.get('decision')})"
    return None


def run_check(name: str, ctx: Ctx, env: dict | None = None) -> tuple[int, list[str]]:
    """Run one check the way CI does; returns (exit code, output lines)."""
    import compare_junit

    env = env if env is not None else {}
    if name not in CHECKS:
        return 2, [f"unknown check {name!r}; one of: {', '.join(CHECKS)}"]
    reason = disabled_reason(ctx, name)
    if reason:
        return 0, [f"[{name}] disabled (C4): {reason}"]
    problems = check_branch_ticket(ctx)  # fail-closed for every check
    if not problems:
        try:
            if name == "branch-ticket":
                problems = []
            elif name == "sop-ready":
                problems = sop_ready(ctx.root).problems
            elif name == "commit-author":
                if not is_ticket_pr(ctx) and not ctx.base_ref:
                    problems = []  # a push, not a PR
                else:
                    token, repo, number = env.get("GITHUB_TOKEN"), env.get("GITHUB_REPOSITORY"), env.get("CI_PR_NUMBER")
                    if not (token and repo and number):
                        raise CheckError("missing GITHUB_TOKEN / GITHUB_REPOSITORY / CI_PR_NUMBER")
                    bot = base_config(ctx)["bot"]["github"]
                    commits = fetch_pr_commits(repo, int(number), token, env.get("GITHUB_API_URL", "https://api.github.com"))
                    problems = check_commit_author(commits, bot)
            elif name == "tests":
                problems = compare_junit.check_tests(env.get("SOP_JUNIT", "build/sop/junit.xml"))
            elif name == "no-weakened-tests":
                base = compare_junit.load_results(env.get("SOP_BASE_JUNIT", ""))
                head = compare_junit.load_results(env.get("SOP_HEAD_JUNIT", ""))
                problems = compare_junit.compare_results(base, head)
            elif name == "done-when":
                results = compare_junit.load_results(env.get("SOP_JUNIT", "build/sop/junit.xml"))
                problems = compare_junit.check_done_when(ctx, results)
            else:
                problems = globals()["check_" + name.replace("-", "_")](ctx)
        except CheckError as exc:
            problems = [f"can't check: {exc}"]
    lines = [f"[{name}] {p}" for p in problems]
    lines.append(f"[{name}] {'FAIL: ' + str(len(problems)) + ' problem(s)' if problems else 'PASS'}")
    return (1 if problems else 0), lines


def main(argv: list[str] | None = None) -> int:
    import os

    parser = argparse.ArgumentParser(description="sop-v2 guards (docs/sop/ci-contract.md).")
    parser.add_argument("check", choices=CHECKS)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)

    if args.check == "sop-ready" and not os.environ.get("CI_BASE_REF"):
        # Local or push run: the bootstrap gate on the working tree.
        result = sop_ready(args.root)
        print(format_disabled(result.disabled_guards))
        if result.ok:
            print("sop-ready: PASS")
            return 0
        for problem in result.problems:
            print(f"  - {problem}")
        print(f"sop-ready: FAIL ({len(result.problems)} problem(s))")
        return 1

    ctx = Ctx(
        root=args.root,
        base=os.environ.get("CI_BASE_SHA", ""),
        head=os.environ.get("CI_HEAD_SHA", "HEAD"),
        base_ref=os.environ.get("CI_BASE_REF", ""),
        head_ref=os.environ.get("CI_HEAD_REF", ""),
        pr_body=os.environ.get("CI_PR_BODY", ""),
    )
    code, lines = run_check(args.check, ctx, dict(os.environ))
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main())
