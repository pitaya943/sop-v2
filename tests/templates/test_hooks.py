"""The three Level 1 hooks (design section 8, T6), driven the way Claude Code drives them.

Each hook reads the PreToolUse JSON on stdin. It prints a hookSpecificOutput
decision ("deny" or "ask") to stdout, or prints nothing to let the call
through. Every rule is tested both ways: the call it must stop, and a
near-miss it must allow.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS = REPO_ROOT / "templates" / ".claude" / "hooks"


def run_hook(name: str, payload: dict, cwd: Path | None = None, env: dict | None = None) -> dict | None:
    proc = subprocess.run(
        [sys.executable, str(HOOKS / name)],
        input=json.dumps(payload), capture_output=True, text=True,
        cwd=cwd, env=env, timeout=20,
    )
    assert proc.returncode == 0, proc.stderr
    if not proc.stdout.strip():
        return None
    out = json.loads(proc.stdout)["hookSpecificOutput"]
    assert out["hookEventName"] == "PreToolUse"
    return out


def bash(command: str, cwd: Path) -> dict:
    return {"hook_event_name": "PreToolUse", "tool_name": "Bash",
            "tool_input": {"command": command}, "cwd": str(cwd)}


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A git repo on branch `feature`, with origin/HEAD pointing at `main`."""
    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)
    git("init", "-q", "-b", "main")
    git("-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "--allow-empty", "-m", "init")
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    git("checkout", "-q", "-b", "feature")
    return tmp_path


def switch(repo: Path, branch: str) -> None:
    subprocess.run(["git", "checkout", "-q", branch], cwd=repo, check=True, capture_output=True)


# --- no_push_main.py -----------------------------------------------------------

@pytest.mark.parametrize("command", [
    "git push origin main",
    "git push origin HEAD:main",
    "git push origin feature:refs/heads/main",
    "git push origin +feature",                  # forced refspec
    "git push --force origin feature",
    "git push -f origin feature",
    "git push --force-with-lease origin feature",
    "git push origin :feature",                  # deleting a branch
    "git push --delete origin feature",
    "git push --all origin",
    "git push --mirror origin",
    "npm test && git push origin main",          # compound command
    "git -C . push origin master",
])
def test_push_hook_denies(repo, command):
    out = run_hook("no_push_main.py", bash(command, repo))
    assert out and out["permissionDecision"] == "deny", command
    assert "pull request" in out["permissionDecisionReason"].lower()  # says what to do instead


@pytest.mark.parametrize("command", [
    "git push origin feature",
    "git push -u origin feature",
    "git push origin HEAD",                      # current branch is feature
    "git push",                                  # implicit current branch
    "git status",
    "echo 'git push origin main'",               # quoted text, not a push
    "git log origin/main",
])
def test_push_hook_allows(repo, command):
    assert run_hook("no_push_main.py", bash(command, repo)) is None, command


@pytest.mark.parametrize("command", ["git push", "git push origin HEAD", "git push -u origin HEAD"])
def test_push_hook_uses_the_current_branch(repo, command):
    switch(repo, "main")
    out = run_hook("no_push_main.py", bash(command, repo))
    assert out and out["permissionDecision"] == "deny"


def test_push_hook_reads_the_default_branch_from_origin(repo):
    subprocess.run(["git", "update-ref", "refs/remotes/origin/trunk", "HEAD"], cwd=repo, check=True)
    subprocess.run(["git", "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/trunk"], cwd=repo, check=True)
    out = run_hook("no_push_main.py", bash("git push origin trunk", repo))
    assert out and out["permissionDecision"] == "deny"


def test_push_hook_ignores_other_tools(repo):
    payload = {"hook_event_name": "PreToolUse", "tool_name": "Read",
               "tool_input": {"file_path": "x"}, "cwd": str(repo)}
    assert run_hook("no_push_main.py", payload) is None


# --- no_destructive.py ---------------------------------------------------------

@pytest.mark.parametrize("command", [
    "rm -rf /",
    "rm -rf ~",
    "rm -fr ~/",
    "rm -r -f $HOME",
    "rm -rf /*",
    "sudo rm -rf /",
    "rm -rf .",
    "git reset --hard",
    "git reset --hard origin/main",
    "git clean -fdx",
    "git clean -f -d",
    "git clean -xf",
    "cd /tmp && rm -rf ~",
])
def test_destructive_hook_denies(repo, command):
    out = run_hook("no_destructive.py", bash(command, repo))
    assert out and out["permissionDecision"] == "deny", command
    assert "instead" in out["permissionDecisionReason"].lower()


@pytest.mark.parametrize("command", [
    "rm -rf build",
    "rm -rf ./node_modules",
    "rm file.txt",
    "rm -r /tmp/scratch",
    "git reset --soft HEAD~1",
    "git reset HEAD file.txt",
    "git clean -n",
    "git clean -nd",
    "git clean -nfd",                            # dry run, even with -f
    "echo 'rm -rf /'",
])
def test_destructive_hook_allows(repo, command):
    assert run_hook("no_destructive.py", bash(command, repo)) is None, command


# --- ask_on_rule_files.py ------------------------------------------------------

def edit(path: str, cwd: Path, tool: str = "Edit") -> dict:
    key = "notebook_path" if tool == "NotebookEdit" else "file_path"
    return {"hook_event_name": "PreToolUse", "tool_name": tool,
            "tool_input": {key: path}, "cwd": str(cwd)}


@pytest.mark.parametrize("rel", [
    "AGENTS.md", "CLAUDE.md", "docs/agents/harness.md", "src/AGENTS.md",
    ".claude/settings.json", ".claude/hooks/no_push_main.py",
    ".github/workflows/tests.yml",
])
@pytest.mark.parametrize("tool", ["Edit", "Write", "MultiEdit"])
def test_rule_hook_asks_for_rule_files(repo, rel, tool):
    out = run_hook("ask_on_rule_files.py", edit(str(repo / rel), repo, tool))
    assert out and out["permissionDecision"] == "ask", (rel, tool)
    assert rel.split("/")[-1] in out["permissionDecisionReason"]


@pytest.mark.parametrize("rel", ["src/app.py", "docs/guide.md", "README.md", "tests/test_x.py", "docs/agents/notes.md"])
def test_rule_hook_allows_other_files(repo, rel):
    assert run_hook("ask_on_rule_files.py", edit(str(repo / rel), repo)) is None


def test_rule_hook_accepts_relative_paths(repo):
    out = run_hook("ask_on_rule_files.py", edit("AGENTS.md", repo))
    assert out and out["permissionDecision"] == "ask"


@pytest.mark.parametrize("command", [
    "sed -i 's/a/b/' AGENTS.md",
    "echo x >> docs/agents/harness.md",
    "rm .claude/hooks/no_push_main.py",
    "mv .github/workflows/tests.yml /tmp/",
    "cat new > CLAUDE.md",
])
def test_rule_hook_asks_for_shell_writes(repo, command):
    out = run_hook("ask_on_rule_files.py", bash(command, repo))
    assert out and out["permissionDecision"] == "ask", command


@pytest.mark.parametrize("command", ["cat AGENTS.md", "grep -n Level docs/agents/harness.md", "sed -i 's/a/b/' src/app.py"])
def test_rule_hook_allows_shell_reads(repo, command):
    assert run_hook("ask_on_rule_files.py", bash(command, repo)) is None, command


# --- shared behaviour ----------------------------------------------------------

@pytest.mark.parametrize("name", ["no_push_main.py", "no_destructive.py", "ask_on_rule_files.py"])
def test_hook_lets_malformed_input_through(name):
    proc = subprocess.run([sys.executable, str(HOOKS / name)], input="not json",
                          capture_output=True, text=True, timeout=20)
    # Fail open, loudly: a broken hook must not wedge the session, but it reports the problem.
    assert proc.returncode == 1
    assert proc.stdout == ""
    assert proc.stderr.strip()


@pytest.mark.parametrize("name", ["no_push_main.py", "no_destructive.py", "ask_on_rule_files.py"])
def test_hook_documents_when_to_remove_it(name):
    text = (HOOKS / name).read_text()
    assert "When to remove" in text  # design principle R6
