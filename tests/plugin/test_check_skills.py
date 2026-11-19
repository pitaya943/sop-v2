"""Tests for scripts/check_skills.py, the plugin and SKILL.md checker (v3 design, step V1).

Each failure case builds a small fake repo in tmp_path and asserts the exact
problem is reported, so a checker that silently accepts everything fails here.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKER = REPO_ROOT / "scripts" / "check_skills.py"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
import check_skills  # noqa: E402

GOOD_SKILL = """---
name: {name}
description: Do one small thing well. Use when the user asks for it.
---

# {name}

Body.
"""


def make_repo(tmp_path: Path, skills: dict[str, str] | None = None, listed: list[str] | None = None,
              manifest: dict | None = None, marketplace: dict | None = None) -> Path:
    """Write a minimal plugin repo; every argument overrides one piece of a valid default."""
    skills = {"tdd": GOOD_SKILL.format(name="tdd")} if skills is None else skills
    listed = [f"./skills/{n}" for n in skills] if listed is None else listed
    for name, text in skills.items():
        (tmp_path / "skills" / name).mkdir(parents=True)
        if text is not None:
            (tmp_path / "skills" / name / "SKILL.md").write_text(text)
    (tmp_path / "skills").mkdir(exist_ok=True)
    (tmp_path / "skills" / "README.md").write_text("# Skills\n")
    plugin = {
        "name": "sop-v2",
        "version": "3.0.0-dev.0",
        "description": "Small, composable skills for agent development.",
        "author": {"name": "sop-v2 contributors"},
        "license": "MIT-0",
        "skills": listed,
    }
    plugin.update(manifest or {})
    market = {
        "name": "sop-v2",
        "owner": {"name": "sop-v2 contributors"},
        "plugins": [{"name": "sop-v2", "source": "./", "description": "Skills."}],
    }
    market.update(marketplace or {})
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / ".claude-plugin" / "plugin.json").write_text(json.dumps(plugin))
    (tmp_path / ".claude-plugin" / "marketplace.json").write_text(json.dumps(market))
    return tmp_path


def problems(root: Path) -> list[str]:
    return check_skills.check(root)


def assert_one(root: Path, fragment: str) -> None:
    found = problems(root)
    assert any(fragment in p for p in found), found


# --- the real repo and a valid fixture pass ----------------------------------

def test_this_repo_passes():
    assert problems(REPO_ROOT) == []


def test_valid_fixture_passes(tmp_path):
    assert problems(make_repo(tmp_path)) == []


def test_cli_exit_codes(tmp_path):
    ok = subprocess.run([sys.executable, str(CHECKER), "--root", str(make_repo(tmp_path / "a"))],
                        capture_output=True, text=True)
    assert ok.returncode == 0, ok.stderr
    bad_root = make_repo(tmp_path / "b", listed=["./skills/missing"])
    bad = subprocess.run([sys.executable, str(CHECKER), "--root", str(bad_root)], capture_output=True, text=True)
    assert bad.returncode == 1
    assert "missing" in bad.stderr


@pytest.fixture(autouse=True)
def _mk(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()


# --- manifest ----------------------------------------------------------------

@pytest.mark.parametrize("override, fragment", [
    ({"name": "Sop V2"}, "name"),
    ({"version": "3.0"}, "version"),
    ({"description": ""}, "description"),
    ({"skills": "./skills"}, "skills"),
])
def test_bad_manifest_fields(tmp_path, override, fragment):
    assert_one(make_repo(tmp_path, manifest=override), f"plugin.json: {fragment}")


def test_missing_manifest(tmp_path):
    root = make_repo(tmp_path)
    (root / ".claude-plugin" / "plugin.json").unlink()
    assert_one(root, "plugin.json: missing")


def test_invalid_json(tmp_path):
    root = make_repo(tmp_path)
    (root / ".claude-plugin" / "plugin.json").write_text("{not json")
    assert_one(root, "plugin.json: not valid JSON")


def test_marketplace_must_point_at_this_plugin(tmp_path):
    root = make_repo(tmp_path, marketplace={"plugins": [{"name": "other", "source": "./"}]})
    assert_one(root, "marketplace.json")


def test_marketplace_source_must_be_repo_root(tmp_path):
    root = make_repo(tmp_path, marketplace={"plugins": [{"name": "sop-v2", "source": "./sub"}]})
    assert_one(root, "marketplace.json")


# --- listing ------------------------------------------------------------------

def test_listed_skill_must_exist(tmp_path):
    assert_one(make_repo(tmp_path, listed=["./skills/tdd", "./skills/missing"]), "skills/missing")


def test_listed_path_must_be_under_skills(tmp_path):
    assert_one(make_repo(tmp_path, listed=["./skills/tdd", "./docs/tdd"]), "./docs/tdd")


def test_duplicate_listing(tmp_path):
    assert_one(make_repo(tmp_path, listed=["./skills/tdd", "./skills/tdd"]), "listed twice")


def test_unlisted_skill_directory(tmp_path):
    skills = {"tdd": GOOD_SKILL.format(name="tdd"), "build": GOOD_SKILL.format(name="build")}
    assert_one(make_repo(tmp_path, skills=skills, listed=["./skills/tdd"]), "skills/build: not listed")


def test_listed_directory_without_skill_md(tmp_path):
    assert_one(make_repo(tmp_path, skills={"tdd": None}), "skills/tdd/SKILL.md: missing")


# --- SKILL.md -----------------------------------------------------------------

def skill(text: str) -> dict[str, str]:
    return {"tdd": text}


def test_no_frontmatter(tmp_path):
    assert_one(make_repo(tmp_path, skills=skill("# tdd\n")), "no frontmatter")


def test_name_must_match_directory(tmp_path):
    assert_one(make_repo(tmp_path, skills=skill(GOOD_SKILL.format(name="other"))), "does not match")


def test_description_required(tmp_path):
    text = "---\nname: tdd\n---\n\nBody.\n"
    assert_one(make_repo(tmp_path, skills=skill(text)), "description")


def test_description_too_long(tmp_path):
    text = f"---\nname: tdd\ndescription: {'x' * 1025}\n---\n"
    assert_one(make_repo(tmp_path, skills=skill(text)), "1024")


def test_unquoted_colon_space_is_rejected(tmp_path):
    # Real YAML parsers fail on this line, so the skill would be skipped at install.
    text = "---\nname: tdd\ndescription: Use it: always\n---\n"
    assert_one(make_repo(tmp_path, skills=skill(text)), "quote")


def test_quoted_colon_is_fine(tmp_path):
    text = '---\nname: tdd\ndescription: "Use it: always"\n---\n'
    assert problems(make_repo(tmp_path, skills=skill(text))) == []


def test_unknown_key(tmp_path):
    text = "---\nname: tdd\ndescription: Fine.\ncolour: red\n---\n"
    assert_one(make_repo(tmp_path, skills=skill(text)), "unknown key 'colour'")


def test_duplicate_key(tmp_path):
    text = "---\nname: tdd\nname: tdd\ndescription: Fine.\n---\n"
    assert_one(make_repo(tmp_path, skills=skill(text)), "duplicate key")


@pytest.mark.parametrize("value, ok", [("true", True), ("false", True), ("yes", False), ('"true"', False)])
def test_disable_model_invocation_is_boolean(tmp_path, value, ok):
    text = f"---\nname: tdd\ndescription: Fine.\ndisable-model-invocation: {value}\n---\n"
    found = problems(make_repo(tmp_path, skills=skill(text)))
    assert (found == []) is ok, found


def test_skill_md_line_limit(tmp_path):
    body = "line\n" * check_skills.MAX_LINES
    text = "---\nname: tdd\ndescription: Fine.\n---\n" + body
    assert_one(make_repo(tmp_path, skills=skill(text)), f"over {check_skills.MAX_LINES} lines")


def test_line_limit_is_inclusive(tmp_path):
    head = "---\nname: tdd\ndescription: Fine.\n---\n"
    text = head + "line\n" * (check_skills.MAX_LINES - head.count("\n"))
    assert len(text.splitlines()) == check_skills.MAX_LINES
    assert problems(make_repo(tmp_path, skills=skill(text))) == []
