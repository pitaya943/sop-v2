"""The shipped skill set matches the v3 design (sections 5 and 14).

* Each expected skill exists, is listed in plugin.json, and has the right kind:
  user-invoked skills set ``disable-model-invocation: true``; model-invoked
  skills don't (design principle R3).
* Skill files are English (decision O1): no CJK characters in skills/**.
* Every skill reads the project config first and copes without it (R4).
* User-invoked skills never tell the agent to run another user-invoked skill.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import check_skills  # noqa: E402

# Grows step by step (design section 13): V2 adds the core five.
USER_INVOKED = {"setup", "build", "verify"}
MODEL_INVOKED = {"tdd", "evidence"}
EXPECTED = USER_INVOKED | MODEL_INVOKED
CONFIG = "docs/agents/harness.md"
CJK_RE = re.compile(r"[　-鿿＀-￯]")


def frontmatter(name: str) -> dict:
    fields, errors = check_skills.parse_frontmatter((REPO_ROOT / "skills" / name / "SKILL.md").read_text())
    assert errors == []
    return fields


def test_expected_skills_are_listed():
    plugin = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
    listed = {p.removeprefix("./skills/") for p in plugin["skills"]}
    assert EXPECTED <= listed


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_skill_kind(name):
    disabled = frontmatter(name).get("disable-model-invocation", False)
    assert disabled is (name in USER_INVOKED)


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_reads_project_config_first(name):
    text = (REPO_ROOT / "skills" / name / "SKILL.md").read_text()
    assert CONFIG in text
    assert "/setup" in text or name == "setup"  # points at setup when the config is missing


@pytest.mark.parametrize("name", sorted(USER_INVOKED))
def test_user_invoked_skills_do_not_invoke_each_other(name):
    text = (REPO_ROOT / "skills" / name / "SKILL.md").read_text()
    for other in USER_INVOKED - {name, "setup"}:  # suggesting /setup for missing config is allowed
        assert not re.search(rf"(?:run|invoke|call|use)\s+`?/{other}\b", text, re.I), other


def test_skill_files_are_english():
    offenders = []
    for path in (REPO_ROOT / "skills").rglob("*.md"):
        for number, line in enumerate(path.read_text().splitlines(), start=1):
            # Link targets may carry the design doc's bilingual heading anchors.
            if CJK_RE.search(re.sub(r"\]\([^)]*\)", "]()", line)):
                offenders.append(f"{path.relative_to(REPO_ROOT)}:{number}")
    assert offenders == []


def test_cjk_detector_works():
    assert CJK_RE.search("中文") and CJK_RE.search("（") and not CJK_RE.search("plain English — ok")
