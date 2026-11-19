#!/usr/bin/env python3
"""Load and validate the sop-v2 project configuration (.sop/config.yml).

Standard library only, Python >= 3.11 (design doc 14.2, decision D13).

The module has three parts:

1. A parser and emitter for a *restricted YAML subset* (decision D12).
   The subset is chosen so that:
     * it has a native ``null``: P2 needs every field present and unset in the
       template, which TOML cannot express;
     * it allows comments next to each field, for people editing by hand, which
       JSON cannot;
     * anything it accepts means the same thing to a standard YAML 1.2 parser.
       Constructs that are ambiguous between YAML versions (``yes``, ``no``,
       ``~``, ``0123``, dates, ...) are rejected with a hint to quote them,
       never guessed. Unsupported YAML features fail loudly; they are never
       silently misread.

2. A validator for a small JSON Schema subset (design doc 14.2, open question 4).
   Supported keywords: ``type`` (a single name), ``properties``, ``required``,
   ``additionalProperties`` (``false`` only), ``items``, ``enum``, ``pattern``,
   ``minLength``, ``minimum``, ``maximum`` and one extension,
   ``x-not-equal-to`` (cross-field inequality). Annotation keywords
   (``$schema``, ``title``, ``description``, ``$comment``) are ignored.
   Any other keyword is a schema error, so a rule is never silently skipped.

3. A command line: ``python3 scripts/sop/config.py [--config P] [--schema P]``
   prints every violation with its field path and exits 1 if there are any.

Design choice: the validator *collects* every violation instead of stopping at
the first one, so a person filling the file by hand sees the whole list at once.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Restricted YAML subset
# ---------------------------------------------------------------------------


class ConfigSyntaxError(ValueError):
    """The text is not in the supported YAML subset. Carries a 1-based line."""

    def __init__(self, line: int, message: str):
        super().__init__(f"line {line}: {message}")
        self.line = line
        self.message = message


# A mapping key: plain identifier. Keeping keys this narrow means a key never
# needs quoting and can't be confused with a scalar.
_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):(?:[ ]+(.*))?$")
_INT_RE = re.compile(r"^-?(?:0|[1-9][0-9]*)$")

# Plain scalars that YAML 1.1 and 1.2 read differently, or that read as
# something other than text. We refuse to guess; the user must quote them
# (if they mean text) or write the canonical form.
_AMBIGUOUS_WORDS = {
    "y", "yes", "n", "no", "on", "off", "true", "false", "null", "~",
}
_NUMBER_LIKE_RE = re.compile(
    r"^[-+]?(?:"
    r"[0-9][0-9_]*(?:\.[0-9_]*)?(?:[eE][-+]?[0-9]+)?"  # 0123, 1.5, 1e3, 1_000
    r"|\.[0-9]+(?:[eE][-+]?[0-9]+)?"                     # .5
    r"|0[xXoObB][0-9A-Fa-f_]+"                           # 0x1F, 0o17, 0b10
    r"|\.(?:inf|Inf|INF|nan|NaN|NAN)"                    # .inf, .nan
    r"|[0-9][0-9_]*(?::[0-5]?[0-9])+(?:\.[0-9_]*)?"      # 12:30 (YAML 1.1 base 60)
    r")$"
)
_DATE_LIKE_RE = re.compile(r"^[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}")
# Characters that start a special construct when they begin a plain scalar.
_INDICATORS = set("-?:,[]{}#&*!|>'\"%@`")


@dataclass
class _Line:
    indent: int
    text: str  # content after the indentation, comments not yet removed
    number: int  # 1-based


def _split_lines(text: str) -> list[_Line]:
    """Split into significant lines, rejecting characters the subset forbids."""
    if text.startswith("﻿"):  # tolerate a UTF-8 BOM from Windows editors
        text = text[1:]
    lines: list[_Line] = []
    for number, raw in enumerate(text.split("\n"), start=1):
        raw = raw.removesuffix("\r")  # tolerate CRLF line endings
        if "\t" in raw:
            raise ConfigSyntaxError(number, "tab character found; indent with spaces only")
        if any(ord(c) < 32 for c in raw):
            raise ConfigSyntaxError(number, "control character found")
        stripped = raw.lstrip(" ")
        if not stripped or stripped.startswith("#"):
            continue  # blank line or full-line comment
        if raw.startswith(("---", "...", "%")):
            raise ConfigSyntaxError(
                number, "document markers and directives (---, ..., %) are not supported"
            )
        lines.append(_Line(len(raw) - len(stripped), stripped, number))
    return lines


def _strip_comment(value: str, number: int) -> str:
    """Remove a trailing ``# comment`` from a value. Quote-aware."""
    if value.startswith("#"):  # "key:   # note" -> no value, only a comment
        return ""
    if value[:1] in ("'", '"'):
        end = _closing_quote(value, number)
        rest = value[end + 1:]
        if rest.strip() and not (rest.startswith(" ") and rest.lstrip().startswith("#")):
            raise ConfigSyntaxError(number, "unexpected text after the closing quote")
        return value[: end + 1]
    # In YAML a comment starts with " #"; a "#" inside a word is text.
    cut = value.find(" #")
    if cut != -1:
        value = value[:cut]
    return value.rstrip(" ")


def _closing_quote(value: str, number: int) -> int:
    """Index of the quote that closes the string starting at value[0]."""
    quote = value[0]
    i = 1
    while i < len(value):
        c = value[i]
        if quote == '"' and c == "\\":
            i += 2
            continue
        if c == quote:
            if quote == "'" and value[i + 1:i + 2] == "'":  # '' is an escaped '
                i += 2
                continue
            return i
        i += 1
    raise ConfigSyntaxError(number, "unterminated quoted string")


def _parse_scalar(value: str, number: int) -> Any:
    """Turn the text of one value into None, bool, int, str or []."""
    if value == "":
        raise ConfigSyntaxError(
            number, "missing value; write null if the field is not filled in yet"
        )
    if value[0] == '"':
        body = value[1:-1]
        # Only \\ and \" escapes are supported; anything else is ambiguous.
        out, i = [], 0
        while i < len(body):
            if body[i] == "\\":
                nxt = body[i + 1:i + 2]
                if nxt not in ("\\", '"'):
                    raise ConfigSyntaxError(
                        number, f"unsupported escape '\\{nxt}'; only \\\\ and \\\" are allowed"
                    )
                out.append(nxt)
                i += 2
            else:
                out.append(body[i])
                i += 1
        return "".join(out)
    if value[0] == "'":
        return value[1:-1].replace("''", "'")
    if value.startswith("["):
        return _parse_flow_list(value, number)
    if value in ("null",):
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if _INT_RE.match(value):
        return int(value)
    # Everything below is a plain (unquoted) string; reject the risky ones.
    if value.lower() in _AMBIGUOUS_WORDS or value == "":
        raise ConfigSyntaxError(
            number,
            f"'{value}' is ambiguous in YAML; use true, false or null exactly, "
            f"or quote it if you mean text: \"{value}\"",
        )
    if _NUMBER_LIKE_RE.match(value):
        raise ConfigSyntaxError(
            number,
            f"'{value}' looks like a number but is not a plain integer; "
            f"quote it if you mean text: \"{value}\"",
        )
    if _DATE_LIKE_RE.match(value):
        raise ConfigSyntaxError(
            number, f"'{value}' looks like a date; quote it: \"{value}\""
        )
    if value[0] in _INDICATORS:
        raise ConfigSyntaxError(
            number,
            f"text starting with '{value[0]}' must be quoted, e.g. \"{value}\" "
            "(flow collections, anchors, aliases and tags are not supported)",
        )
    if ": " in value or value.endswith(":"):
        raise ConfigSyntaxError(number, f"text containing ': ' must be quoted: \"{value}\"")
    return value


def _parse_flow_list(value: str, number: int) -> list:
    """Parse a one-line list such as ``[T-010, T-011]`` or ``[]``.

    Only scalars are allowed inside; each item follows the same rules as a
    value on its own (so ``[yes]`` and ``[**]`` are rejected like ``yes`` and
    ``**``). Nested lists or mappings, empty items, and text after the closing
    bracket are errors. Quoted items may contain commas.
    """
    items: list[str] = []
    current: list[str] = []
    quote = ""
    i = 1
    while True:
        if i >= len(value):
            raise ConfigSyntaxError(number, "unterminated list; close it with ']' on the same line")
        c = value[i]
        if quote:
            current.append(c)
            if quote == '"' and c == "\\":
                current.append(value[i + 1:i + 2])
                i += 2
                continue
            if c == quote:
                if quote == "'" and value[i + 1:i + 2] == "'":
                    current.append("'")
                    i += 2
                    continue
                quote = ""
        elif c in ("'", '"') and not "".join(current).strip():
            quote = c
            current.append(c)
        elif c in "[{":
            raise ConfigSyntaxError(number, "nested lists or mappings are not supported inside [ ]")
        elif c == ",":
            items.append("".join(current))
            current = []
        elif c == "]":
            items.append("".join(current))
            break
        else:
            current.append(c)
        i += 1
    if value[i + 1:].strip():
        raise ConfigSyntaxError(number, "unexpected text after ']'")
    if len(items) == 1 and not items[0].strip():
        return []
    result = []
    for raw in items:
        item = raw.strip()
        if not item:
            raise ConfigSyntaxError(number, "empty item in list; remove the extra ','")
        if item[0] in ("'", '"') and _closing_quote(item, number) != len(item) - 1:
            raise ConfigSyntaxError(number, "unexpected text after the closing quote")
        result.append(_parse_scalar(item, number))
    return result


class _Parser:
    """Recursive descent over indentation levels.

    A block is either a mapping (lines "key: value") or a list (lines "- item")
    at one indentation. Nested blocks must be indented more than their key.
    """

    def __init__(self, lines: list[_Line]):
        self.lines = lines
        self.i = 0

    def parse_document(self) -> dict:
        if not self.lines:
            raise ConfigSyntaxError(1, "the file is empty")
        first = self.lines[0]
        if first.indent != 0:
            raise ConfigSyntaxError(first.number, "the first line must not be indented")
        if self._is_list_item(first):
            raise ConfigSyntaxError(first.number, "the top level must be 'key: value' lines")
        result = self._parse_mapping(0)
        if self.i < len(self.lines):
            line = self.lines[self.i]
            raise ConfigSyntaxError(line.number, "unexpected indentation")
        return result

    @staticmethod
    def _is_list_item(line: _Line) -> bool:
        return line.text == "-" or line.text.startswith("- ")

    def _parse_block(self, indent: int) -> Any:
        line = self.lines[self.i]
        if self._is_list_item(line):
            return self._parse_list(indent)
        return self._parse_mapping(indent)

    def _parse_mapping(self, indent: int) -> dict:
        result: dict[str, Any] = {}
        while self.i < len(self.lines):
            line = self.lines[self.i]
            if line.indent < indent:
                break
            if line.indent > indent:
                raise ConfigSyntaxError(line.number, "unexpected indentation")
            if self._is_list_item(line):
                raise ConfigSyntaxError(
                    line.number, "a list item cannot appear among 'key: value' lines"
                )
            match = _KEY_RE.match(line.text)
            if not match:
                raise ConfigSyntaxError(
                    line.number,
                    "expected 'key: value' (keys use letters, digits and _; "
                    "a space is required after ':')",
                )
            key, rest = match.group(1), _strip_comment(match.group(2) or "", line.number)
            if key in result:
                raise ConfigSyntaxError(line.number, f"duplicate key '{key}'")
            self.i += 1
            if rest == "":
                # "key:" alone opens a nested block, which must be indented more.
                if self.i >= len(self.lines) or self.lines[self.i].indent <= indent:
                    raise ConfigSyntaxError(
                        line.number,
                        f"'{key}' has no value; write null if it is not filled in yet",
                    )
                result[key] = self._parse_block(self.lines[self.i].indent)
            else:
                result[key] = _parse_scalar(rest, line.number)
        return result

    def _parse_list(self, indent: int) -> list:
        result: list[Any] = []
        while self.i < len(self.lines):
            line = self.lines[self.i]
            if line.indent < indent:
                break
            if line.indent > indent:
                raise ConfigSyntaxError(line.number, "unexpected indentation")
            if not self._is_list_item(line):
                raise ConfigSyntaxError(
                    line.number, "'key: value' lines cannot follow list items at the same indentation"
                )
            item = line.text[1:]
            spaces = len(item) - len(item.lstrip(" "))
            item = item.lstrip(" ")
            if item == "" or item.startswith("#"):
                raise ConfigSyntaxError(
                    line.number, "put the list item on the same line as '-'"
                )
            if _KEY_RE.match(item):
                # "- key: value" starts a mapping whose keys align with "key".
                # Rewrite this line as the mapping's first line and recurse.
                item_indent = indent + 1 + spaces
                self.lines[self.i] = _Line(item_indent, item, line.number)
                result.append(self._parse_mapping(item_indent))
            else:
                value = _strip_comment(item, line.number)
                if value.startswith("["):
                    # A list inside a list is not in the subset (dump_yaml can't write it).
                    raise ConfigSyntaxError(line.number, "nested lists are not supported")
                result.append(_parse_scalar(value, line.number))
                self.i += 1
        return result


def parse_yaml(text: str) -> dict:
    """Parse text in the restricted YAML subset. Raises ConfigSyntaxError."""
    return _Parser(_split_lines(text)).parse_document()


def _emit_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        if any(ord(c) < 32 for c in value):
            raise ValueError("multi-line strings and control characters are not supported")
        try:  # emit plain if it reads back as the same string
            if _parse_scalar(value, 0) == value and " #" not in value and value.strip() == value:
                return value
        except ConfigSyntaxError:
            pass
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    raise TypeError(f"unsupported value type: {type(value).__name__}")


def dump_yaml(data: dict, indent: int = 0) -> str:
    """Write a dict in the restricted YAML subset (inverse of parse_yaml).

    The fallback bootstrap script (S3) needs to write the config file with the
    standard library only, which is one reason the format is a subset we own.
    """
    pad = " " * indent
    out: list[str] = []
    for key, value in data.items():
        if not isinstance(key, str) or not _KEY_RE.match(key + ":"):
            raise ValueError(f"unsupported key: {key!r}")
        if isinstance(value, dict):
            if not value:
                raise ValueError("empty mappings are not supported")
            out.append(f"{pad}{key}:")
            out.append(dump_yaml(value, indent + 2).rstrip("\n"))
        elif isinstance(value, list) and value:
            out.append(f"{pad}{key}:")
            for item in value:
                if isinstance(item, dict):
                    if not item:
                        raise ValueError("empty mappings are not supported")
                    body = dump_yaml(item, indent + 4).rstrip("\n").split("\n")
                    out.append(f"{pad}  - {body[0].lstrip()}")
                    out.extend(body[1:])
                elif isinstance(item, list):
                    raise ValueError("nested lists are not supported")
                else:
                    out.append(f"{pad}  - {_emit_scalar(item)}")
        elif isinstance(value, list):
            out.append(f"{pad}{key}: []")
        else:
            out.append(f"{pad}{key}: {_emit_scalar(value)}")
    return "\n".join(out) + "\n"


def load_yaml_file(path: Path) -> dict:
    return parse_yaml(Path(path).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# JSON Schema subset
# ---------------------------------------------------------------------------


class SchemaError(ValueError):
    """The schema itself uses something outside the supported subset."""


_ANNOTATIONS = {"$schema", "title", "description", "$comment"}
_KEYWORDS = {
    "type", "properties", "required", "additionalProperties", "items",
    "enum", "pattern", "minLength", "minimum", "maximum", "x-not-equal-to",
}
_TYPES = {"object", "array", "string", "integer", "boolean"}


@dataclass(frozen=True)
class Violation:
    """One failed rule. ``path`` is like ``bot.github`` or ``spec_paths[0]``."""

    path: str
    keyword: str  # the schema keyword that failed, or "null" for unset values
    message: str

    def __str__(self) -> str:
        return f"{self.path or '(root)'}: {self.message}"


def check_schema(schema: Any, where: str = "#") -> None:
    """Raise SchemaError if the schema uses anything outside the subset."""
    if not isinstance(schema, dict):
        raise SchemaError(f"{where}: a schema must be an object")
    unknown = set(schema) - _KEYWORDS - _ANNOTATIONS
    if unknown:
        raise SchemaError(f"{where}: unsupported keyword(s): {', '.join(sorted(unknown))}")
    t = schema.get("type")
    if t is not None and (not isinstance(t, str) or t not in _TYPES):
        raise SchemaError(f"{where}: unsupported type {t!r} (null is never allowed)")
    if "additionalProperties" in schema and schema["additionalProperties"] is not False:
        raise SchemaError(f"{where}: additionalProperties must be false")
    if "pattern" in schema:
        try:
            re.compile(schema["pattern"])
        except re.error as exc:
            raise SchemaError(f"{where}: invalid pattern: {exc}") from exc
    if "enum" in schema and (not isinstance(schema["enum"], list) or not schema["enum"]):
        raise SchemaError(f"{where}: enum must be a non-empty list")
    for key in ("minimum", "maximum", "minLength"):
        if key in schema and (not isinstance(schema[key], int) or isinstance(schema[key], bool)):
            raise SchemaError(f"{where}: {key} must be an integer")
    if "required" in schema:
        missing = set(schema["required"]) - set(schema.get("properties", {}))
        if missing:
            raise SchemaError(f"{where}: required names unknown properties: {sorted(missing)}")
    if "x-not-equal-to" in schema:
        spec = schema["x-not-equal-to"]
        if (
            not isinstance(spec, dict)
            or set(spec) - {"pointer", "ignore_case"}
            or not isinstance(spec.get("pointer"), str)
            or not spec["pointer"].startswith("/")
        ):
            raise SchemaError(
                f"{where}: x-not-equal-to must be {{\"pointer\": \"/a/b\", \"ignore_case\": bool}}"
            )
    for name, sub in schema.get("properties", {}).items():
        check_schema(sub, f"{where}/properties/{name}")
    if "items" in schema:
        check_schema(schema["items"], f"{where}/items")


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):  # bool is a subclass of int in Python
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _resolve_pointer(root: Any, pointer: str) -> Any:
    """Follow a JSON Pointer like /owner/github. Returns None if absent."""
    node = root
    for part in pointer.lstrip("/").split("/"):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def _join(path: str, key: str) -> str:
    return f"{path}.{key}" if path else key


def _validate(value: Any, schema: dict, path: str, root: Any, out: list[Violation]) -> None:
    if value is None:
        out.append(Violation(path, "null", "is not filled in (null); every field needs an explicit value"))
        return
    expected = schema.get("type")
    if expected and _type_name(value) != expected:
        out.append(Violation(path, "type", f"must be {expected}, got {_type_name(value)} ({value!r})"))
        return  # further checks would only add noise

    # Compare type as well as value: in Python, True == 1.
    if "enum" in schema and not any(
        _type_name(value) == _type_name(e) and value == e for e in schema["enum"]
    ):
        allowed = ", ".join(map(str, schema["enum"]))
        out.append(Violation(path, "enum", f"{value!r} is not one of: {allowed}"))
    if "pattern" in schema and isinstance(value, str) and not re.search(schema["pattern"], value):
        out.append(Violation(path, "pattern", f"{value!r} does not match the pattern {schema['pattern']}"))
    if "minLength" in schema and isinstance(value, str) and len(value) < schema["minLength"]:
        out.append(Violation(path, "minLength", f"must be at least {schema['minLength']} characters"))
    if "minimum" in schema and isinstance(value, int) and value < schema["minimum"]:
        out.append(Violation(path, "minimum", f"must be >= {schema['minimum']}, got {value}"))
    if "maximum" in schema and isinstance(value, int) and value > schema["maximum"]:
        out.append(Violation(path, "maximum", f"must be <= {schema['maximum']}, got {value}"))

    if "x-not-equal-to" in schema:
        spec = schema["x-not-equal-to"]
        other = _resolve_pointer(root, spec["pointer"])
        a, b = value, other
        if spec.get("ignore_case") and isinstance(a, str) and isinstance(b, str):
            a, b = a.casefold(), b.casefold()
        if other is not None and a == b:
            other_path = spec["pointer"].lstrip("/").replace("/", ".")
            out.append(Violation(path, "x-not-equal-to", f"must differ from {other_path} ({other!r})"))

    if isinstance(value, dict):
        props = schema.get("properties", {})
        for name in schema.get("required", []):
            if name not in value:
                out.append(Violation(_join(path, name), "required", "is missing (required field)"))
        for name, sub_value in value.items():
            if name in props:
                _validate(sub_value, props[name], _join(path, name), root, out)
            elif schema.get("additionalProperties") is False:
                out.append(Violation(_join(path, name), "additionalProperties", "is not a known field (typo?)"))
    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            _validate(item, schema["items"], f"{path}[{index}]", root, out)


def validate(data: Any, schema: dict) -> list[Violation]:
    """Return every violation of ``schema`` by ``data`` (empty list = valid)."""
    check_schema(schema)
    out: list[Violation] = []
    _validate(data, schema, "", data, out)
    return out


def load_schema(path: Path) -> dict:
    schema = json.loads(Path(path).read_text(encoding="utf-8"))
    check_schema(schema)
    return schema


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate .sop/config.yml against .sop/schema.json.")
    parser.add_argument("--config", type=Path, default=REPO_ROOT / ".sop" / "config.yml")
    parser.add_argument("--schema", type=Path, default=REPO_ROOT / ".sop" / "schema.json")
    parser.add_argument(
        "--git-identity",
        action="store_true",
        help="after validating, set this repo's git author to the machine account (bot.*)",
    )
    args = parser.parse_args(argv)
    try:
        data = load_yaml_file(args.config)
    except ConfigSyntaxError as exc:
        print(f"{args.config}: {exc}", file=sys.stderr)
        return 1
    violations = validate(data, load_schema(args.schema))
    for v in violations:
        print(f"{args.config}: {v}", file=sys.stderr)
    if violations:
        print(f"{len(violations)} problem(s) found.", file=sys.stderr)
        return 1
    print(f"{args.config}: OK")
    if args.git_identity:
        return set_git_identity(data)
    return 0


# GitHub's noreply domain; the address is "<user id>+<login>@" + this.
NOREPLY_DOMAIN = "users.noreply.github.com"


def set_git_identity(data: dict) -> int:
    """Make the machine account the commit author in the current repository.

    Every session runs this before its first commit, so commit-author never
    sees a personal identity. Uses the noreply address, never a real email.
    """
    import subprocess

    login = data["bot"]["github"]
    email = f"{data['bot']['github_id']}+{login}" + "@" + NOREPLY_DOMAIN
    for key, value in (("user.name", login), ("user.email", email)):
        subprocess.run(["git", "config", "--local", key, value], check=True)
    print(f"git author set to: {login} <{email}>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
