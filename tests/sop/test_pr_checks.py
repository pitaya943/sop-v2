"""PR checks (S2): every check has a case that makes it fail, run in a temporary
git repository (no network). Mirrors docs/sop/ci-contract.md section 2."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys

import pytest

import compare_junit
import config
import guards
from conftest import FIXTURES, REPO_ROOT

GIT_ENV = dict(
    os.environ,
    GIT_AUTHOR_NAME="Example Bot", GIT_AUTHOR_EMAIL="bot@example.com",
    GIT_COMMITTER_NAME="Example Bot", GIT_COMMITTER_EMAIL="bot@example.com",
)
BOARD_HEAD = "| Ticket | Milestone | 標題 | 狀態 | PR | 修正輪數 | 備註 |\n| --- | --- | --- | --- | --- | --- | --- |\n"


def ticket(tid="T-001", allowed=("src/**", "tests/**", "docs/evidence/T-001/**"), append_only=(),
           serial=(), screens: bool | None = False, done_when=("tests.test_a::test_ok",)) -> str:
    meta = {
        "id": tid, "title": "Example", "milestone": "M1", "depends_on": [],
        "allowed_paths": list(allowed), "append_only": list(append_only), "serial": list(serial),
        "done_when": list(done_when), "status": "todo",
    }
    if screens is not None:
        meta["screens"] = screens
    return "---\n" + config.dump_yaml(meta) + "---\n\n# " + tid + "\n"


class Repo:
    def __init__(self, path):
        self.path = path
        self.git("init", "-q", "-b", "main")

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.path, env=GIT_ENV, check=True,
                              capture_output=True, text=True).stdout

    def write(self, rel, text):
        target = self.path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    def commit(self, message="change"):
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message)


@pytest.fixture
def repo(tmp_path):
    """milestone/M1 with config, board and ticket T-001; HEAD on ticket/T-001."""
    r = Repo(tmp_path)
    cfg = config.load_yaml_file(FIXTURES / "completed-config.yml")
    cfg["spec_paths"] = ["docs/spec/**"]
    cfg["serial_resources"] = ["db-schema", "lockfile"]
    cfg["append_only_files"] = ["tests/implemented.txt"]
    r.write(".sop/config.yml", config.dump_yaml(cfg))
    r.write("docs/board.md", BOARD_HEAD)
    r.write("docs/tickets/T-001.md", ticket())
    r.write("src/a.py", "one = 1\n")
    r.write("tests/implemented.txt", "R1\nR2\n")
    r.write("docs/spec/rules.md", "rules\n")
    r.write("AGENTS.md", "rules\n")
    r.write(".sop/managed.txt", ".sop/managed.txt\nscripts/sop/\ndocs/tickets/_template.md\nCLAUDE.md\n"
            ".claude/skills/learning/  module:learning\n")
    r.write(".claude/skills/learning/SKILL.md", "learning\n")
    r.write("scripts/sop/guards.py", "# guard\n")
    r.commit("base")
    r.git("checkout", "-q", "-b", "milestone/M1")
    r.git("checkout", "-q", "-b", "ticket/T-001")
    return r


def ctx(repo, head_ref="ticket/T-001", base_ref="milestone/M1", body=""):
    return guards.Ctx(root=repo.path, base=base_ref, head="HEAD", base_ref=base_ref,
                      head_ref=head_ref, pr_body=body)


def on_base(repo, rel, text):
    """Commit a file on milestone/M1 and come back to the ticket branch (merging it in)."""
    repo.git("checkout", "-q", "milestone/M1")
    repo.write(rel, text)
    repo.commit("base update")
    repo.git("checkout", "-q", "ticket/T-001")
    repo.git("merge", "-q", "--no-edit", "milestone/M1")


# ---------------------------------------------------------------------------
# branch-ticket (fail-closed gate for every check)
# ---------------------------------------------------------------------------


def test_branch_ticket_passes_for_a_ticket_branch(repo):
    assert guards.check_branch_ticket(ctx(repo)) == []


@pytest.mark.parametrize("head_ref", ["feature/x", "ticket/T-1a", "ticket/t-001", "ticket/T-001/x"])
def test_branch_ticket_rejects_other_source_branches(repo, head_ref):
    assert guards.check_branch_ticket(ctx(repo, head_ref=head_ref))


def test_branch_ticket_rejects_a_missing_ticket_file(repo):
    repo.git("checkout", "-q", "-b", "ticket/T-099")
    assert "T-099.md not found" in guards.check_branch_ticket(ctx(repo, head_ref="ticket/T-099"))[0]


def test_ticket_from_the_pr_branch_is_ignored(repo):
    """A PR can't add its own ticket: tickets are read from the target branch."""
    repo.git("checkout", "-q", "-b", "ticket/T-002")
    repo.write("docs/tickets/T-002.md", ticket("T-002"))
    repo.commit()
    assert guards.check_branch_ticket(ctx(repo, head_ref="ticket/T-002"))


def test_a_failing_gate_fails_every_check(repo):
    for name in ("path-scope", "readonly-paths", "evidence", "append-only"):
        code, lines = guards.run_check(name, ctx(repo, head_ref="feature/x"))
        assert code == 1 and "ticket/T-<number>" in lines[0], name


def test_the_gate_also_fails_checks_that_never_read_the_ticket(repo, tmp_path):
    """tests / no-weakened-tests / commit-author don't load the ticket themselves."""
    report = junit(tmp_path, "ok.xml", {"a::t": "passed"})
    code, lines = guards.run_check("tests", ctx(repo, head_ref="feature/x"), env={"SOP_JUNIT": str(report)})
    assert code == 1 and "ticket/T-<number>" in lines[0]
    code, _ = guards.run_check("tests", ctx(repo), env={"SOP_JUNIT": str(report)})
    assert code == 0


def test_non_ticket_prs_skip_ticket_checks(repo):
    c = ctx(repo, head_ref="milestone/M1", base_ref="main")
    for check in (guards.check_path_scope, guards.check_readonly_paths, guards.check_evidence):
        assert check(c) == []


# ---------------------------------------------------------------------------
# readonly-paths
# ---------------------------------------------------------------------------


def test_readonly_rejects_rules_and_spec(repo):
    repo.write("AGENTS.md", "changed\n")
    repo.write("docs/spec/rules.md", "changed\n")
    repo.commit()
    problems = guards.check_readonly_paths(ctx(repo))
    assert len(problems) == 2


def test_readonly_covers_template_managed_paths(repo):
    """A ticket PR can't edit the guards that judge it (managed paths are read-only, 14.5)."""
    on_base(repo, "docs/tickets/T-001.md", ticket(allowed=("**",)))
    repo.write("scripts/sop/guards.py", "# always pass\n")
    repo.commit()
    assert any("scripts/sop/guards.py" in p for p in guards.check_readonly_paths(ctx(repo)))


def test_readonly_allows_an_exactly_listed_path(repo):
    on_base(repo, "docs/tickets/T-001.md", ticket(allowed=("src/**", "AGENTS.md")))
    repo.write("AGENTS.md", "changed\n")
    repo.commit()
    assert guards.check_readonly_paths(ctx(repo)) == []


def test_readonly_wildcards_never_open_a_readonly_path(repo):
    """D25: only an exact entry counts; '**' or '.github/**' can't be a back door."""
    on_base(repo, "docs/tickets/T-001.md", ticket(allowed=("**", ".github/**")))
    repo.write(".github/workflows/x.yml", "x\n")
    repo.commit()
    assert guards.check_readonly_paths(ctx(repo))


def test_readonly_passes_for_ordinary_files(repo):
    repo.write("src/a.py", "one = 2\n")
    repo.commit()
    assert guards.check_readonly_paths(ctx(repo)) == []


# ---------------------------------------------------------------------------
# path-scope
# ---------------------------------------------------------------------------


def test_path_scope_rejects_files_outside_allowed_paths(repo):
    repo.write("other/b.py", "x\n")
    repo.commit()
    assert guards.check_path_scope(ctx(repo)) == ["other/b.py (A) is outside T-001's allowed_paths"]


def test_path_scope_checks_both_sides_of_a_rename(repo):
    (repo.path / "other").mkdir()
    repo.git("mv", "src/a.py", "other/a.py")
    repo.commit()
    assert guards.check_path_scope(ctx(repo)) == ["other/a.py (A) is outside T-001's allowed_paths"]


def test_readonly_catches_a_readonly_file_renamed_away(repo):
    """Rename detection is off, so moving AGENTS.md shows up as deleting it."""
    repo.git("mv", "AGENTS.md", "src/AGENTS.md")
    repo.commit()
    assert any("AGENTS.md (D)" in p for p in guards.check_readonly_paths(ctx(repo)))


def test_single_star_does_not_cross_directories():
    assert guards.path_matches("src/*", "src/a.py")
    assert not guards.path_matches("src/*", "src/deep/a.py")
    assert guards.path_matches("src/**", "src/deep/a.py")


def test_path_scope_passes_inside_allowed_paths(repo):
    repo.write("src/a.py", "one = 2\n")
    repo.write("tests/test_a.py", "x\n")
    repo.commit()
    assert guards.check_path_scope(ctx(repo)) == []


def test_ticket_widening_its_own_allowed_paths_does_not_help(repo):
    repo.write("docs/tickets/T-001.md", ticket(allowed=("**",)))
    repo.write("other/b.py", "x\n")
    repo.commit()
    assert any("other/b.py" in p for p in guards.check_path_scope(ctx(repo)))


# ---------------------------------------------------------------------------
# append-only
# ---------------------------------------------------------------------------


def _append_only_ticket(repo, path="tests/implemented.txt"):
    on_base(repo, "docs/tickets/T-001.md", ticket(append_only=(path,)))


def test_append_only_accepts_added_lines(repo):
    _append_only_ticket(repo)
    repo.write("tests/implemented.txt", "R1\nR2\nR3\n")
    repo.commit()
    assert guards.check_append_only(ctx(repo)) == []


def test_append_only_rejects_changed_or_removed_lines(repo):
    _append_only_ticket(repo)
    repo.write("tests/implemented.txt", "R1\nR9\n")
    repo.commit()
    assert any("R2" in p for p in guards.check_append_only(ctx(repo)))


def test_append_only_file_must_be_shared_and_allowed(repo):
    _append_only_ticket(repo, "src/a.py")
    problems = guards.check_append_only(ctx(repo))
    assert any("append_only_files" in p for p in problems)


# ---------------------------------------------------------------------------
# serial-resource
# ---------------------------------------------------------------------------


def _serial_setup(repo, other_state):
    on_base(repo, "docs/tickets/T-002.md", ticket("T-002", serial=("db-schema",)))
    on_base(repo, "docs/tickets/T-001.md", ticket(serial=("db-schema",)))
    on_base(repo, "docs/board.md", BOARD_HEAD
            + "| T-001 | M1 | A | building | — | 0 | |\n"
            + f"| T-002 | M1 | B | {other_state} | — | 0 | |\n")


def test_serial_resource_conflict_with_an_in_progress_ticket(repo):
    _serial_setup(repo, "verifying")
    assert guards.check_serial_resource(ctx(repo)) == [
        "serial resource 'db-schema' is also held by T-002, which is in progress"
    ]


def test_serial_resource_free_once_the_other_ticket_merged(repo):
    _serial_setup(repo, "merged")
    assert guards.check_serial_resource(ctx(repo)) == []


def test_serial_resource_must_be_declared_in_config(repo):
    on_base(repo, "docs/tickets/T-001.md", ticket(serial=("cache",)))
    assert any("isn't in serial_resources" in p for p in guards.check_serial_resource(ctx(repo)))


# ---------------------------------------------------------------------------
# evidence
# ---------------------------------------------------------------------------

FENCE = "`" * 3
GOOD_BODY = f"## 證據 / Evidence\n\n{FENCE}text\n$ scripts/sop/test\n3 passed\n{FENCE}\n"


@pytest.mark.parametrize("body", [
    GOOD_BODY,
    "## Evidence\n\nSee [log](docs/evidence/T-001/run.txt)\n",
    "## 證據\n\nhttps://example.com/x/blob/abc/docs/evidence/T-001/a.png\n",
])
def test_evidence_accepts_a_code_block_or_a_link(repo, body):
    assert guards.check_evidence(ctx(repo, body=body)) == []


@pytest.mark.parametrize("body", [
    "## 完成了什麼\n\nDone.\n",
    "## 證據\n\n<!-- fill in -->\n",
    f"## 證據\n\n{FENCE}\n{FENCE}\n",
    "## 證據\n\nSee docs/evidence/T-002/x.png\n",
])
def test_evidence_rejects_missing_or_empty_proof(repo, body):
    assert guards.check_evidence(ctx(repo, body=body))


def test_evidence_needs_screenshots_when_screens_is_true(repo):
    on_base(repo, "docs/tickets/T-001.md", ticket(screens=True))
    assert any("no screenshot" in p for p in guards.check_evidence(ctx(repo, body=GOOD_BODY)))
    repo.write("docs/evidence/T-001/01-form.png", "png")
    repo.commit()
    assert guards.check_evidence(ctx(repo, body=GOOD_BODY)) == []


def test_evidence_requires_the_screens_field(repo):
    on_base(repo, "docs/tickets/T-001.md", ticket(screens=None))
    assert any("screens" in p for p in guards.check_evidence(ctx(repo, body=GOOD_BODY)))


# ---------------------------------------------------------------------------
# commit-author
# ---------------------------------------------------------------------------


def commit(sha, login, parents=1):
    return {"sha": sha, "parents": [{}] * parents, "author": {"login": login} if login else None}


def test_commit_author_passes_for_the_machine_account():
    assert guards.check_commit_author([commit("a1", "example-bot"), commit("b2", "Example-Bot", 2)],
                                      "example-bot") == []


@pytest.mark.parametrize("commits, fragment", [
    ([commit("a1", "example-owner")], "author is example-owner"),
    ([commit("a1", None)], "can't be matched"),
    ([commit("m1", "example-owner", parents=2)], "merge commit"),
    ([], "no commits"),
])
def test_commit_author_rejects(commits, fragment):
    assert any(fragment in p for p in guards.check_commit_author(commits, "example-bot"))


def test_commit_author_fails_closed_past_the_api_limit():
    commits = [commit(f"{i:040x}", "example-bot") for i in range(guards.API_MAX_COMMITS)]
    assert guards.check_commit_author(commits, "example-bot")


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_fetch_pr_commits_pages_through_results():
    pages = [[commit(str(i), "example-bot") for i in range(100)], [commit("x", "example-bot")]]
    seen = []

    def urlopen(req, timeout):
        seen.append(req.full_url)
        return _Response(json.dumps(pages[len(seen) - 1]).encode())

    commits = guards.fetch_pr_commits("example-owner/example-template", 7, "secret-token", urlopen=urlopen)
    assert len(commits) == 101 and len(seen) == 2
    assert all("secret-token" not in url for url in seen)


def test_fetch_pr_commits_fails_closed_without_leaking_the_token():
    def urlopen(req, timeout):
        raise OSError("connection refused to secret-token")

    with pytest.raises(guards.CheckError) as info:
        guards.fetch_pr_commits("example-owner/example-template", 7, "secret-token", urlopen=urlopen)
    assert "secret-token" not in str(info.value)


def test_commit_author_cli_needs_the_pr_environment(repo):
    code, lines = guards.run_check("commit-author", ctx(repo), env={})
    assert code == 1 and "GITHUB_TOKEN" in lines[0]


# ---------------------------------------------------------------------------
# Disabled checks (C4): read from the TARGET branch's config
# ---------------------------------------------------------------------------


def _disable_on(repo, branch_side_only=False):
    cfg = config.parse_yaml((repo.path / ".sop" / "config.yml").read_text())
    cfg["overrides"]["disabled_guards"] = [{"guard": "path-scope", "reason": "No reason.", "decision": "D-001"}]
    if branch_side_only:
        repo.write(".sop/config.yml", config.dump_yaml(cfg))
        repo.commit()
    else:
        on_base(repo, ".sop/config.yml", config.dump_yaml(cfg))


def test_a_disabled_check_reports_success_with_its_reason(repo):
    _disable_on(repo)
    repo.write("other/b.py", "x\n")
    repo.commit()
    code, lines = guards.run_check("path-scope", ctx(repo))
    assert code == 0 and "disabled (C4)" in lines[0] and "D-001" in lines[0]


def test_a_pr_cannot_disable_a_check_for_itself(repo):
    _disable_on(repo, branch_side_only=True)
    repo.write("other/b.py", "x\n")
    repo.commit()
    code, _ = guards.run_check("path-scope", ctx(repo))
    assert code == 1


def test_sop_ready_can_never_be_disabled(repo):
    assert guards.disabled_reason(ctx(repo), "sop-ready") is None


# ---------------------------------------------------------------------------
# JUnit: tests, no-weakened-tests, done-when
# ---------------------------------------------------------------------------


def junit(tmp_path, name, cases):
    """cases: {test id: passed | failed | error | skipped}."""
    rows = []
    for test_id, outcome in cases.items():
        classname, _, case = test_id.rpartition("::")
        inner = {"passed": "", "failed": "<failure/>", "error": "<error/>", "skipped": "<skipped/>"}[outcome]
        rows.append(f'<testcase classname="{classname}" name="{case}">{inner}</testcase>')
    path = tmp_path / name
    path.write_text(f'<?xml version="1.0"?><testsuites><testsuite>{"".join(rows)}</testsuite></testsuites>')
    return path


def test_load_results_maps_outcomes(tmp_path):
    path = junit(tmp_path, "r.xml", {"a::ok": "passed", "a::bad": "failed", "a::err": "error", "a::skip": "skipped"})
    assert compare_junit.load_results(path) == {"a::ok": "passed", "a::bad": "failed", "a::err": "failed",
                                                "a::skip": "skipped"}


def test_load_results_worst_outcome_wins_for_duplicates(tmp_path):
    path = tmp_path / "dup.xml"
    path.write_text('<testsuite><testcase classname="a" name="t"/><testcase classname="a" name="t">'
                    '<failure/></testcase></testsuite>')
    assert compare_junit.load_results(path) == {"a::t": "failed"}


@pytest.mark.parametrize("content", [None, "not xml", "<testsuite><testcase"])
def test_load_results_returns_none_for_missing_or_broken_reports(tmp_path, content):
    path = tmp_path / "r.xml"
    if content is not None:
        path.write_text(content)
    assert compare_junit.load_results(path) is None


def test_tests_check(tmp_path):
    assert compare_junit.check_tests(junit(tmp_path, "ok.xml", {"a::t": "passed"})) == []
    assert compare_junit.check_tests(junit(tmp_path, "bad.xml", {"a::t": "failed"})) == ["a::t failed"]
    assert compare_junit.check_tests(junit(tmp_path, "empty.xml", {}))
    assert compare_junit.check_tests(tmp_path / "missing.xml")


def test_no_weakened_tests_compares_results():
    base = {"a::t1": "passed", "a::t2": "passed", "a::t3": "failed"}
    assert compare_junit.compare_results(base, {"a::t1": "passed", "a::t2": "passed", "a::new": "passed"}) == []
    problems = compare_junit.compare_results(base, {"a::t1": "skipped"})
    assert problems == ["a::t1 passes on the target branch but is skipped on the PR",
                        "a::t2 passes on the target branch but is not collected on the PR"]


def test_no_weakened_tests_fails_without_both_reports():
    assert len(compare_junit.compare_results(None, None)) == 2
    assert compare_junit.compare_results({"a::t": "passed"}, None)


def test_no_weakened_tests_caps_long_lists():
    base = {f"a::t{i}": "passed" for i in range(40)}
    problems = compare_junit.compare_results(base, {})
    assert len(problems) == compare_junit.MAX_LISTED + 1 and "40 in total" in problems[-1]


def test_done_when_for_a_ticket(repo, tmp_path):
    c = ctx(repo)
    assert compare_junit.check_done_when(c, {"tests.test_a::test_ok": "passed"}) == []
    assert compare_junit.check_done_when(c, {"tests.test_a::test_ok": "failed"})
    assert compare_junit.check_done_when(c, {}) == ["T-001: done_when test tests.test_a::test_ok was not run"]
    assert compare_junit.check_done_when(c, None)


def test_done_when_for_a_milestone_pr_covers_every_ticket(repo):
    repo.git("checkout", "-q", "milestone/M1")
    repo.write("docs/tickets/T-002.md", ticket("T-002", done_when=("tests.test_b::test_b",)))
    repo.write("docs/tickets/T-009.md", ticket("T-009", done_when=("x::other",)).replace("milestone: M1", "milestone: M2"))
    repo.commit()
    c = ctx(repo, head_ref="milestone/M1", base_ref="main")
    c.head = "milestone/M1"
    problems = compare_junit.check_done_when(c, {"tests.test_a::test_ok": "passed"})
    assert problems == ["T-002: done_when test tests.test_b::test_b was not run"]


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------


def test_cli_runs_a_check_from_the_environment(repo):
    repo.write("other/b.py", "x\n")
    repo.commit()
    env = dict(os.environ, CI_BASE_SHA="milestone/M1", CI_HEAD_SHA="HEAD", CI_BASE_REF="milestone/M1",
               CI_HEAD_REF="ticket/T-001", CI_PR_BODY="")
    proc = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "sop" / "guards.py"), "path-scope",
                           "--root", str(repo.path)], env=env, capture_output=True, text=True)
    assert proc.returncode == 1 and "other/b.py" in proc.stdout


def test_every_check_has_a_cli_name():
    assert set(guards.CHECKS) == {"sop-ready", "branch-ticket", "readonly-paths", "path-scope", "append-only",
                                  "serial-resource", "evidence", "commit-author", "tests",
                                  "no-weakened-tests", "done-when"}


def test_guards_workflow_has_one_job_per_check():
    """Required status checks use job names, so every check needs a job of that name."""
    import re

    text = (REPO_ROOT / ".github" / "workflows" / "sop-guards.yml").read_text()
    body = text.split("\njobs:\n", 1)[1]
    # Two-space-indented keys under "jobs:" are the job names; split the body per job.
    chunks = re.split(r"^  ([a-z][a-z-]*):\n", body, flags=re.M)[1:]
    jobs = dict(zip(chunks[0::2], chunks[1::2]))
    assert set(guards.CHECKS) <= set(jobs)
    for name in guards.CHECKS:
        assert "needs: detect" in jobs[name] or "needs: [detect" in jobs[name], name
        assert "needs.detect.outputs.project == 'true'" in jobs[name], name
    assert "&" not in "".join(line for line in text.splitlines() if "steps:" in line)  # no YAML anchors


def test_guards_workflow_never_interpolates_pr_text_into_shell():
    """The PR body and branch names reach scripts only through env (injection safety)."""
    text = (REPO_ROOT / ".github" / "workflows" / "sop-guards.yml").read_text()
    for line in text.splitlines():
        if line.strip().startswith("run:") or line.startswith("          "):
            assert "github.event.pull_request.body" not in line or line.strip().startswith("CI_PR_BODY:")
            assert "${{ github.head_ref" not in line or line.strip().startswith("CI_HEAD_REF:")


def test_setup_guide_lists_exactly_the_required_checks():
    """docs/sop/setup.md step 7 is what the Owner types into the ruleset."""
    import re

    text = (REPO_ROOT / "docs" / "sop" / "setup.md").read_text()
    step7 = text.split("## 7.", 1)[1]
    block = re.search(r"```text\n(.*?)\n```", step7, re.S).group(1)
    assert block.split() == list(guards.CHECKS)


# ---------------------------------------------------------------------------
# Bootstrap and sync PRs may change only their own paths (S3, decision 5)
# ---------------------------------------------------------------------------


def _special_pr(repo, branch):
    repo.git("checkout", "-q", "main")
    repo.git("checkout", "-q", "-b", branch)
    return ctx(repo, head_ref=branch, base_ref="main")


def test_bootstrap_pr_may_fill_config_and_remove_disabled_modules(repo):
    c = _special_pr(repo, "sop/bootstrap")
    repo.write(".sop/bootstrap.yml", "ready: true\n")
    repo.write("README.md", "# Example Project\n")
    repo.git("rm", "-q", "-r", ".claude/skills/learning")
    repo.commit()
    assert guards.check_path_scope(c) == []


def test_bootstrap_pr_may_not_change_template_owned_files(repo):
    c = _special_pr(repo, "sop/bootstrap")
    repo.write("scripts/sop/guards.py", "# weakened\n")
    repo.commit()
    assert guards.check_path_scope(c) == [
        "scripts/sop/guards.py (M): a bootstrap PR may not change template-owned paths "
        "(it may only delete paths of disabled modules)"
    ]


def test_sync_pr_may_change_only_managed_paths(repo):
    c = _special_pr(repo, "sop/sync-v2.1.0")
    repo.write("scripts/sop/guards.py", "# new version\n")
    repo.write("AGENTS.md", "rules v2\n")
    repo.commit()
    assert guards.check_path_scope(c) == []
    repo.write("src/a.py", "sneaked in\n")
    repo.commit()
    assert guards.check_path_scope(c) == [
        "src/a.py (M): a sop-sync PR may change only template-owned paths, AGENTS.md and .sop/config.yml"
    ]


def test_sync_pr_may_add_paths_the_new_version_manages(repo):
    c = _special_pr(repo, "sop/sync-v2.1.0")
    repo.write(".sop/managed.txt", (repo.path / ".sop/managed.txt").read_text() + "docs/sop/new.md\n")
    repo.write("docs/sop/new.md", "new\n")
    repo.commit()
    assert guards.check_path_scope(c) == []
