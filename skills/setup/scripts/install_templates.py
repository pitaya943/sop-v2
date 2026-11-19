#!/usr/bin/env python3
"""Copy the pitaya Level 1 templates into a project (design sections 8 and 10).

Usage::

    python3 install_templates.py --target . --level 1 --test-command "pytest -q"
    python3 install_templates.py --target . --level 1 --test-command "pytest -q" --check

Rules, so a re-run is always safe:

* A missing file is created. `<TEST_COMMAND>` is replaced with the project's
  command, and hooks are made executable.
* An existing file is never overwritten. It is reported as `unchanged` (same
  content), `stale` (a copy of an older template version, read from its
  "pitaya template <version>" header), or `differs` (the project's own file).
  Showing the diff and deciding is left to the user.
* `.claude/settings.json` is the exception: it's merged additively. Missing
  permission rules and hook entries are added; nothing is removed or changed.
* `--check` reports what would happen and writes nothing.

Output: one line per file, `<status> <path>`. Exit 0 on success, 2 on bad
arguments. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TEMPLATES = PLUGIN_ROOT / "templates"
SETTINGS = ".claude/settings.json"
DECISIONS = "docs/decisions.md"
PLACEHOLDER = "<TEST_COMMAND>"
HEADER_RE = re.compile(r"pitaya template (\S+)")


def plugin_version() -> str:
    manifest = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
    return json.loads(manifest.read_text())["version"] if manifest.is_file() else "unknown"


def header_version(text: str) -> str | None:
    match = HEADER_RE.search("\n".join(text.splitlines()[:3]))
    return match.group(1) if match else None


def render(rel: str, text: str, test_command: str) -> str:
    if rel == SETTINGS:
        settings = json.loads(text)
        allow = settings.setdefault("permissions", {}).setdefault("allow", [])
        rule = f"Bash({test_command})"
        if rule not in allow:
            allow.append(rule)
        return json.dumps(settings, indent=2) + "\n"
    return text.replace(PLACEHOLDER, test_command)


def merge_settings(existing: dict, ours: dict) -> dict:
    """Add our permission rules and hooks to the project's settings without removing anything."""
    merged = json.loads(json.dumps(existing))
    perms = merged.setdefault("permissions", {})
    for key in ("allow", "deny"):
        current = perms.setdefault(key, [])
        current += [rule for rule in ours.get("permissions", {}).get(key, []) if rule not in current]
    groups = merged.setdefault("hooks", {}).setdefault("PreToolUse", [])
    for group in ours.get("hooks", {}).get("PreToolUse", []):
        same = next((g for g in groups if g.get("matcher") == group.get("matcher")), None)
        if same is None:
            groups.append(json.loads(json.dumps(group)))
            continue
        commands = {h.get("command") for h in same.setdefault("hooks", [])}
        same["hooks"] += [h for h in group["hooks"] if h.get("command") not in commands]
    return merged


def plan_file(rel: str, wanted: str, dest: Path) -> tuple[str, str | None]:
    """Return (status, text to write or None)."""
    if not dest.exists():
        return "created", wanted
    have = dest.read_text()
    if rel == SETTINGS:
        try:
            merged = merge_settings(json.loads(have), json.loads(wanted))
        except json.JSONDecodeError:
            return "differs", None
        if merged == json.loads(have):
            return "unchanged", None
        return "merged", json.dumps(merged, indent=2) + "\n"
    if have == wanted:
        return "unchanged", None
    theirs, ours = header_version(have), header_version(wanted)
    if theirs and ours and theirs != ours:
        return "stale", f"({theirs} -> {ours})"
    return "differs", None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Copy the pitaya Level 1 templates into a project.")
    parser.add_argument("--target", type=Path, default=Path("."))
    parser.add_argument("--level", type=int, choices=(0, 1), required=True,
                        help="0 copies nothing; 1 copies the Level 1 defaults. Levels 2-3 come from recipes.")
    parser.add_argument("--test-command", help="the project's test command, exactly as it runs (required for level 1)")
    parser.add_argument("--no-decisions", action="store_true", help="don't create docs/decisions.md")
    parser.add_argument("--templates", type=Path, default=DEFAULT_TEMPLATES)
    parser.add_argument("--check", action="store_true", help="report only; write nothing")
    args = parser.parse_args(argv)

    if args.level == 0:
        print("level 0: nothing to copy (skills only)")
        return 0
    if not args.test_command:
        parser.error("level 1 needs --test-command, the project's test command exactly as it runs")
    if not args.templates.is_dir():
        parser.error(f"templates not found at {args.templates}; install the pitaya plugin or pass --templates")

    print(f"pitaya templates {plugin_version()} -> {args.target.resolve()}")
    for src in sorted(p for p in args.templates.rglob("*") if p.is_file()):
        rel = src.relative_to(args.templates).as_posix()
        if args.no_decisions and rel == DECISIONS:
            continue
        dest = args.target / rel
        wanted = render(rel, src.read_text(), args.test_command)
        status, payload = plan_file(rel, wanted, dest)
        if status == "stale":
            print(f"{status.ljust(8)} {rel} {payload}")
            continue
        if args.check:
            label = {"created": "would create", "merged": "would merge"}.get(status, status)
            print(f"{label.ljust(8)} {rel}")
            continue
        if payload is not None and status in ("created", "merged"):
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(payload)
            if dest.suffix == ".py" and "/hooks/" in f"/{rel}":
                dest.chmod(0o755)
        print(f"{status.ljust(8)} {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
