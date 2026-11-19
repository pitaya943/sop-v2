"""Shared fixtures for the sop-v2 template's own tests (template-only)."""

from __future__ import annotations

import copy
import shutil
import socket
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).parent / "fixtures"

# The scripts under test are run as plain files in projects, not as a package,
# so import them the same way.
sys.path.insert(0, str(REPO_ROOT / "scripts" / "sop"))
sys.path.insert(0, str(Path(__file__).parent))

import config  # noqa: E402


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Fail any test that tries to open a network connection."""

    def refuse(*args, **kwargs):
        raise RuntimeError("tests must not use the network")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


@pytest.fixture(scope="session")
def schema() -> dict:
    return config.load_schema(REPO_ROOT / ".sop" / "schema.json")


@pytest.fixture(scope="session")
def _filled_cached() -> dict:
    return config.load_yaml_file(FIXTURES / "completed-config.yml")


@pytest.fixture
def filled(_filled_cached) -> dict:
    """A valid, completed config (fresh copy per test, safe to mutate)."""
    return copy.deepcopy(_filled_cached)


@pytest.fixture
def make_project(tmp_path):
    """Build a completed project in tmp_path; returns a function taking overrides.

    The project has the template's .sop/ files with the completed config and
    bootstrap state, no template-only paths, and an empty decision log.
    """

    def build(config_data: dict | None = None, bootstrap_text: str | None = None) -> Path:
        root = tmp_path / "project"
        shutil.copytree(REPO_ROOT / ".sop", root / ".sop")
        if config_data is None:
            shutil.copy(FIXTURES / "completed-config.yml", root / ".sop" / "config.yml")
        else:
            (root / ".sop" / "config.yml").write_text(config.dump_yaml(config_data))
        (root / ".sop" / "bootstrap.yml").write_text(
            bootstrap_text
            if bootstrap_text is not None
            else (FIXTURES / "completed-bootstrap.yml").read_text()
        )
        (root / "docs").mkdir()
        (root / "docs" / "decisions.md").write_text("# Decisions\n\n| ID | Decision |\n| --- | --- |\n")
        return root

    return build
