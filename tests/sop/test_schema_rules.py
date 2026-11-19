"""Every rule in .sop/schema.json has a rejected and an accepted case.

The rule inventory is *discovered* from the schema, and
test_every_rule_has_cases fails if a rule is added without cases. This is the
evidence for open question 4 (is the schema subset enough?).
"""

from __future__ import annotations

import copy
import json

import pytest

import config
from conftest import REPO_ROOT

# ---------------------------------------------------------------------------
# Schema walking helpers
# ---------------------------------------------------------------------------


def walk(schema: dict, path: str = ""):
    """Yield (path, node) for every node. Array items get a "[]" suffix."""
    yield path, schema
    for name, sub in schema.get("properties", {}).items():
        yield from walk(sub, f"{path}.{name}" if path else name)
    if "items" in schema:
        yield from walk(schema["items"], f"{path}[]")


def property_paths(schema: dict) -> list[str]:
    """Paths of every named field outside array items (e.g. bot.github)."""
    return [p for p, _ in walk(schema) if p and "[]" not in p]


def object_paths(schema: dict) -> list[str]:
    return [p for p, n in walk(schema) if n.get("type") == "object"]


VALUE_KEYWORDS = ("enum", "pattern", "minLength", "minimum", "maximum", "x-not-equal-to")


def discovered_rules(schema: dict) -> set[tuple[str, str]]:
    return {(p, kw) for p, n in walk(schema) for kw in VALUE_KEYWORDS if kw in n}


# A valid sample for each array's items (completed config lists may be empty).
ITEM_SAMPLES = {
    "spec_paths[]": "docs/spec/**",
    "serial_resources[]": "db-schema",
    "append_only_files[]": "tests/implemented.txt",
    "sensitive_areas[]": "payments",
    "overrides.disabled_guards[]": {
        "guard": "evidence",
        "reason": "This project has no user interface.",
        "decision": "D-001",
    },
}


def get_at(cfg: dict, path: str):
    node = cfg
    for part in path.split("."):
        node = node[part]
    return node


def set_at(cfg: dict, path: str, value) -> None:
    *parents, last = path.split(".")
    node = cfg
    for part in parents:
        node = node[part]
    node[last] = value


def apply(cfg: dict, rule_path: str, value) -> str:
    """Put ``value`` at ``rule_path`` and return the path a violation would use.

    For item paths such as overrides.disabled_guards[].guard, the list is
    replaced by a one-element list built from ITEM_SAMPLES.
    """
    if "[]" not in rule_path:
        set_at(cfg, rule_path, value)
        return rule_path
    container, rest = rule_path.split("[]", 1)
    rest = rest.lstrip(".")
    item = copy.deepcopy(ITEM_SAMPLES[container + "[]"])
    if rest:
        item[rest] = value
    else:
        item = value
    set_at(cfg, container, [item])
    return rule_path.replace("[]", "[0]")


def good_value(filled: dict, rule_path: str):
    if "[]" not in rule_path:
        return get_at(filled, rule_path)
    container, rest = rule_path.split("[]", 1)
    item = ITEM_SAMPLES[container + "[]"]
    return item[rest.lstrip(".")] if rest else item


# ---------------------------------------------------------------------------
# Cases for value rules: (path, keyword) -> (rejected values, accepted values)
# ---------------------------------------------------------------------------

LOGIN_40 = "a" * 40
CASES = {
    ("project.name", "pattern"): (["", "   "], ["Example Project"]),
    ("project.goal", "pattern"): (["", " "], ["Show the gate works."]),
    ("owner.display_name", "pattern"): ([""], ["Example Owner"]),
    ("owner.github", "pattern"): (
        ["-example", "example-", "exa--mple", "exa_mple", "has space", LOGIN_40, ""],
        ["example-owner", "a", "A1-b2", "a" * 39],
    ),
    ("bot.github", "pattern"): (["example_bot", LOGIN_40, "@example-bot"], ["example-bot"]),
    ("bot.github", "x-not-equal-to"): (["example-owner", "Example-Owner"], ["example-bot"]),
    ("bot.github_id", "minimum"): ([0, -1], [1, 1000001]),
    ("doc_language", "enum"): (["fr", "EN", "zh-tw", "zh_TW"], ["en", "zh-TW"]),
    ("max_parallel", "minimum"): ([0, -1], [1]),
    ("max_parallel", "maximum"): ([6, 99], [5]),
    ("spec_paths[]", "pattern"): (["/etc/spec", " docs", ""], ["docs/spec/**", "*.md"]),
    ("serial_resources[]", "pattern"): (["DB", "db schema", "-db", ""], ["db-schema", "lockfile2"]),
    ("append_only_files[]", "pattern"): (["/abs.txt", ""], ["tests/implemented.txt"]),
    ("sensitive_areas[]", "pattern"): (["", "  "], ["payments"]),
    ("template.source", "pattern"): (
        ["example-owner", "owner/", "/repo", "a/b/c", "own er/repo"],
        ["example-owner/example-template", "a/b.c_d-e"],
    ),
    ("overrides.disabled_guards[].guard", "enum"): (
        ["sop-ready", "no-such-guard", "Evidence"],
        ["evidence", "done-when", "commit-author"],
    ),
    ("overrides.disabled_guards[].reason", "pattern"): ([""], ["No UI."]),
    ("overrides.disabled_guards[].decision", "pattern"): (
        ["D-1", "D-01", "d-001", "D001", "ADR-001", "D-001x"],
        ["D-001", "D-1234"],
    ),
}

WRONG_TYPE = {
    "string": [123, True, ["x"]],
    "integer": ["3", True, 2.5],
    "boolean": ["true", 1, 0],
    "array": ["docs/**", {"a": 1}],
    "object": ["text", []],
}


def has(violations, path, keyword) -> bool:
    return any(v.path == path and v.keyword == keyword for v in violations)


# ---------------------------------------------------------------------------
# Schema shape (P2 invariants)
# ---------------------------------------------------------------------------


def test_schema_uses_only_the_subset(schema):
    config.check_schema(schema)  # raises on anything outside the subset


def test_every_object_requires_all_fields_and_rejects_unknown(schema):
    """P2: no optional fields (no defaults) and no silently ignored typos."""
    for path, node in walk(schema):
        if node.get("type") == "object":
            assert set(node["required"]) == set(node["properties"]), path or "(root)"
            assert node["additionalProperties"] is False, path or "(root)"


def test_every_node_has_a_type(schema):
    for path, node in walk(schema):
        assert node.get("type") in {"object", "array", "string", "integer", "boolean"}, path


def test_every_rule_has_cases(schema):
    assert discovered_rules(schema) == set(CASES)


# ---------------------------------------------------------------------------
# The completed sample and the template
# ---------------------------------------------------------------------------


def test_completed_sample_is_valid(schema, filled):
    assert config.validate(filled, schema) == []


def test_template_reports_every_field_as_unfilled(schema):
    data = config.load_yaml_file(REPO_ROOT / ".sop" / "config.yml")
    violations = config.validate(data, schema)
    # Only "null" violations: every field is present, none is unknown.
    assert {v.keyword for v in violations} == {"null"}
    leaves = [p for p in property_paths(schema) if get_at_schema(schema, p).get("type") != "object"]
    assert sorted(v.path for v in violations) == sorted(leaves)
    for v in violations:
        assert "not filled in" in str(v) and v.path in str(v)


def get_at_schema(schema: dict, path: str) -> dict:
    node = schema
    for part in path.split("."):
        node = node["properties"][part]
    return node


# ---------------------------------------------------------------------------
# Per-rule rejected / accepted cases
# ---------------------------------------------------------------------------

_value_params = [
    pytest.param(path, kw, bad, id=f"{path}:{kw}:reject:{bad!r}")
    for (path, kw), (bads, _) in CASES.items()
    for bad in bads
]
_good_params = [
    pytest.param(path, kw, good, id=f"{path}:{kw}:accept:{good!r}")
    for (path, kw), (_, goods) in CASES.items()
    for good in goods
]


@pytest.mark.parametrize("path, keyword, bad", _value_params)
def test_value_rule_rejects(schema, filled, path, keyword, bad):
    where = apply(filled, path, bad)
    assert has(config.validate(filled, schema), where, keyword)


@pytest.mark.parametrize("path, keyword, good", _good_params)
def test_value_rule_accepts(schema, filled, path, keyword, good):
    apply(filled, path, good)
    assert config.validate(filled, schema) == []


def _type_params():
    schema = json.loads((REPO_ROOT / ".sop" / "schema.json").read_text())
    for path, node in walk(schema):
        if not path:
            continue  # the root is covered by test_root_must_be_a_mapping
        for bad in WRONG_TYPE[node["type"]]:
            yield pytest.param(path, bad, id=f"{path}:type:reject:{bad!r}")


@pytest.mark.parametrize("path, bad", list(_type_params()))
def test_type_rule_rejects(schema, filled, path, bad):
    where = apply(filled, path, bad)
    assert has(config.validate(filled, schema), where, "type")


@pytest.mark.parametrize("path", [p for p, _ in walk(json.loads((REPO_ROOT / ".sop" / "schema.json").read_text())) if p])
def test_type_rule_accepts(schema, filled, path):
    apply(filled, path, copy.deepcopy(good_value(filled, path)))
    assert config.validate(filled, schema) == []


def test_root_must_be_a_mapping(schema):
    assert has(config.validate(["not", "a", "mapping"], schema), "", "type")


# ---------------------------------------------------------------------------
# null, missing and unknown fields
# ---------------------------------------------------------------------------


def _schema():
    return json.loads((REPO_ROOT / ".sop" / "schema.json").read_text())


@pytest.mark.parametrize("path", property_paths(_schema()))
def test_any_single_field_null_fails(schema, filled, path):
    set_at(filled, path, None)
    violations = config.validate(filled, schema)
    assert has(violations, path, "null")
    assert len(violations) == 1


def test_null_list_item_fails(schema, filled):
    filled["sensitive_areas"] = ["payments", None]
    assert has(config.validate(filled, schema), "sensitive_areas[1]", "null")


@pytest.mark.parametrize("path", property_paths(_schema()))
def test_any_missing_field_fails(schema, filled, path):
    *parents, last = path.split(".")
    node = filled
    for part in parents:
        node = node[part]
    del node[last]
    assert has(config.validate(filled, schema), path, "required")


@pytest.mark.parametrize("path", object_paths(_schema()))
def test_unknown_field_fails(schema, filled, path):
    if path == "":
        filled["unexpected"] = 1
        where = "unexpected"
    elif "[]" in path:
        item = dict(ITEM_SAMPLES[path], unexpected=1)
        set_at(filled, path[:-2], [item])
        where = path.replace("[]", "[0]") + ".unexpected"
    else:
        get_at(filled, path)["unexpected"] = 1
        where = f"{path}.unexpected"
    assert has(config.validate(filled, schema), where, "additionalProperties")


def test_all_violations_are_reported_at_once(schema, filled):
    filled["max_parallel"] = 9
    filled["doc_language"] = "fr"
    filled["bot"]["github"] = "example-owner"
    violations = config.validate(filled, schema)
    assert {(v.path, v.keyword) for v in violations} == {
        ("max_parallel", "maximum"),
        ("doc_language", "enum"),
        ("bot.github", "x-not-equal-to"),
    }


# ---------------------------------------------------------------------------
# The validator itself: subset boundaries
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_schema",
    [
        {"type": "string", "format": "email"},  # unsupported keyword
        {"type": "null"},  # null is never a valid type
        {"type": ["string", "null"]},  # the usual way to allow null
        {"type": "number"},  # floats are not in the subset
        {"type": "object", "additionalProperties": True},
        {"type": "string", "pattern": "("},  # invalid regex
        {"type": "string", "enum": []},
        {"type": "integer", "minimum": "1"},
        {"type": "object", "required": ["a"], "properties": {}},
        {"type": "string", "x-not-equal-to": "/a"},  # wrong shape
        {"type": "object", "properties": {"a": {"type": "string", "oneOf": []}}},  # nested
    ],
)
def test_check_schema_rejects_outside_subset(bad_schema):
    with pytest.raises(config.SchemaError):
        config.check_schema(bad_schema)


def test_min_length_keyword():
    """minLength is in the subset but unused by the config schema today."""
    s = {"type": "string", "minLength": 3}
    assert has(config.validate("ab", s), "", "minLength")
    assert config.validate("abc", s) == []


def test_not_equal_is_case_sensitive_unless_asked():
    s = {
        "type": "object",
        "required": ["a", "b"],
        "properties": {"a": {"type": "string"}, "b": {"type": "string", "x-not-equal-to": {"pointer": "/a"}}},
    }
    assert config.validate({"a": "X", "b": "x"}, s) == []
    assert has(config.validate({"a": "x", "b": "x"}, s), "b", "x-not-equal-to")


def test_enum_does_not_confuse_bool_and_int():
    assert has(config.validate(True, {"type": "integer", "enum": [1]}), "", "type")
    assert has(config.validate(1, {"enum": [True]}), "", "enum")
