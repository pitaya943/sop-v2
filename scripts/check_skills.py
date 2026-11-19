#!/usr/bin/env python3
"""Check the plugin manifests and every SKILL.md (v3 design, sections 4 and 5).

What it guarantees, so the plugin installs the skills we think it does:

* ``.claude-plugin/plugin.json`` has a kebab-case name, a semver version, a
  description, and ``skills`` as a list of ``./skills/<dir>`` paths.
* ``.claude-plugin/marketplace.json`` lists exactly this plugin, sourced from
  the repo root.
* Every listed directory has a SKILL.md, and every directory under
  ``skills/`` is listed (no shipped-by-accident or forgotten skills).
* Each SKILL.md has frontmatter that a strict YAML parser accepts: only known
  keys, ``name`` equal to its directory, a description of 1-1024 characters,
  and a real boolean for ``disable-model-invocation``.
* Each SKILL.md is at most MAX_LINES lines (principle R7: short skills).

Frontmatter parsing is deliberately narrower than YAML: one ``key: value`` per
line, values plain or quoted. Anything outside that subset is reported rather
than guessed at, because a value YAML misreads makes the installer skip the
skill silently. Standard library only, so it runs anywhere without installs.

Usage::

    python3 scripts/check_skills.py [--root PATH]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MAX_LINES = 80
MAX_DESCRIPTION = 1024
KNOWN_KEYS = {"name", "description", "disable-model-invocation", "argument-hint", "allowed-tools"}
BOOLEAN_KEYS = {"disable-model-invocation"}

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
# Semantic Versioning 2.0.0, without build metadata.
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$")
LISTED_RE = re.compile(r"^\./skills/([a-z0-9]+(?:-[a-z0-9]+)*)$")
KEY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9-]*):(?: (.*))?$")
# Plain scalars YAML would read as something other than the string we wrote.
YAML_INDICATORS = tuple("-?:,[]{}#&*!|>'\"%@`")


def _load_json(path: Path, label: str, out: list[str]) -> dict | None:
    if not path.is_file():
        out.append(f"{label}: missing ({path.name} is required)")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        out.append(f"{label}: not valid JSON ({exc.msg}, line {exc.lineno})")
        return None
    if not isinstance(data, dict):
        out.append(f"{label}: must be a JSON object")
        return None
    return data


def check_manifest(root: Path, out: list[str]) -> list[str] | None:
    """Check plugin.json and marketplace.json; return the listed skill paths when usable."""
    plugin = _load_json(root / ".claude-plugin" / "plugin.json", "plugin.json", out)
    market = _load_json(root / ".claude-plugin" / "marketplace.json", "marketplace.json", out)
    if plugin is None:
        return None

    name = plugin.get("name")
    if not isinstance(name, str) or not NAME_RE.match(name):
        out.append(f"plugin.json: name must be kebab-case, got {name!r}")
    version = plugin.get("version")
    if not isinstance(version, str) or not SEMVER_RE.match(version):
        out.append(f"plugin.json: version must be semver (e.g. 3.0.0 or 3.0.0-dev.0), got {version!r}")
    description = plugin.get("description")
    if not isinstance(description, str) or not description.strip():
        out.append("plugin.json: description is required")

    if market is not None:
        entries = market.get("plugins")
        ok = (isinstance(entries, list) and len(entries) == 1 and isinstance(entries[0], dict)
              and entries[0].get("name") == name and entries[0].get("source") == "./")
        if not ok:
            out.append(f'marketplace.json: plugins must be exactly one entry named {name!r} with source "./"')

    listed = plugin.get("skills")
    if not isinstance(listed, list) or not all(isinstance(p, str) for p in listed):
        out.append("plugin.json: skills must be a list of paths like ./skills/<name>")
        return None
    return listed


def parse_frontmatter(text: str) -> tuple[dict[str, str | bool] | None, list[str]]:
    """Parse the leading ---/--- block; return (fields, problems). fields is None without a block."""
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return None, ["no frontmatter (the file must start with a --- line)"]
    try:
        end = lines.index("---", 1)
    except ValueError:
        return None, ["no frontmatter (missing the closing --- line)"]

    fields: dict[str, str | bool] = {}
    errors: list[str] = []
    for number, line in enumerate(lines[1:end], start=2):
        match = KEY_RE.match(line)
        if not match:
            errors.append(f"line {number}: expected 'key: value', got {line!r}")
            continue
        key, raw = match.group(1), (match.group(2) or "").strip()
        if key in fields:
            errors.append(f"line {number}: duplicate key {key!r}")
            continue
        if key not in KNOWN_KEYS:
            errors.append(f"line {number}: unknown key {key!r} (allowed: {', '.join(sorted(KNOWN_KEYS))})")
            continue
        value = _scalar(raw, key, number, errors)
        if value is not None:
            fields[key] = value
    return fields, errors


def _scalar(raw: str, key: str, number: int, errors: list[str]) -> str | bool | None:
    if key in BOOLEAN_KEYS:
        if raw in ("true", "false"):
            return raw == "true"
        errors.append(f"line {number}: {key} must be true or false (unquoted), got {raw!r}")
        return None
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        inner = raw[1:-1]
        if raw[0] == '"' and ('"' in inner.replace('\\"', "") or "\\" in inner.replace('\\"', "")):
            errors.append(f"line {number}: escapes inside double quotes are not supported; rephrase")
            return None
        if raw[0] == "'" and "'" in inner.replace("''", ""):
            errors.append(f"line {number}: a single quote inside single quotes must be doubled ('')")
            return None
        return inner.replace('\\"', '"') if raw[0] == '"' else inner.replace("''", "'")
    if ": " in raw or raw.endswith(":") or " #" in raw:
        errors.append(f"line {number}: {key} contains ': ', ' #' or a trailing ':'; quote the value")
        return None
    if raw.startswith(YAML_INDICATORS):
        errors.append(f"line {number}: {key} starts with a YAML indicator character; quote the value")
        return None
    return raw


def check_skill(root: Path, dirname: str, out: list[str]) -> None:
    where = f"skills/{dirname}/SKILL.md"
    path = root / "skills" / dirname / "SKILL.md"
    if not path.is_file():
        out.append(f"{where}: missing")
        return
    text = path.read_text(encoding="utf-8")
    fields, errors = parse_frontmatter(text)
    out.extend(f"{where}: {e}" for e in errors)
    if fields is None:
        return
    name = fields.get("name")
    if name != dirname:
        out.append(f"{where}: name {name!r} does not match its directory {dirname!r}")
    description = fields.get("description")
    if not isinstance(description, str) or not description.strip():
        out.append(f"{where}: description is required")
    elif len(description) > MAX_DESCRIPTION:
        out.append(f"{where}: description is {len(description)} characters (limit {MAX_DESCRIPTION})")
    count = len(text.splitlines())
    if count > MAX_LINES:
        out.append(f"{where}: {count} lines, over {MAX_LINES} lines (move details to a sibling file)")


def check(root: Path) -> list[str]:
    """Return every problem found under root; an empty list means everything passes."""
    out: list[str] = []
    listed = check_manifest(root, out)
    if listed is None:
        return out

    seen: set[str] = set()
    for entry in listed:
        match = LISTED_RE.match(entry)
        if not match:
            out.append(f"plugin.json: {entry!r} is not a ./skills/<kebab-case-name> path")
            continue
        dirname = match.group(1)
        if dirname in seen:
            out.append(f"plugin.json: {entry!r} is listed twice")
            continue
        seen.add(dirname)
        if not (root / "skills" / dirname).is_dir():
            out.append(f"plugin.json: skills/{dirname} is listed but the directory does not exist")
            continue
        check_skill(root, dirname, out)

    skills_dir = root / "skills"
    if skills_dir.is_dir():
        for child in sorted(skills_dir.iterdir()):
            if child.is_dir() and child.name not in seen:
                out.append(f"skills/{child.name}: not listed in plugin.json (add it, or move it out of skills/)")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    found = check(args.root)
    if found:
        print("\n".join(found), file=sys.stderr)
        print(f"\n{len(found)} problem(s) in the plugin manifests or SKILL.md files.", file=sys.stderr)
        return 1
    print("Plugin manifests and every SKILL.md: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
