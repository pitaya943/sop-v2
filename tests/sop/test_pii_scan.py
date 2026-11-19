"""The personal-data scan (P1) catches what it should and nothing else."""

from __future__ import annotations

import os
import subprocess

import pytest

import pii_scan

# Samples are assembled at runtime so that this file itself contains no
# literal personal-data shapes: the scan covers every file with no exceptions.
AT = "@"
GH = "github" + ".com/"


@pytest.mark.parametrize(
    "text",
    [
        "contact: someone.real" + AT + "gmail.com",
        "author 12345+someone" + AT + "users.noreply.github.com",
        "see https://" + GH + "someone-real/private-repo",
        "thanks " + AT + "someone-real for the review",
        "(" + AT + "someone)",
    ],
)
def test_flags_personal_data(text):
    assert pii_scan.scan_text(text, "f.md")


@pytest.mark.parametrize(
    "text",
    [
        "owner: example-owner",
        "Contact person@example.com",
        "Co-Authored-By: Claude <noreply@anthropic.com>",
        "uses: actions/checkout@v4",
        "https://github.com/actions/setup-python",
        "https://github.com/example-owner/example-template",
        "mention @claude to request a review",
        "@example-bot opened the PR",
        "the @-mention workflow",
        "a JSON Pointer like /owner/github",
    ],
)
def test_allows_fictional_and_tool_values(text):
    assert pii_scan.scan_text(text, "f.md") == []


def test_python_decorators_are_not_mentions():
    assert pii_scan.scan_text(AT + "pytest.fixture\ndef f(): pass\n", "t.py", python=True) == []
    assert pii_scan.scan_text(AT + "pytest.fixture\n", "t.md") != []


def test_claude_md_import_is_not_a_mention():
    line = AT + "AGENTS.md\n"
    assert pii_scan.scan_text(line, "CLAUDE.md") == []
    assert pii_scan.scan_text(line, "notes.md") != []  # only CLAUDE.md imports
    assert pii_scan.scan_text("hi " + line, "CLAUDE.md") != []  # whole line only


def test_css_at_rules_are_not_mentions_in_html_only():
    line = AT + "media (prefers-color-scheme: dark) {"
    assert pii_scan.scan_text(line, "report.html") == []
    assert pii_scan.scan_text(line, "notes.md") != []
    assert pii_scan.scan_text(AT + "someone", "report.html") != []


def test_repository_is_clean():
    assert pii_scan.scan_files(pii_scan.repo_files()) == []


def _commit(repo, name, email, message):
    env = dict(
        os.environ,
        GIT_AUTHOR_NAME=name, GIT_AUTHOR_EMAIL=email,
        GIT_COMMITTER_NAME=name, GIT_COMMITTER_EMAIL=email,
    )
    subprocess.run(
        ["git", "commit", "--allow-empty", "-q", "-m", message], cwd=repo, env=env, check=True
    )


@pytest.fixture
def repo(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    _commit(tmp_path, "Claude", "noreply@anthropic.com", "base")
    monkeypatch.setattr(pii_scan, "REPO_ROOT", tmp_path)
    return tmp_path


def test_commit_scan_accepts_noreply_commits(repo):
    _commit(repo, "Claude", "noreply@anthropic.com", "Add x\n\nCo-Authored-By: Claude <noreply@anthropic.com>")
    assert pii_scan.scan_commits("HEAD~1..HEAD") == []


def test_commit_scan_flags_personal_author(repo):
    _commit(repo, "Real Person", "real.person" + AT + "gmail.com", "Add x")
    findings = pii_scan.scan_commits("HEAD~1..HEAD")
    assert any("author" in f for f in findings)
    assert any("committer" in f for f in findings)


def test_commit_scan_flags_personal_data_in_message(repo):
    _commit(repo, "Claude", "noreply@anthropic.com", "Fix bug reported by " + AT + "someone-real")
    assert any(AT + "someone-real" in f for f in pii_scan.scan_commits("HEAD~1..HEAD"))
