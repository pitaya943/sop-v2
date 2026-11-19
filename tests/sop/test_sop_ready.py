"""sop-ready: the repo-level layer (L2) of the bootstrap gate (design doc 15)."""

from __future__ import annotations

import subprocess
import sys

import pytest

import config
import guards
from conftest import FIXTURES, REPO_ROOT

GUARDS = REPO_ROOT / "scripts" / "sop" / "guards.py"
TEMPLATE_ONLY = guards.read_path_list(REPO_ROOT / ".sop" / "template-only.txt")
MARKERS = dict(guards.read_template_only(REPO_ROOT / ".sop" / "template-only.txt"))


def run_cli(root):
    return subprocess.run(
        [sys.executable, str(GUARDS), "sop-ready", "--root", str(root)],
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# The unfilled template fails; a completed sample passes
# ---------------------------------------------------------------------------


def test_unfilled_template_fails_with_a_message_per_field():
    result = guards.sop_ready(REPO_ROOT)
    assert not result.ok
    schema = config.load_schema(REPO_ROOT / ".sop" / "schema.json")
    for v in config.validate(config.load_yaml_file(REPO_ROOT / ".sop" / "config.yml"), schema):
        assert f".sop/config.yml: {v.path}: is not filled in (null)" in "\n".join(result.problems)
    assert any("ready is not true" in p for p in result.problems)
    for rel in TEMPLATE_ONLY:
        assert f"template-only path still present: {rel}" in "\n".join(result.problems)


def test_unfilled_template_cli_exits_nonzero():
    proc = run_cli(REPO_ROOT)
    assert proc.returncode == 1
    assert "project.name: is not filled in" in proc.stdout
    assert "sop-ready: FAIL" in proc.stdout


def test_completed_sample_passes(make_project):
    root = make_project()
    result = guards.sop_ready(root)
    assert result.problems == []
    proc = run_cli(root)
    assert proc.returncode == 0, proc.stdout
    assert "Disabled guards (C4): none" in proc.stdout
    assert "sop-ready: PASS" in proc.stdout


def test_single_null_field_fails(make_project, filled):
    filled["modules"]["docs_lint"] = None
    result = guards.sop_ready(make_project(filled))
    assert result.problems == [
        ".sop/config.yml: modules.docs_lint: is not filled in (null); every field needs an explicit value"
    ]


def test_config_syntax_error_fails_with_line(make_project):
    root = make_project()
    (root / ".sop" / "config.yml").write_text("project:\n  name: yes\n")
    result = guards.sop_ready(root)
    assert any("line 2" in p and "ambiguous" in p for p in result.problems)


def test_missing_config_fails(make_project):
    root = make_project()
    (root / ".sop" / "config.yml").unlink()
    assert ".sop/config.yml is missing" in guards.sop_ready(root).problems


# ---------------------------------------------------------------------------
# Template-only leftovers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rel", TEMPLATE_ONLY)
def test_leftover_template_only_path_fails(make_project, rel):
    root = make_project()
    target = root / rel.rstrip("/")
    if rel.endswith("/"):
        target.mkdir(parents=True)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((REPO_ROOT / rel).read_text())  # the template's own version
    result = guards.sop_ready(root)
    assert len(result.problems) == 1
    assert result.problems[0].startswith(f"template-only path still present: {rel} ")


@pytest.mark.parametrize("rel, text", [
    ("README.md", "# Example Project\n\nA project README written at bootstrap.\n"),
    ("LICENSE", "Apache License\nVersion 2.0, January 2004\n"),
])
def test_project_may_replace_marker_entries(make_project, rel, text):
    """README.md and LICENSE may exist as the project's own versions (S3 fix)."""
    root = make_project()
    (root / rel).write_text(text)
    assert guards.sop_ready(root).problems == []


def test_marker_entries_carry_template_specific_text():
    for rel, marker in MARKERS.items():
        if marker:
            assert marker in (REPO_ROOT / rel).read_text(), rel


def test_template_only_list_matches_design():
    """Design doc 14.4 lists exactly these paths."""
    assert TEMPLATE_ONLY == [
        "docs/design/",
        "tests/sop/",
        ".github/workflows/self-ci.yml",
        "README.md",
        "LICENSE",
    ]


# ---------------------------------------------------------------------------
# Disabled guards (C4) need a recorded decision
# ---------------------------------------------------------------------------


def _disable(filled, decision="D-007", guard="evidence"):
    filled["overrides"]["disabled_guards"] = [
        {"guard": guard, "reason": "This project has no user interface.", "decision": decision}
    ]
    return filled


def test_disabled_guard_without_decision_record_fails(make_project, filled):
    root = make_project(_disable(filled))
    result = guards.sop_ready(root)
    assert result.problems == [
        "guard 'evidence' is disabled with decision D-007, which is not recorded in docs/decisions.md"
    ]


def test_disabled_guard_without_decision_log_fails(make_project, filled):
    root = make_project(_disable(filled))
    (root / "docs" / "decisions.md").unlink()
    assert any("docs/decisions.md does not exist" in p for p in guards.sop_ready(root).problems)


def test_disabled_guard_with_decision_record_passes_and_is_listed(make_project, filled):
    root = make_project(_disable(filled))
    with (root / "docs" / "decisions.md").open("a") as f:
        f.write("| D-007 | Turn off the evidence guard: the project has no UI. |\n")
    proc = run_cli(root)
    assert proc.returncode == 0, proc.stdout
    assert "  - evidence: This project has no user interface. (decision D-007)" in proc.stdout


def test_disabled_guards_are_listed_even_when_failing(make_project, filled):
    proc = run_cli(make_project(_disable(filled)))
    assert proc.returncode == 1
    assert "(decision D-007)" in proc.stdout


@pytest.mark.parametrize(
    "decisions_text",
    ["| D-0071 | other |", "| XD-007 | other |", "| D-07 | other |", "| D-00 | other |"],
)
def test_decision_reference_must_match_a_whole_id(make_project, filled, decisions_text):
    root = make_project(_disable(filled))
    (root / "docs" / "decisions.md").write_text(decisions_text + "\n")
    assert not guards.sop_ready(root).ok


def test_sop_ready_itself_cannot_be_disabled(make_project, filled):
    root = make_project(_disable(filled, guard="sop-ready"))
    (root / "docs" / "decisions.md").write_text("| D-007 | disable the gate |\n")
    result = guards.sop_ready(root)
    assert any("overrides.disabled_guards[0].guard" in p for p in result.problems)


# ---------------------------------------------------------------------------
# Bootstrap state
# ---------------------------------------------------------------------------

COMPLETED_BOOT = (FIXTURES / "completed-bootstrap.yml").read_text()


def test_ready_false_fails(make_project):
    root = make_project(bootstrap_text=COMPLETED_BOOT.replace("ready: true", "ready: false"))
    assert any("ready is not true" in p for p in guards.sop_ready(root).problems)


def test_template_bootstrap_state_is_unapproved():
    boot = config.load_yaml_file(REPO_ROOT / ".sop" / "bootstrap.yml")
    assert config.validate(boot, guards.BOOTSTRAP_SCHEMA) == []
    assert boot["ready"] is False
    assert {c["status"] for c in boot["checks"].values()} == {"pending"}


@pytest.mark.parametrize("status", ["pending", "failed"])
def test_ready_true_with_unfinished_check_fails(make_project, status):
    text = COMPLETED_BOOT.replace(
        'status: passed\n    evidence: "fictional: main ruleset restricts updates"',
        f'status: {status}\n    evidence: ""',
    )
    assert text != COMPLETED_BOOT
    result = guards.sop_ready(make_project(bootstrap_text=text))
    assert result.problems == [f".sop/bootstrap.yml: check B3 is {status}"]


def test_passed_check_without_evidence_fails(make_project):
    text = COMPLETED_BOOT.replace('"fictional: main ruleset restricts updates"', '"  "')
    result = guards.sop_ready(make_project(bootstrap_text=text))
    assert result.problems == [".sop/bootstrap.yml: check B3 is passed but has no evidence"]


@pytest.mark.parametrize(
    "mutate, fragment",
    [
        (lambda t: t.replace("  B7:\n", "  B8:\n"), "checks.B7: is missing"),
        (lambda t: t.replace("status: not_applicable", "status: skipped"), "checks.B6.status"),
        (lambda t: t.replace("ready: true", "ready: 'true'"), "ready: must be boolean"),
        (lambda t: t + "extra: 1\n", "extra: is not a known field"),
    ],
)
def test_malformed_bootstrap_state_fails(make_project, mutate, fragment):
    result = guards.sop_ready(make_project(bootstrap_text=mutate(COMPLETED_BOOT)))
    assert any(fragment in p for p in result.problems), result.problems
