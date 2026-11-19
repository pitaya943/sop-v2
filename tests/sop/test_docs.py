"""Checks on the shipped collaboration docs (S1).

The rule "every concrete value comes from a config field" is enforced
indirectly: docs name config fields by path (e.g. `bot.github`), so we check
that every such path exists in the schema, that no templating placeholders
slipped in (design doc 14.3: no templating), and that links resolve.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

import config
import guards
from conftest import REPO_ROOT

SOP = REPO_ROOT / ".sop"
SCHEMA = json.loads((SOP / "schema.json").read_text())


def shipped_docs() -> list[Path]:
    """AGENTS.md plus every Markdown file under a template-managed path."""
    files = {REPO_ROOT / "AGENTS.md"}
    # Project-owned skeletons shipped with the template (S1c).
    for rel in ("docs/board.md", "docs/decisions.md", "docs/pitfalls.md", "docs/milestones/README.md"):
        files.add(REPO_ROOT / rel)
    for rel in guards.read_path_list(SOP / "managed.txt"):
        target = REPO_ROOT / rel
        if rel.endswith("/") and target.is_dir():
            files.update(target.rglob("*.md"))
        elif target.is_file() and target.suffix == ".md":
            files.add(target)
    return sorted(files)


DOCS = shipped_docs()
DOC_IDS = [str(p.relative_to(REPO_ROOT)) for p in DOCS]
# Docs whose links and examples we also check (the design doc is template-only).
ALL_MD = DOCS + [REPO_ROOT / "docs" / "design" / "sop-v2-design.md"]


def test_shipped_docs_exist():
    names = set(DOC_IDS)
    for expected in ["AGENTS.md", "CLAUDE.md", "docs/sop/workflow.md", "docs/sop/parallel.md",
                     "docs/sop/dispatch.md", "docs/sop/ci-contract.md", "docs/sop/bootstrap.md",
                     "docs/sop/sync.md"]:
        assert expected in names


# ---------------------------------------------------------------------------
# Config field references
# ---------------------------------------------------------------------------

FIELD_REF_RE = re.compile(r"`([a-z_]+(?:\.[a-z_*]+)*)`")


def resolves(path: str) -> bool:
    node = SCHEMA
    for part in path.split("."):
        if part == "*" and node.get("type") == "object":
            return True  # e.g. modules.*
        props = node.get("properties", {})
        if part not in props:
            return False
        node = props[part]
    return True


def field_refs(text: str) -> list[str]:
    """Backticked dotted names whose first segment is a top-level config field."""
    top = set(SCHEMA["properties"])
    return [m for m in FIELD_REF_RE.findall(text) if m.split(".")[0] in top]


@pytest.mark.parametrize("doc", DOCS, ids=DOC_IDS)
def test_config_field_references_exist(doc):
    unknown = [ref for ref in field_refs(doc.read_text()) if not resolves(ref)]
    assert unknown == [], f"{doc.name} names config fields that are not in the schema"


def test_field_reference_check_catches_typos():
    assert field_refs("use `bot.githb` and `bot.github`") == ["bot.githb", "bot.github"]
    assert not resolves("bot.githb") and resolves("bot.github") and resolves("modules.*")


@pytest.mark.parametrize("doc", DOCS, ids=DOC_IDS)
def test_no_templating_placeholders(doc):
    text = doc.read_text()
    for token in ("{{", "}}", "{%", "%}"):
        assert token not in text, f"{doc.name} contains {token!r}; values come from .sop/config.yml at runtime"


# ---------------------------------------------------------------------------
# AGENTS.md project-section markers (D20)
# ---------------------------------------------------------------------------

BEGIN, END = "<!-- sop:project:begin -->", "<!-- sop:project:end -->"


def test_agents_md_has_one_project_section():
    text = (REPO_ROOT / "AGENTS.md").read_text()
    assert text.count(BEGIN) == 1 and text.count(END) == 1
    assert text.index(BEGIN) < text.index(END)


def test_claude_md_imports_agents_md():
    assert (REPO_ROOT / "CLAUDE.md").read_text().splitlines()[0] == "@" + "AGENTS.md"  # built at runtime for the PII scan


# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------

LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.*?)\s*$", re.MULTILINE)


def github_slug(heading: str) -> str:
    """Approximate GitHub's heading anchors: lowercase, drop punctuation, spaces to '-'."""
    return re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")


def planned(rel: str) -> bool:
    """True if a missing link target is a template path due in a later stage.

    Exempt only an exact managed entry, or a path under a managed directory
    that does not exist yet. A missing file inside an existing managed
    directory (e.g. docs/sop/typo.md) is a broken link, not a plan.
    """
    for entry in guards.read_path_list(SOP / "managed.txt"):
        if rel == entry.rstrip("/"):
            return True
        if entry.endswith("/") and rel.startswith(entry) and not (REPO_ROOT / entry).exists():
            return True
    return False


@pytest.mark.parametrize("doc", ALL_MD, ids=[str(p.relative_to(REPO_ROOT)) for p in ALL_MD])
def test_relative_links_resolve(doc):
    problems = []
    for target in LINK_RE.findall(doc.read_text()):
        if re.match(r"[a-z]+:", target):
            continue  # external URL
        path_part, _, anchor = target.partition("#")
        dest = (doc.parent / path_part).resolve() if path_part else doc
        rel = dest.relative_to(REPO_ROOT).as_posix() if dest.is_relative_to(REPO_ROOT) else str(dest)
        if not dest.exists():
            if not planned(rel):
                problems.append(f"{target}: {rel} does not exist")
            continue
        if anchor and dest.suffix == ".md":
            slugs = {github_slug(h) for h in HEADING_RE.findall(dest.read_text())}
            if anchor not in slugs:
                problems.append(f"{target}: no heading with anchor #{anchor}")
    assert problems == []


def test_planned_does_not_hide_typos_in_existing_dirs():
    """docs/sop/ already exists, so a missing file inside it is a typo, not a plan."""
    assert not planned("docs/sop/typo.md")
    assert planned("docs/tickets/_template.md")  # exact managed entry


def test_slug_matches_github_style():
    assert github_slug("5. 升級 / Escalation") == "5-升級--escalation"
    assert github_slug("4. 停用檢查 / Disabling a guard") == "4-停用檢查--disabling-a-guard"


# ---------------------------------------------------------------------------
# Ticket examples use the restricted YAML subset (D17)
# ---------------------------------------------------------------------------

FRONT_MATTER_RE = re.compile(r"```yaml\n---\n(.*?)\n---\n```", re.DOTALL)


@pytest.mark.parametrize(
    "doc", [REPO_ROOT / "docs" / "sop" / "workflow.md", REPO_ROOT / "docs" / "design" / "sop-v2-design.md"],
    ids=["workflow.md", "design doc"],
)
def test_ticket_example_parses(doc):
    blocks = FRONT_MATTER_RE.findall(doc.read_text())
    assert blocks, "no ticket front-matter example found"
    for block in blocks:
        data = config.parse_yaml(block)
        assert data["id"] == "T-012"
        assert data["depends_on"] == ["T-010"]
        assert isinstance(data["allowed_paths"], list)
