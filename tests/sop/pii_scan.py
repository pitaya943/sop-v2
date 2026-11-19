#!/usr/bin/env python3
"""Personal-data scan for the sop-v2 template repo itself (P1, design doc 16).

Template-only: projects created from the template store real accounts in
.sop/config.yml by design, so this scan would only produce noise there.

Approach: an ALLOWLIST. We look for shapes that usually carry personal data
(email addresses, github.com/<account> links, at-mentions) and fail on any value
not explicitly allowed. A blocklist would have to spell out the very data it
hides, so it is not used.

Usage::

    python3 tests/sop/pii_scan.py                       # scan files
    python3 tests/sop/pii_scan.py --commits BASE..HEAD  # also scan commits

Commit scan: authors and committers must use an allowed noreply identity, and
commit messages are scanned like files. Run it on pull-request ranges only:
merge commits made on github.com by the Owner are accepted (design doc 16).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# --- allowlist -------------------------------------------------------------
# Fictional examples and public tool sources only. Compared case-insensitively.
ALLOWED_EMAILS = {
    "noreply@anthropic.com",  # default commit author of Claude sessions
    "noreply@github.com",  # GitHub's committer for web merges
}
ALLOWED_EMAIL_DOMAINS = {"example.com", "example.org", "example.net"}
ALLOWED_ACCOUNTS = {
    "example-owner", "example-bot",  # fictional examples
    "actions",  # official GitHub Actions (github.com/actions/...)
    "apps",  # github.com/apps/<app> pages
}
ALLOWED_MENTIONS = {
    "example-owner", "example-bot",
    "claude",  # the @claude review trigger of the claude_review module
}
# Identities allowed as commit author / committer (exact "Name <email>").
ALLOWED_AUTHORS = {"Claude <noreply@anthropic.com>"}
ALLOWED_COMMITTERS = {"Claude <noreply@anthropic.com>", "GitHub <noreply@github.com>"}

# --- patterns --------------------------------------------------------------
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,})")
ACCOUNT_RE = re.compile(r"github\.com/([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))", re.IGNORECASE)
# An at-sign followed by a login, not preceded by a word char, ".", "/", "@" or
# "-" (so emails and action refs such as "checkout@v4" are not mentions).
MENTION_RE = re.compile(r"(?<![\w./@-])@([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))")
PY_DECORATOR_RE = re.compile(r"^\s*@[A-Za-z_][\w.]*")
# CSS at-rules in .html / .css files are not mentions.
CSS_AT_RULES = {"media", "import", "font-face", "keyframes", "supports", "page", "charset", "layer", "container"}
# A CLAUDE.md line that is only "@<path>" imports that file; it is not a mention.
CLAUDE_IMPORT_RE = re.compile(r"^@[\w./-]+\.md\s*$")


def scan_text(text: str, source: str, python: bool = False) -> list[str]:
    """Return one finding per disallowed match, as "source:line: message"."""
    findings = []
    for number, line in enumerate(text.splitlines(), start=1):
        for m in EMAIL_RE.finditer(line):
            email = m.group(0).lower()
            if email not in ALLOWED_EMAILS and m.group(1).lower() not in ALLOWED_EMAIL_DOMAINS:
                findings.append(f"{source}:{number}: email address {m.group(0)!r}")
        for m in ACCOUNT_RE.finditer(line):
            if m.group(1).lower() not in ALLOWED_ACCOUNTS:
                findings.append(f"{source}:{number}: GitHub account link {m.group(0)!r}")
        if python and PY_DECORATOR_RE.match(line):
            continue  # a Python decorator line is not a mention
        if source.endswith("CLAUDE.md") and CLAUDE_IMPORT_RE.match(line):
            continue
        css = source.endswith((".html", ".css"))
        for m in MENTION_RE.finditer(line):
            if css and m.group(1).lower() in CSS_AT_RULES:
                continue
            if m.group(1).lower() not in ALLOWED_MENTIONS:
                findings.append(f"{source}:{number}: @-mention {m.group(0)!r}")
    return findings


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True
    ).stdout


def repo_files() -> list[str]:
    """Tracked files plus untracked, non-ignored ones (so new files are caught pre-commit)."""
    out = _git("ls-files", "--cached", "--others", "--exclude-standard", "-z")
    return sorted({p for p in out.split("\0") if p and (REPO_ROOT / p).is_file()})


def scan_files(paths: list[str]) -> list[str]:
    findings = []
    for rel in paths:
        try:
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # binary file
        findings += scan_text(text, rel, python=rel.endswith(".py"))
    return findings


def scan_commits(rev_range: str) -> list[str]:
    findings = []
    fmt = "%H%x1f%an <%ae>%x1f%cn <%ce>%x1f%B%x1e"
    for record in _git("log", f"--format={fmt}", rev_range).split("\x1e"):
        record = record.strip("\n")
        if not record:
            continue
        sha, author, committer, message = record.split("\x1f", 3)
        short = sha[:7]
        if author not in ALLOWED_AUTHORS:
            findings.append(f"commit {short}: author {author!r} is not an allowed noreply identity")
        if committer not in ALLOWED_COMMITTERS:
            findings.append(f"commit {short}: committer {committer!r} is not an allowed noreply identity")
        findings += scan_text(message, f"commit {short} message")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--commits", metavar="BASE..HEAD", help="also scan commits in this range")
    args = parser.parse_args(argv)
    try:
        return _run(args)
    except subprocess.CalledProcessError as exc:
        print(f"personal-data scan: ERROR running {' '.join(exc.cmd)}: {exc.stderr.strip()}")
        return 2


def _run(args: argparse.Namespace) -> int:
    files = repo_files()
    findings = scan_files(files)
    scanned = f"{len(files)} files"
    if args.commits:
        findings += scan_commits(args.commits)
        scanned += f" and commits {args.commits}"
    for f in findings:
        print(f)
    if findings:
        print(f"personal-data scan: FAIL ({len(findings)} finding(s) in {scanned})")
        return 1
    print(f"personal-data scan: PASS ({scanned})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
