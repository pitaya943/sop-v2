"""The shipped skills (S1b): format, the L3 gate check, and identity setup."""

from __future__ import annotations

import re

import pytest

import config
from conftest import REPO_ROOT

SKILLS_DIR = REPO_ROOT / ".claude" / "skills"
SKILLS = sorted(p.parent for p in SKILLS_DIR.glob("*/SKILL.md"))
IDS = [p.name for p in SKILLS]
CORE = ["plan-milestone", "build-ticket", "verify-ticket", "ask-owner", "milestone-report"]
FRONT_MATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def front_matter(skill):
    match = FRONT_MATTER_RE.match((skill / "SKILL.md").read_text())
    assert match, f"{skill.name}: SKILL.md must start with front matter"
    return config.parse_yaml(match.group(1))


def test_core_and_module_skills_exist():
    assert set(CORE) | {"learning"} <= set(IDS)


@pytest.mark.parametrize("skill", SKILLS, ids=IDS)
def test_front_matter(skill):
    meta = front_matter(skill)
    assert set(meta) == {"name", "description"}
    assert meta["name"] == skill.name
    assert isinstance(meta["description"], str) and len(meta["description"]) > 20


@pytest.mark.parametrize("skill", SKILLS, ids=IDS)
def test_every_skill_checks_the_bootstrap_gate(skill):
    """L3 of the bootstrap gate (design doc 15): every skill reads bootstrap.yml."""
    assert "`.sop/bootstrap.yml`" in (skill / "SKILL.md").read_text()


@pytest.mark.parametrize("skill", [s for s in SKILLS if s.name != "ask-owner"],
                         ids=[i for i in IDS if i != "ask-owner"])
def test_committing_skills_set_the_git_identity(skill):
    """Every skill that commits sets the machine account as author first."""
    assert "--git-identity" in (skill / "SKILL.md").read_text()


def test_agents_md_lists_every_core_skill():
    text = (REPO_ROOT / "AGENTS.md").read_text()
    for name in CORE:
        assert f"| `{name}` |" in text
