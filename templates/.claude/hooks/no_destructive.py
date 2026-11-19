#!/usr/bin/env python3
# pitaya template 3.0.0-dev.0 · .claude/hooks/no_destructive.py
"""PreToolUse hook: stop the few shell commands that wipe work and can't be undone.

What it guards against: one command destroying the working tree, the home
directory or uncommitted changes: a recursive `rm` of `/`, `~`, `$HOME`, `.`
or `..`; `git reset --hard`; and `git clean` that forces deletion of
directories or ignored files.

How it decides: it parses each Bash command into simple commands and checks
each one. Quoted text (`echo 'rm -rf /'`) is not a command and is let through.

Limits: it lists only the most common and least recoverable forms; it is not
a sandbox. Only Claude Code runs hooks.

When to remove: when sessions run in a disposable sandbox or container where
nothing outside the checkout can be lost, and transcripts show these commands
are no longer attempted.

Protocol: reads PreToolUse JSON on stdin; prints a hookSpecificOutput
decision to stdout, or nothing to let the call through. Exits 1 with a
message on stderr when the input can't be read (fails open, loudly).
"""

from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path

CONTROL = {"&&", "||", ";", "|", "&", "(", ")"}
WRAPPERS = {"sudo", "command", "env", "time", "nohup", "exec"}
GIT_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
RM_TARGETS = {"/", "/*", "~", "~/", "~/*", "$HOME", "$HOME/", "$HOME/*", "${HOME}", "${HOME}/", ".", "./", "..", "../"}


def segments(command: str) -> list[list[str]]:
    """Split a shell command into simple commands, each a list of words."""
    lexer = shlex.shlex(command.replace("\n", " ; "), posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:  # unbalanced quotes: fall back to plain words
        tokens = command.split()
    out, current = [], []
    for tok in tokens:
        if tok in CONTROL:
            if current:
                out.append(current)
            current = []
        else:
            current.append(tok)
    if current:
        out.append(current)
    return [strip_prefix(seg) for seg in out if seg]


def strip_prefix(words: list[str]) -> list[str]:
    """Drop leading VAR=value assignments and wrappers such as sudo."""
    i = 0
    while i < len(words) and ("=" in words[i] and not words[i].startswith("-") or words[i] in WRAPPERS):
        i += 1
    return words[i:]


def short_flags(args: list[str]) -> str:
    return "".join(a[1:] for a in args if a.startswith("-") and not a.startswith("--"))


def check_rm(args: list[str]) -> str | None:
    recursive = "--recursive" in args or any(c in short_flags(args) for c in "rR")
    if not recursive:
        return None
    for target in (a for a in args if not a.startswith("-")):
        if target in RM_TARGETS:
            return (f"`rm` recursively deletes `{target}`, which can't be undone. "
                    "Instead, delete the specific build or temp directory by name")
    return None


def check_git(words: list[str]) -> str | None:
    i = 1
    while i < len(words) and words[i].startswith("-"):
        i += 2 if words[i] in GIT_OPTS_WITH_VALUE else 1
    if i >= len(words):
        return None
    sub, args = words[i], words[i + 1:]
    if sub == "reset" and "--hard" in args:
        return ("`git reset --hard` throws away uncommitted work. "
                "Instead, use `git stash` to set changes aside, or `git restore <file>` for one file")
    if sub == "clean":
        flags = short_flags(args)
        if "n" in flags or "--dry-run" in args:
            return None
        forced = "f" in flags or "--force" in args
        if forced and any(c in flags for c in "dxX"):
            return ("`git clean` with -d or -x deletes untracked and ignored files for good. "
                    "Instead, run `git clean -n` first to list them, and delete specific paths")
    return None


def decide(payload: dict) -> dict | None:
    if payload.get("tool_name") != "Bash":
        return None
    command = (payload.get("tool_input") or {}).get("command") or ""
    for words in segments(command):
        if not words:
            continue
        program = Path(words[0]).name
        reason = check_rm(words[1:]) if program == "rm" else check_git(words) if program == "git" else None
        if reason:
            return {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"Blocked by .claude/hooks/no_destructive.py: {reason}. "
                    "If it really is needed, ask the user to run it themselves."
                ),
            }
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        decision = decide(payload)
    except Exception as exc:  # fail open, but say so
        print(f"no_destructive.py could not check this call: {exc}", file=sys.stderr)
        return 1
    if decision:
        print(json.dumps({"hookSpecificOutput": decision}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
