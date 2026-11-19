"""The restricted YAML subset (decision D12): what it accepts, what it refuses.

Refusals matter as much as acceptances: anything a standard YAML parser could
read differently must be an error with a fix, never a silent guess.
"""

from __future__ import annotations

import pytest

import config
from conftest import FIXTURES, REPO_ROOT


def test_template_config_parses_to_all_null():
    data = config.load_yaml_file(REPO_ROOT / ".sop" / "config.yml")

    def leaves(node):
        for value in node.values():
            if isinstance(value, dict):
                yield from leaves(value)
            else:
                yield value

    assert list(leaves(data)) and all(v is None for v in leaves(data))


def test_completed_fixture_parses():
    data = config.load_yaml_file(FIXTURES / "completed-config.yml")
    assert data["bot"] == {"github": "example-bot", "github_id": 1000001}
    assert data["spec_paths"] == ["docs/spec/**"]
    assert data["append_only_files"] == []
    assert data["modules"] == {"learning": True, "claude_review": False, "docs_lint": False}


@pytest.mark.parametrize(
    "text, expected",
    [
        ("a: 1\n", {"a": 1}),
        ("a: -3\n", {"a": -3}),
        ("a: 0\n", {"a": 0}),
        ("a: true\nb: false\nc: null\n", {"a": True, "b": False, "c": None}),
        ("a: hello world\n", {"a": "hello world"}),
        ("a: zh-TW\n", {"a": "zh-TW"}),
        ("a: 1.0.0\n", {"a": "1.0.0"}),  # not a number in any YAML version
        ("a: owner/repo\n", {"a": "owner/repo"}),
        ("a: it's\n", {"a": "it's"}),
        ("a: a#b\n", {"a": "a#b"}),  # "#" inside a word is text
        ("a: x  # comment\n", {"a": "x"}),
        ('a: "no"\n', {"a": "no"}),
        ("a: 'no'\n", {"a": "no"}),
        ('a: "**/*.md"  # glob\n', {"a": "**/*.md"}),
        ('a: "say \\"hi\\" \\\\ ok"\n', {"a": 'say "hi" \\ ok'}),
        ("a: 'it''s'\n", {"a": "it's"}),
        ('a: ""\n', {"a": ""}),
        ("a: []\n", {"a": []}),
        ("a: []  # none\n", {"a": []}),
        ("a: [T-010]\n", {"a": ["T-010"]}),  # ticket depends_on (D17)
        ("a: [T-010, T-011]  # deps\n", {"a": ["T-010", "T-011"]}),
        ("a: [ p ,q ]\n", {"a": ["p", "q"]}),
        ('a: ["**/*.md", \'a, b\', 3]\n', {"a": ["**/*.md", "a, b", 3]}),
        ("a: [null, true]\n", {"a": [None, True]}),
        ("a:\n  - x\n  - 'y'\n", {"a": ["x", "y"]}),
        ("a:  # note\n  b: 1\n", {"a": {"b": 1}}),
        ("a:\n    b: 1\n    c:\n      d: 2\ne: 3\n", {"a": {"b": 1, "c": {"d": 2}}, "e": 3}),
        (
            "a:\n  - k: 1\n    j: p\n  - k: 2\n    j: q\n",
            {"a": [{"k": 1, "j": "p"}, {"k": 2, "j": "q"}]},
        ),
        ("# only a comment\n\na: 1\n", {"a": 1}),
        ("a: 1\r\nb: 2\r\n", {"a": 1, "b": 2}),  # Windows line endings
        ("\ufeffa: 1\n", {"a": 1}),  # BOM
        ("a: 1", {"a": 1}),  # no final newline
    ],
)
def test_accepts(text, expected):
    assert config.parse_yaml(text) == expected


@pytest.mark.parametrize(
    "text, line, fragment",
    [
        ("", 1, "empty"),
        ("# nothing\n", 1, "empty"),
        ("a:\tb\n", 1, "tab"),
        ("\ta: 1\n", 1, "tab"),
        ("a: 1\n---\nb: 2\n", 2, "document markers"),
        ("%YAML 1.2\na: 1\n", 1, "directives"),
        ("a:\n", 1, "write null"),
        ("a:\nb: 1\n", 1, "write null"),
        ("a: ~\n", 1, "ambiguous"),
        ("a: yes\n", 1, "ambiguous"),
        ("a: y\n", 1, "ambiguous"),  # YAML 1.1 reads y as true
        ("a: No\n", 1, "ambiguous"),
        ("a: on\n", 1, "ambiguous"),
        ("a: True\n", 1, "ambiguous"),
        ("a: NULL\n", 1, "ambiguous"),
        ("a: 0123\n", 1, "number"),
        ("a: 1.5\n", 1, "number"),
        ("a: 1e3\n", 1, "number"),
        ("a: 0x1F\n", 1, "number"),
        ("a: +1\n", 1, "number"),
        ("a: 1_000\n", 1, "number"),
        ("a: .inf\n", 1, "number"),
        ("a: 12:30\n", 1, "number"),  # YAML 1.1 reads this as 750
        ("a: 2026-11-19\n", 1, "date"),
        ("a: **/*.md\n", 1, "must be quoted"),
        ("a: &anchor x\n", 1, "must be quoted"),
        ("a: *alias\n", 1, "must be quoted"),
        ("a: !tag x\n", 1, "must be quoted"),
        ("a: {b: 1}\n", 1, "must be quoted"),
        ("a: [x, [y]]\n", 1, "nested"),
        ("a:\n  - [x, y]\n", 2, "nested"),  # a flow list inside a block list
        ("a:\n  - []\n", 2, "nested"),
        ("a: [x, {y: 1}]\n", 1, "nested"),
        ("a: [x,]\n", 1, "empty item"),
        ("a: [, x]\n", 1, "empty item"),
        ("a: [x,, y]\n", 1, "empty item"),
        ("a: [x\n", 1, "unterminated"),
        ("a: [x] y\n", 1, "after ']'"),
        ("a: [yes]\n", 1, "ambiguous"),
        ("a: [0123]\n", 1, "number"),
        ("a: [**/*.md]\n", 1, "must be quoted"),
        ('a: ["x]\n', 1, "unterminated"),
        ("a: |\n  text\n", 1, "must be quoted"),
        ("a: @-x\n", 1, "must be quoted"),
        ("a: b: c\n", 1, "': '"),
        ("a: b:\n", 1, "': '"),
        ('a: "open\n', 1, "unterminated"),
        ('a: "x" y\n', 1, "after the closing quote"),
        ('a: "\\n"\n', 1, "unsupported escape"),
        ("a: 1\na: 2\n", 2, "duplicate key"),
        ("a:1\n", 1, "expected 'key: value'"),
        ("my-key: 1\n", 1, "expected 'key: value'"),
        ('"a": 1\n', 1, "expected 'key: value'"),
        ("  a: 1\n", 1, "indented"),
        ("- a\n", 1, "top level"),
        ("a: 1\n  b: 2\n", 2, "unexpected indentation"),
        ("a:\n  b: 1\n c: 2\n", 3, "unexpected indentation"),
        ("a:\n  - x\n  b: 1\n", 3, "cannot follow list items"),
        ("a:\n  b: 1\n  - x\n", 3, "list item cannot appear"),
        ("a:\n  -\n", 2, "same line"),
        ("a:\n  - x\n    - y\n", 3, "unexpected indentation"),
        ("a: 1\x00\n", 1, "control character"),
    ],
)
def test_rejects(text, line, fragment):
    with pytest.raises(config.ConfigSyntaxError) as info:
        config.parse_yaml(text)
    assert info.value.line == line
    assert fragment in info.value.message


TRICKY_STRINGS = [
    "no", "Yes", "~", "null", "true", "0123", "1.5", "12:30", "2026-01-01",
    "**/*.md", "-dash", "a: b", "ends:", "x #y", "trailing ", " leading",
    "", "it's", 'say "hi"', "back\\slash", "[]", "{}", "@-x", "plain text",
]


def test_round_trip_of_tricky_strings():
    data = {"items": TRICKY_STRINGS, "one": "no", "nested": {"value": "**"}}
    text = config.dump_yaml(data)
    assert config.parse_yaml(text) == data


def test_round_trip_of_completed_fixture():
    data = config.load_yaml_file(FIXTURES / "completed-config.yml")
    data["overrides"]["disabled_guards"] = [
        {"guard": "evidence", "reason": "No UI: CLI only.", "decision": "D-001"},
        {"guard": "tests", "reason": "no", "decision": "D-002"},
    ]
    assert config.parse_yaml(config.dump_yaml(data)) == data


@pytest.mark.parametrize(
    "data",
    [
        {"a": "two\nlines"},
        {"a": {}},
        {"a": [[1]]},
        {"a": 1.5},
        {"bad-key": 1},
    ],
)
def test_dump_refuses_what_the_subset_cannot_hold(data):
    with pytest.raises((ValueError, TypeError)):
        config.dump_yaml(data)


def test_agrees_with_a_real_yaml_parser():
    """Anything the subset accepts must mean the same to PyYAML (YAML 1.1).

    The subset refuses every construct where YAML 1.1 and 1.2 differ, so
    agreeing with 1.1 on accepted input implies agreeing with 1.2 too.
    Skipped when PyYAML is not installed (it is not a CI dependency).
    """
    yaml = pytest.importorskip("yaml")
    samples = [
        (REPO_ROOT / ".sop" / "config.yml").read_text(),
        (REPO_ROOT / ".sop" / "bootstrap.yml").read_text(),
        (FIXTURES / "completed-config.yml").read_text(),
        (FIXTURES / "completed-bootstrap.yml").read_text(),
        config.dump_yaml({"items": TRICKY_STRINGS}),
        "deps: [T-010, T-011]\nmixed: ['a, b', \"**/*.md\", 3, null]\nnone: []\n",
    ]
    for text in samples:
        assert config.parse_yaml(text) == yaml.safe_load(text)
