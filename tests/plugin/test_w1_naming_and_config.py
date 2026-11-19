"""W1: the plugin is named "pitaya" (T25) and the harness template carries the config fields of design section 6.

The harness file is read by agents, not parsed, so these tests pin the labels
skills rely on and the defaults the design promises, rather than a schema.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / ".claude-plugin" / "plugin.json"
MARKET = REPO_ROOT / ".claude-plugin" / "marketplace.json"
TEMPLATE = REPO_ROOT / "skills" / "setup" / "harness-template.md"

PLUGIN_NAME = "pitaya"

# Label -> a phrase the default value must contain (design section 6).
FIELDS = {
    "Level": "1",
    "Owner": "example-owner",
    "Machine account": "example-bot",
    "Autonomy": "Only the Owner merges",
    "Tickets": "labelled `ticket`",
    "Test command": "`",
    "Document language": "",
    "Verification": "fresh subagent",
    "Fix rounds": "2",
    "Decisions": "docs/decisions.md",
    "Learning": "off",
}


def test_plugin_is_named_pitaya():
    assert json.loads(PLUGIN.read_text())["name"] == PLUGIN_NAME


def test_marketplace_lists_pitaya():
    market = json.loads(MARKET.read_text())
    assert [p["name"] for p in market["plugins"]] == [PLUGIN_NAME]


def test_readme_install_line_uses_plugin_name():
    readme = (REPO_ROOT / "README.md").read_text()
    assert re.search(rf"/plugin install {PLUGIN_NAME}@", readme)
    assert "/plugin install sop-v2@" not in readme


def test_skills_refer_to_the_plugin_not_the_old_name():
    offenders = [str(p.relative_to(REPO_ROOT)) for p in (REPO_ROOT / "skills").rglob("*.md")
                 if "sop-v2 skill" in p.read_text()]
    assert offenders == []


@pytest.mark.parametrize("label, default", FIELDS.items())
def test_harness_template_field(label, default):
    lines = [line for line in TEMPLATE.read_text().splitlines() if line.startswith(f"- {label}:")]
    assert len(lines) == 1, f"expected one '- {label}:' line"
    assert default in lines[0]


def test_pitfalls_are_off_by_default():
    # T12: decisions on, pitfalls off; the template mentions pitfalls only as an option.
    text = TEMPLATE.read_text()
    assert "- Pitfalls:" not in text
