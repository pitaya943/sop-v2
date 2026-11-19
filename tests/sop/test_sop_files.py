"""The other S0 files: the test-interface stub, managed.txt and version."""

from __future__ import annotations

import os
import re
import subprocess

import config
import guards
from conftest import REPO_ROOT

SOP = REPO_ROOT / ".sop"


def test_test_stub_fails_with_instructions():
    stub = REPO_ROOT / "scripts" / "sop" / "test"
    assert os.access(stub, os.X_OK), "scripts/sop/test must be executable"
    proc = subprocess.run([str(stub)], capture_output=True, text=True)
    assert proc.returncode != 0
    assert "please implement the test interface" in proc.stderr


def test_version_is_a_semver_prerelease():
    version = (SOP / "version").read_text()
    assert re.fullmatch(r"\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?\n", version)


def _managed():
    entries = []
    for line in (SOP / "managed.txt").read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            parts = line.split()
            entries.append((parts[0], parts[1:]))
    return entries


def test_managed_module_tags_name_real_modules():
    schema = config.load_schema(SOP / "schema.json")
    modules = set(schema["properties"]["modules"]["properties"])
    tagged = set()
    for path, tags in _managed():
        assert len(tags) <= 1, path
        for tag in tags:
            assert tag.startswith("module:"), f"{path}: unknown tag {tag}"
            assert tag.removeprefix("module:") in modules, f"{path}: unknown module {tag}"
            tagged.add(tag.removeprefix("module:"))
    assert tagged == modules, "every optional module owns at least one path"


def test_managed_paths_exclude_project_owned_and_template_only():
    """sop-sync overwrites managed paths, so they must never cover project data."""
    project_owned = [
        ".sop/config.yml", ".sop/bootstrap.yml", "AGENTS.md",
        "docs/board.md", "docs/decisions.md", "docs/pitfalls.md",
        "docs/tickets/T-001.md", "docs/milestones/M1.md", "docs/milestones/README.md", "docs/evidence/",
        "docs/project/", ".claude/skills/project/", ".github/workflows/project-checks.yml",
        "scripts/project/",
        "scripts/sop/test",  # the project's own test runner (design doc 10.2)
    ]
    template_only = guards.read_path_list(SOP / "template-only.txt")
    for path, _ in _managed():
        for owned in project_owned + template_only:
            covers = path == owned or (path.endswith("/") and owned.startswith(path))
            assert not covers, f"managed path {path} covers {owned}"


def test_template_config_lists_every_schema_field():
    """The template has every field present, in schema order, all null."""
    schema = config.load_schema(SOP / "schema.json")
    data = config.load_yaml_file(SOP / "config.yml")

    def keys(node):
        return list(node)

    assert keys(data) == list(schema["properties"])
    for name, sub in schema["properties"].items():
        if sub["type"] == "object":
            assert keys(data[name]) == list(sub["properties"]), name


def test_git_identity_sets_the_machine_account_as_author(tmp_path):
    """--git-identity sets user.name / user.email from bot.* (noreply address)."""
    import sys

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    fixture = REPO_ROOT / "tests" / "sop" / "fixtures" / "completed-config.yml"
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "sop" / "config.py"),
         "--config", str(fixture), "--git-identity"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    get = lambda key: subprocess.run(
        ["git", "config", "--local", key], cwd=tmp_path, capture_output=True, text=True
    ).stdout.strip()
    assert get("user.name") == "example-bot"
    assert get("user.email") == "1000001+example-bot" + "@" + config.NOREPLY_DOMAIN


def test_git_identity_refuses_an_invalid_config(tmp_path):
    import sys

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "sop" / "config.py"),
         "--config", str(SOP / "config.yml"), "--git-identity"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert proc.returncode == 1
    no_name = subprocess.run(["git", "config", "--local", "user.name"], cwd=tmp_path,
                             capture_output=True, text=True)
    assert no_name.stdout == ""
