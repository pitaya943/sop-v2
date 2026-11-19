"""Optional modules (S3c): their files, their workflows, and B7 for every
combination of module switches (design doc 19)."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import itertools
import shutil
import subprocess

import pytest

import config
from conftest import FIXTURES, REPO_ROOT

WORKFLOWS = REPO_ROOT / ".github" / "workflows"


def _load(name):
    loader = importlib.machinery.SourceFileLoader(f"sop_{name}", str(REPO_ROOT / "scripts" / "sop" / name))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(f"sop_{name}", loader))
    loader.exec_module(module)
    return module


bootstrap = _load("bootstrap")
docs_lint = _load("docs_lint.py")
MODULES = list(config.load_schema(REPO_ROOT / ".sop" / "schema.json")["properties"]["modules"]["properties"])


def module_paths():
    """{module: [paths]} from .sop/managed.txt."""
    out: dict[str, list[str]] = {}
    for line in (REPO_ROOT / ".sop" / "managed.txt").read_text().splitlines():
        parts = line.split("#", 1)[0].split()
        for tag in parts[1:]:
            if tag.startswith("module:"):
                out.setdefault(tag[len("module:"):], []).append(parts[0])
    return out


def test_every_module_path_exists_in_the_template():
    for module, paths in module_paths().items():
        for rel in paths:
            assert (REPO_ROOT / rel.rstrip("/")).exists(), f"{module}: {rel}"


def test_workflows_sit_directly_in_the_workflows_directory():
    """GitHub ignores workflow files in subdirectories of .github/workflows/."""
    assert [p for p in WORKFLOWS.iterdir() if p.is_dir()] == []
    for paths in module_paths().values():
        for rel in paths:
            if rel.startswith(".github/workflows/"):
                assert rel.count("/") == 2 and rel.split("/")[-1].startswith("module-"), rel


@pytest.mark.parametrize("name", ["module-docs-lint.yml", "module-claude-review.yml"])
def test_module_workflows_skip_the_template_repo(name):
    text = (WORKFLOWS / name).read_text()
    assert ".github/workflows/self-ci.yml" in text and "needs.detect.outputs.project == 'true'" in text


def test_claude_review_is_gated_and_uses_the_checked_secret():
    text = (WORKFLOWS / "module-claude-review.yml").read_text()
    assert f"secrets.{bootstrap.CLAUDE_REVIEW_SECRET}" in text  # the secret B6 checks
    assert "'@claude'" in text  # only when mentioned
    assert '["OWNER", "MEMBER", "COLLABORATOR"]' in text  # never for drive-by commenters
    assert "anthropics/claude-code-action@v" in text


# ---------------------------------------------------------------------------
# docs_lint
# ---------------------------------------------------------------------------


@pytest.fixture
def docs(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "a.md").write_text("# Title\n\n## Second part / Two\n")
    return tmp_path


@pytest.mark.parametrize("text, broken", [
    ("[ok](a.md) [ok](a.md#second-part--two) [web](https://example.com/x.md)", False),
    ("[missing](nope.md)", True),
    ("[bad anchor](a.md#third)", True),
    ("```\n[inside a fence](nope.md)\n```\n", False),
])
def test_docs_lint(docs, text, broken):
    (docs / "b.md").write_text(text + "\n")
    assert bool(docs_lint.check_file(docs, "b.md")) is broken


def test_docs_lint_passes_on_the_template():
    assert docs_lint.main(["--root", str(REPO_ROOT)]) == 0


# ---------------------------------------------------------------------------
# B7 for every combination of module switches
# ---------------------------------------------------------------------------


def _copy_template(dest):
    files = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                           cwd=REPO_ROOT, capture_output=True, text=True).stdout.split()
    for rel in files:
        if (REPO_ROOT / rel).is_file():
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO_ROOT / rel, dest / rel)


@pytest.mark.parametrize("switches", list(itertools.product([False, True], repeat=len(MODULES))),
                         ids=lambda s: "-".join(f"{m}={'on' if v else 'off'}" for m, v in zip(MODULES, s)))
def test_b7_is_right_for_every_module_combination(tmp_path, switches):
    root = tmp_path / "project"
    _copy_template(root)
    answers = {p: bootstrap.get_path(config.load_yaml_file(FIXTURES / "completed-config.yml"), p)
               for p, _ in bootstrap.fields(config.load_schema(REPO_ROOT / ".sop" / "schema.json"))}
    for module, on in zip(MODULES, switches):
        answers[f"modules.{module}"] = on
    assert bootstrap.write_config(root, answers) == []
    bootstrap.apply(root)
    for module, on in zip(MODULES, switches):
        for rel in module_paths()[module]:
            assert (root / rel.rstrip("/")).exists() is on, f"{module}={on}: {rel}"
    results = bootstrap.check(root, run_tests=False)
    assert results["B7"][0] == "passed", results["B7"][1]
    assert results["B6"][0] == ("pending" if switches[MODULES.index("claude_review")] else "not_applicable")


def test_b7_fails_when_a_disabled_module_file_comes_back(tmp_path):
    root = tmp_path / "project"
    _copy_template(root)
    answers = {p: bootstrap.get_path(config.load_yaml_file(FIXTURES / "completed-config.yml"), p)
               for p, _ in bootstrap.fields(config.load_schema(REPO_ROOT / ".sop" / "schema.json"))}
    answers["modules.docs_lint"] = False
    assert bootstrap.write_config(root, answers) == []
    bootstrap.apply(root)
    (root / ".github" / "workflows" / "module-docs-lint.yml").write_text("name: x\n")
    status, evidence = bootstrap.check(root, run_tests=False)["B7"]
    assert status == "failed" and "module-docs-lint.yml" in evidence
