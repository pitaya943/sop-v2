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
        for rel in read_path_list(sop / "template-only.txt"):
            if (root / rel.rstrip("/")).exists():
                problems.append(f"template-only path still present: {rel} (bootstrap removes it)")
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="sop-v2 stack-neutral guards.")
    sub = parser.add_subparsers(dest="guard", required=True)
    ready = sub.add_parser("sop-ready", help="bootstrap gate: config valid, approved, template files removed")
    ready.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)

    result = sop_ready(args.root)
    print(format_disabled(result.disabled_guards))
    if result.ok:
        print("sop-ready: PASS")
        return 0
    for problem in result.problems:
        print(f"  - {problem}")
    print(f"sop-ready: FAIL ({len(result.problems)} problem(s))")
    return 1


if __name__ == "__main__":
    sys.exit(main())
