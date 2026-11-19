#!/usr/bin/env python3
"""Docs check for the optional docs_lint module (modules.docs_lint). Stdlib only.

Checks every tracked Markdown file: each relative link points to a file that
exists, and each #anchor matches a heading in the target file (GitHub's
anchor rules: lowercase, punctuation dropped, spaces become "-").

    python3 scripts/sop/docs_lint.py [--root PATH]

Exit 1 with one line per broken link.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.*?)\s*$", re.MULTILINE)
FENCE_RE = re.compile(r"^(`{3,}|~{3,}).*?^\1", re.MULTILINE | re.DOTALL)


def github_slug(heading: str) -> str:
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def anchors(text: str) -> set[str]:
    return {github_slug(h) for h in HEADING_RE.findall(FENCE_RE.sub("", text))}


def check_file(root: Path, rel: str) -> list[str]:
    path = root / rel
    text = FENCE_RE.sub("", path.read_text(encoding="utf-8", errors="replace"))
    problems = []
    for target in LINK_RE.findall(text):
        if re.match(r"[a-z][a-z0-9+.-]*:", target):
            continue  # external (https:, mailto:, ...)
        file_part, _, anchor = target.partition("#")
        dest = (path.parent / file_part).resolve() if file_part else path
        if not dest.exists():
            problems.append(f"{rel}: link {target} -> missing {file_part}")
        elif anchor and dest.suffix == ".md" and anchor not in anchors(dest.read_text(encoding="utf-8", errors="replace")):
            problems.append(f"{rel}: link {target} -> no heading for #{anchor}")
    return problems


def markdown_files(root: Path) -> list[str]:
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.md"],
                         cwd=root, capture_output=True, text=True, check=True).stdout
    return sorted(p for p in out.splitlines() if p)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    files = markdown_files(args.root)
    problems = [p for rel in files for p in check_file(args.root, rel)]
    for p in problems:
        print(p)
    print(f"docs-lint: {'FAIL: ' + str(len(problems)) + ' broken link(s)' if problems else 'PASS'} ({len(files)} files)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
