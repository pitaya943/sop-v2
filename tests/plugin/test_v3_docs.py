"""Link checks for the v3 docs: README, skills/, the v3 design doc and (later) docs/guardrails, docs/concepts.

Relative links must resolve and Markdown anchors must match a heading, using
GitHub's slug rules (lowercase, punctuation dropped, spaces to '-').
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.*?)\s*$", re.MULTILINE)
FENCE_RE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)


def v3_docs() -> list[Path]:
    docs = {REPO_ROOT / "README.md", REPO_ROOT / "docs" / "suggestion.md",
            REPO_ROOT / "docs" / "design" / "v3-lightweight-design.md"}
    for rel in ("skills", "docs/guardrails", "docs/concepts"):
        docs.update((REPO_ROOT / rel).rglob("*.md"))
    return sorted(docs)


DOCS = v3_docs()


def github_slug(heading: str) -> str:
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def broken_links(doc: Path) -> list[str]:
    text = FENCE_RE.sub("", doc.read_text(encoding="utf-8"))
    problems = []
    for target in LINK_RE.findall(text):
        if re.match(r"[a-z]+:", target):
            continue  # external URL
        path_part, _, anchor = target.partition("#")
        dest = (doc.parent / path_part).resolve() if path_part else doc
        if not dest.exists():
            problems.append(f"{target}: target does not exist")
            continue
        if anchor and dest.suffix == ".md":
            slugs = {github_slug(h) for h in HEADING_RE.findall(dest.read_text(encoding="utf-8"))}
            if anchor not in slugs:
                problems.append(f"{target}: no heading with anchor #{anchor}")
    return problems


@pytest.mark.parametrize("doc", DOCS, ids=[str(p.relative_to(REPO_ROOT)) for p in DOCS])
def test_relative_links_resolve(doc):
    assert broken_links(doc) == []


def test_link_check_catches_bad_targets(tmp_path):
    (tmp_path / "other.md").write_text("# Real heading\n")
    doc = tmp_path / "doc.md"
    doc.write_text("[a](missing.md) [b](other.md#wrong) [c](other.md#real-heading) [d](https://example.com)\n")
    assert broken_links(doc) == ["missing.md: target does not exist", "other.md#wrong: no heading with anchor #wrong"]
