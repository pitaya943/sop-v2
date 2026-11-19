"""scripts/sop/sync (S3b): what a template update overwrites and what it never
touches. Offline: the "template" is a local git repo with tags."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import shutil
import subprocess

import pytest

import config
import guards
from conftest import FIXTURES, REPO_ROOT

GIT_ENV = dict(os.environ, GIT_AUTHOR_NAME="Example Bot", GIT_AUTHOR_EMAIL="bot@example.com",
               GIT_COMMITTER_NAME="Example Bot", GIT_COMMITTER_EMAIL="bot@example.com")


def _load(name):
    loader = importlib.machinery.SourceFileLoader(f"sop_{name}", str(REPO_ROOT / "scripts" / "sop" / name))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(f"sop_{name}", loader))
    loader.exec_module(module)
    return module


sync = _load("sync")
bootstrap = _load("bootstrap")


def git(path, *args):
    return subprocess.run(["git", *args], cwd=path, env=GIT_ENV, check=True, capture_output=True, text=True).stdout


def copy_template(dest):
    files = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                           cwd=REPO_ROOT, capture_output=True, text=True).stdout.split()
    for rel in files:
        if (REPO_ROOT / rel).is_file():
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO_ROOT / rel, dest / rel)


@pytest.fixture
def setup(tmp_path):
    """(template repo with v2.0.0 and v2.1.0, bootstrapped project at v2.0.0)."""
    tpl = tmp_path / "template"
    tpl.mkdir()
    copy_template(tpl)
    git(tpl, "init", "-q", "-b", "main")
    git(tpl, "add", "-A")
    git(tpl, "commit", "-q", "-m", "v2.0.0")
    git(tpl, "tag", "v2.0.0")

    proj = tmp_path / "project"
    shutil.copytree(tpl, proj, ignore=shutil.ignore_patterns(".git"))
    git(proj, "init", "-q", "-b", "main")
    answers = {p: bootstrap.get_path(config.load_yaml_file(FIXTURES / "completed-config.yml"), p)
               for p, _ in bootstrap.fields(config.load_schema(REPO_ROOT / ".sop" / "schema.json"))}
    answers["modules.learning"] = False
    assert bootstrap.write_config(proj, answers) == []
    bootstrap.apply(proj, notes="- **Commands:** `make test`")
    (proj / "scripts" / "sop" / "test").write_text("#!/bin/sh\necho project test runner\n")
    (proj / "docs" / "board.md").write_text((proj / "docs" / "board.md").read_text() + "| T-001 | M1 | A | merged | #1 | 0 | |\n")
    git(proj, "add", "-A")
    git(proj, "commit", "-q", "-m", "bootstrap")

    # v2.1.0: change a doc, add a doc, drop a managed file, add a config field, change AGENTS.md
    (tpl / "docs" / "sop" / "workflow.md").write_text((tpl / "docs" / "sop" / "workflow.md").read_text() + "\nv2.1 rule\n")
    (tpl / "docs" / "sop" / "new.md").write_text("# New\n")
    (tpl / "docs" / "tickets" / "_template.md").unlink()
    managed = (tpl / ".sop" / "managed.txt").read_text().replace("docs/tickets/_template.md\n", "")
    (tpl / ".sop" / "managed.txt").write_text(managed)
    schema = json.loads((tpl / ".sop" / "schema.json").read_text())
    schema["properties"]["review_hours"] = {"type": "integer", "minimum": 1}
    schema["required"].append("review_hours")
    (tpl / ".sop" / "schema.json").write_text(json.dumps(schema, indent=2))
    (tpl / ".sop" / "config.yml").write_text((tpl / ".sop" / "config.yml").read_text()
                                             + "review_hours: null      # hours the Owner aims to answer within\n")
    (tpl / "AGENTS.md").write_text((tpl / "AGENTS.md").read_text().replace("# AGENTS.md", "# AGENTS.md (v2.1)", 1))
    tool = tpl / "scripts" / "sop" / "newtool"
    tool.write_text("#!/bin/sh\necho new\n")
    tool.chmod(0o755)
    (tpl / ".sop" / "managed.txt").write_text((tpl / ".sop" / "managed.txt").read_text() + "scripts/sop/newtool\n")
    (tpl / ".sop" / "version").write_text("2.1.0\n")
    git(tpl, "add", "-A")
    git(tpl, "commit", "-q", "-m", "v2.1.0")
    git(tpl, "tag", "v2.1.0")
    return tpl, proj


def test_sync_updates_template_paths_and_keeps_project_files(setup):
    tpl, proj = setup
    test_runner = (proj / "scripts" / "sop" / "test").read_text()
    board = (proj / "docs" / "board.md").read_text()
    report = sync.sync(proj, str(tpl), "v2.1.0")

    assert "v2.1 rule" in (proj / "docs" / "sop" / "workflow.md").read_text()
    assert (proj / "docs" / "sop" / "new.md").exists()
    assert not (proj / "docs" / "tickets" / "_template.md").exists()
    assert (proj / ".sop" / "version").read_text() == "2.1.0\n"
    assert "docs/sop/new.md" in report["updated"]
    # project-owned files are never touched
    assert (proj / "scripts" / "sop" / "test").read_text() == test_runner
    assert (proj / "docs" / "board.md").read_text() == board
    # AGENTS.md: template part from v2.1.0, project section kept
    agents = (proj / "AGENTS.md").read_text()
    assert agents.startswith("# AGENTS.md (v2.1)") and "`make test`" in agents and "Example Project" in agents


def test_sync_keeps_config_values_and_asks_for_new_fields(setup):
    tpl, proj = setup
    report = sync.sync(proj, str(tpl), "v2.1.0")
    assert report["added_fields"] == ["review_hours"]
    cfg = config.load_yaml_file(proj / ".sop" / "config.yml")
    assert cfg["bot"]["github"] == "example-bot" and cfg["review_hours"] is None
    assert "# hours the Owner aims to answer within" in (proj / ".sop" / "config.yml").read_text()
    problems = guards.sop_ready(proj).problems
    assert any("review_hours: is not filled in" in p for p in problems)  # P2 holds during updates


def test_sync_respects_module_switches(setup):
    tpl, proj = setup
    sync.sync(proj, str(tpl), "v2.1.0")
    assert not (proj / ".claude" / "skills" / "learning").exists()  # learning is off
    text = bootstrap.set_values((proj / ".sop" / "config.yml").read_text(), {"modules.learning": True})
    (proj / ".sop" / "config.yml").write_text(text)
    sync.sync(proj, str(tpl), "v2.1.0")
    assert (proj / ".claude" / "skills" / "learning" / "SKILL.md").exists()  # turning it on adds it
    text = bootstrap.set_values((proj / ".sop" / "config.yml").read_text(), {"modules.learning": False})
    (proj / ".sop" / "config.yml").write_text(text)
    report = sync.sync(proj, str(tpl), "v2.1.0")
    assert not (proj / ".claude" / "skills" / "learning").exists()
    assert any("module learning is off" in r for r in report["removed"])


def test_sync_keeps_executable_bits(setup):
    tpl, proj = setup
    sync.sync(proj, str(tpl), "v2.1.0")
    assert os.access(proj / "scripts" / "sop" / "bootstrap", os.X_OK)
    assert os.access(proj / "scripts" / "sop" / "newtool", os.X_OK)  # a new script arrives executable


def test_rollback_is_a_sync_to_the_previous_tag(setup):
    tpl, proj = setup
    sync.sync(proj, str(tpl), "v2.1.0")
    sync.sync(proj, str(tpl), "v2.0.0")
    assert not (proj / "docs" / "sop" / "new.md").exists()
    assert (proj / "docs" / "tickets" / "_template.md").exists()
    assert "v2.1 rule" not in (proj / "docs" / "sop" / "workflow.md").read_text()
    assert "review_hours" not in config.load_yaml_file(proj / ".sop" / "config.yml")


def test_sync_pr_stays_within_its_allowed_paths(setup):
    """The sync result passes path-scope's sop/sync-* limit (D37)."""
    tpl, proj = setup
    git(proj, "checkout", "-q", "-b", "sop/sync-v2.1.0")
    sync.sync(proj, str(tpl), "v2.1.0")
    git(proj, "add", "-A")
    git(proj, "commit", "-q", "-m", "sync")
    ctx = guards.Ctx(root=proj, base="main", head="HEAD", base_ref="main", head_ref="sop/sync-v2.1.0")
    assert guards.check_path_scope(ctx) == []


def test_sync_fails_cleanly_for_an_unknown_tag(setup):
    tpl, proj = setup
    before = (proj / "AGENTS.md").read_text()
    with pytest.raises(sync.SyncError):
        sync.sync(proj, str(tpl), "v9.9.9")
    assert (proj / "AGENTS.md").read_text() == before
