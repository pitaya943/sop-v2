"""scripts/sop/bootstrap: the shared bootstrap steps (S3). No network: the
GitHub API is a fake injected through ``urlopen``."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import io
import json
import shutil
import subprocess
import urllib.error

import pytest

import config
import guards
from conftest import FIXTURES, REPO_ROOT

_LOADER = importlib.machinery.SourceFileLoader("sop_bootstrap", str(REPO_ROOT / "scripts" / "sop" / "bootstrap"))
_SPEC = importlib.util.spec_from_loader("sop_bootstrap", _LOADER)
bootstrap = importlib.util.module_from_spec(_SPEC)
_LOADER.exec_module(bootstrap)

SCHEMA = config.load_schema(REPO_ROOT / ".sop" / "schema.json")
ANSWERS = {path: bootstrap.get_path(config.load_yaml_file(FIXTURES / "completed-config.yml"), path)
           for path, _ in bootstrap.fields(SCHEMA)}


@pytest.fixture
def project(tmp_path):
    """A fresh copy of the template's tracked files, as "Use this template" gives."""
    root = tmp_path / "project"
    files = subprocess.run(["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, text=True).stdout.split()
    for rel in files:
        if (REPO_ROOT / rel).is_file():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO_ROOT / rel, root / rel)
    return root


# ---------------------------------------------------------------------------
# Answers
# ---------------------------------------------------------------------------


def test_fields_cover_every_config_leaf():
    assert [p for p, _ in bootstrap.fields(SCHEMA)] == list(ANSWERS)


@pytest.mark.parametrize("text, field, value", [
    ("Example", {"type": "string"}, "Example"),
    ("3", {"type": "integer"}, 3),
    ("false", {"type": "boolean"}, False),
    ("a, b ,c", {"type": "array", "items": {"type": "string"}}, ["a", "b", "c"]),
    ("[]", {"type": "array", "items": {"type": "string"}}, []),
    ("none", {"type": "array", "items": {"type": "object"}}, []),
])
def test_parse_answer(text, field, value):
    assert bootstrap.parse_answer(text, field) == value


@pytest.mark.parametrize("text, field", [
    ("", {"type": "string"}),  # no defaults
    ("   ", {"type": "integer"}),
    ("two", {"type": "integer"}),
    ("yes", {"type": "boolean"}),  # true / false only
    ("x", {"type": "array", "items": {"type": "object"}}),
])
def test_parse_answer_rejects(text, field):
    with pytest.raises(ValueError):
        bootstrap.parse_answer(text, field)


def test_ask_reasks_until_valid_and_needs_confirmation(project):
    script = []
    for path, field in bootstrap.fields(SCHEMA):
        value = ANSWERS[path]
        if path == "max_parallel":
            script += ["", "9"]  # empty, then out of range: both re-asked
        if path == "bot.github":
            script += ["example-owner"]  # equals owner.github: re-asked
        if isinstance(value, bool):
            script.append("true" if value else "false")
        elif isinstance(value, list):
            script.append(", ".join(value) if value else "[]")
        else:
            script.append(str(value))
    said = []
    answers = iter(script + ["yes"])
    assert bootstrap.ask(project, read=lambda prompt: next(answers), say=said.append) == 0
    assert any("no default" in s for s in said)
    assert any("must be <= 5" in s for s in said)
    assert any("must differ from owner.github" in s for s in said)
    assert config.validate(config.load_yaml_file(project / ".sop" / "config.yml"), SCHEMA) == []


def test_ask_writes_nothing_without_yes(project):
    before = (project / ".sop" / "config.yml").read_text()
    script = iter([("true" if v else "false") if isinstance(v, bool)
                   else (", ".join(v) if v else "[]") if isinstance(v, list) else str(v)
                   for v in ANSWERS.values()] + ["no"])
    assert bootstrap.ask(project, read=lambda p: next(script), say=lambda s: None) == 1
    assert (project / ".sop" / "config.yml").read_text() == before


# ---------------------------------------------------------------------------
# Writing the config without losing comments
# ---------------------------------------------------------------------------


def test_write_config_keeps_comments_and_validates(project):
    assert bootstrap.write_config(project, ANSWERS) == []
    text = (project / ".sop" / "config.yml").read_text()
    assert "# GitHub login of the machine account" in text
    assert "null" not in text.split("Rules for every field")[1]
    assert config.validate(config.load_yaml_file(project / ".sop" / "config.yml"), SCHEMA) == []


def test_write_config_requires_every_field(project):
    partial = {k: v for k, v in ANSWERS.items() if k != "doc_language"}
    problems = bootstrap.write_config(project, partial)
    assert any("doc_language" in p for p in problems)
    assert "doc_language: null" in (project / ".sop" / "config.yml").read_text()


def test_set_values_handles_tricky_lists_and_blocks(project):
    text = (project / ".sop" / "config.yml").read_text()
    guards_list = [{"guard": "evidence", "reason": "No UI: CLI only.", "decision": "D-001"}]
    out = bootstrap.set_values(text, {"spec_paths": ["docs/spec/**", "a, b"], "overrides.disabled_guards": guards_list})
    data = config.parse_yaml(out)
    assert data["spec_paths"] == ["docs/spec/**", "a, b"]
    assert data["overrides"]["disabled_guards"] == guards_list
    again = bootstrap.set_values(out, {"overrides.disabled_guards": []})  # replaces the old block
    assert config.parse_yaml(again)["overrides"]["disabled_guards"] == []
    assert "disabled_guards: [] # list of" in again


# ---------------------------------------------------------------------------
# apply
# ---------------------------------------------------------------------------


def _configured(project, **modules):
    answers = dict(ANSWERS)
    for name, on in modules.items():
        answers[f"modules.{name}"] = on
    assert bootstrap.write_config(project, answers) == []
    return answers


def test_apply_refuses_an_incomplete_config(project):
    with pytest.raises(bootstrap.BootstrapError):
        bootstrap.apply(project)


def test_apply_removes_template_files_and_writes_project_files(project):
    _configured(project, learning=False)
    done = bootstrap.apply(project, notes="- **Commands:** `make test`")
    for rel in ("docs/design", "tests/sop", ".github/workflows/self-ci.yml", "LICENSE", ".claude/skills/learning"):
        assert not (project / rel).exists(), rel
    assert "Example Project" in (project / "README.md").read_text()
    agents = (project / "AGENTS.md").read_text()
    assert agents.count(bootstrap.BEGIN) == 1 and "Example Project" in agents and "`make test`" in agents
    assert any("module learning is off" in d for d in done)
    assert [p for p in guards.sop_ready(project).problems if p.startswith("template-only")] == []


def test_apply_keeps_enabled_modules(project):
    _configured(project, learning=True)
    bootstrap.apply(project)
    assert (project / ".claude" / "skills" / "learning" / "SKILL.md").exists()


# ---------------------------------------------------------------------------
# check, record, finalize
# ---------------------------------------------------------------------------


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fake_github(responses):
    """urlopen that serves {path suffix: json or HTTP status int}."""
    def urlopen(req, timeout):
        for suffix, body in responses.items():
            if req.full_url.endswith(suffix):
                if isinstance(body, int):
                    raise urllib.error.HTTPError(req.full_url, body, "error", {}, None)
                return _Resp(json.dumps(body).encode())
        raise urllib.error.HTTPError(req.full_url, 404, "not found", {}, None)
    return urlopen


GOOD_RULES = [{"type": t} for t in ("update", "deletion", "non_fast_forward", "pull_request")] + [
    {"type": "required_status_checks",
     "parameters": {"required_status_checks": [{"context": c} for c in guards.CHECKS]}}]
GOOD_API = {"/user": {"login": "example-bot"},
            "/collaborators/example-bot/permission": {"permission": "write", "role_name": "write"},
            "/rules/branches/main": GOOD_RULES}


def _passing_test_script(project):
    script = project / "scripts" / "sop" / "test"
    script.write_text("#!/bin/sh\nmkdir -p build/sop\n"
                      "echo '<testsuite><testcase classname=\"smoke\" name=\"test_ok\"/></testsuite>'"
                      " > build/sop/junit.xml\n")
    script.chmod(0o755)


def test_check_passes_everything_on_a_finished_project(project):
    _configured(project)
    bootstrap.apply(project)
    _passing_test_script(project)
    results = bootstrap.check(project, "example-owner/example-project", "token",
                              urlopen=fake_github(GOOD_API))
    assert {cid: s for cid, (s, _) in results.items()} == {
        "B1": "passed", "B2": "passed", "B3": "passed", "B4": "passed",
        "B5": "passed", "B6": "not_applicable", "B7": "passed"}


@pytest.mark.parametrize("override, cid, status", [
    ({"/user": {"login": "example-owner"}}, "B1", "failed"),
    ({"/collaborators/example-bot/permission": {"permission": "admin", "role_name": "admin"}}, "B2", "failed"),
    ({"/collaborators/example-bot/permission": {"permission": "write", "role_name": "maintain"}}, "B2", "failed"),
    ({"/rules/branches/main": [{"type": "pull_request"}]}, "B3", "failed"),
    ({"/rules/branches/main": GOOD_RULES[:4]}, "B4", "failed"),
    ({"/rules/branches/main": 403}, "B3", "pending"),  # unreadable: record a screenshot by hand
])
def test_check_reports_each_problem(project, override, cid, status):
    _configured(project)
    results = bootstrap.check(project, "example-owner/example-project", "token",
                              urlopen=fake_github({**GOOD_API, **override}), run_tests=False)
    assert results[cid][0] == status


def test_check_without_a_token_leaves_api_checks_pending(project):
    _configured(project)
    results = bootstrap.check(project, run_tests=False)
    assert all(results[c][0] == "pending" for c in ("B1", "B2", "B3", "B4"))


def test_check_needs_the_secret_when_claude_review_is_on(project):
    _configured(project, claude_review=True)
    api = {**GOOD_API, "/actions/secrets": {"secrets": [{"name": "OTHER"}]}}
    results = bootstrap.check(project, "example-owner/example-project", "token", urlopen=fake_github(api),
                              run_tests=False)
    assert results["B6"][0] == "failed"


def test_b5_fails_with_the_stub_and_b7_before_apply(project):
    _configured(project)
    results = bootstrap.check(project)
    assert results["B5"][0] == "failed"  # the shipped stub fails on purpose
    assert results["B7"][0] == "failed"  # template-only files still present


def test_record_needs_evidence_for_passed(project):
    with pytest.raises(bootstrap.BootstrapError):
        bootstrap.record(project, {"B3": ("passed", "  ")})
    bootstrap.record(project, {"B3": ("passed", "screenshot docs/evidence/bootstrap/main-ruleset.png")})
    boot = config.load_yaml_file(project / ".sop" / "bootstrap.yml")
    assert boot["checks"]["B3"]["status"] == "passed"
    assert "# main has a ruleset" in (project / ".sop" / "bootstrap.yml").read_text()  # comments kept


def test_finalize_refuses_while_checks_are_open(project):
    assert bootstrap.finalize(project) == [f"{cid} is pending" for cid in guards.CHECK_IDS]
    assert config.load_yaml_file(project / ".sop" / "bootstrap.yml")["ready"] is False


def test_end_to_end_bootstrap_opens_the_gate(project):
    """write -> apply -> implement the test interface -> check -> finalize -> sop-ready passes."""
    _configured(project)
    bootstrap.apply(project)
    _passing_test_script(project)
    bootstrap.record(project, bootstrap.check(project, "example-owner/example-project", "token",
                                              urlopen=fake_github(GOOD_API)))
    assert bootstrap.finalize(project) == []
    assert guards.sop_ready(project).ok
