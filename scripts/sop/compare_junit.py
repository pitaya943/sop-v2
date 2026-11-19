#!/usr/bin/env python3
"""Checks that read the project's test results (JUnit XML). Standard library only.

The project implements ``scripts/sop/test``, which writes ``build/sop/junit.xml``
(docs/sop/ci-contract.md, section 4). Every major test runner can emit JUnit
XML, so these checks stay independent of the stack.

* ``tests``: the report exists, parses, has at least one test, and nothing failed.
* ``no-weakened-tests``: every test ID that passes on the target branch is
  collected and passes on the PR. Judged by results, not by syntax, so it
  doesn't depend on any one test framework (following the reference harness).
  A missing report on either side is a failure.
* ``done-when``: every ``done_when`` ID of the ticket (or, for a milestone PR,
  of every ticket in that milestone) exists and passes.

A test ID is ``classname + "::" + name``.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

# When the same ID appears more than once (retries, parametrized duplicates),
# the worst outcome wins.
_RANK = {"passed": 0, "skipped": 1, "failed": 2}
MAX_LISTED = 30


def load_results(path: str | Path) -> dict[str, str] | None:
    """Parse JUnit XML into {test ID: passed | failed | skipped}.

    Returns None when the file is missing or unreadable: "no report" is
    itself a failure for the callers, never silently treated as empty.
    """
    if not path:
        return None
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError):
        return None
    results: dict[str, str] = {}
    for case in root.iter("testcase"):
        name = case.get("name")
        if not name:
            continue
        classname = case.get("classname") or ""
        test_id = f"{classname}::{name}" if classname else name
        if case.find("failure") is not None or case.find("error") is not None:
            outcome = "failed"
        elif case.find("skipped") is not None:
            outcome = "skipped"
        else:
            outcome = "passed"
        old = results.get(test_id)
        if old is None or _RANK[outcome] > _RANK[old]:
            results[test_id] = outcome
    return results


def check_tests(path: str | Path) -> list[str]:
    results = load_results(path)
    if results is None:
        return [f"no readable JUnit report at {path}; scripts/sop/test must write build/sop/junit.xml"]
    if not results:
        return [f"{path} contains no test cases"]
    failed = sorted(t for t, o in results.items() if o == "failed")
    return _cap([f"{t} failed" for t in failed], "tests failed")


def compare_results(base: dict | None, head: dict | None) -> list[str]:
    """Every ID that passes on the target branch must be collected and pass on the PR."""
    bad = []
    if base is None:
        bad.append("no test report for the target branch, so nothing to compare (a missing report fails)")
    if head is None:
        bad.append("no test report for the PR (the run may have stopped early); a missing report fails")
    if bad:
        return bad
    for test_id in sorted(t for t, o in base.items() if o == "passed"):
        if test_id not in head:
            bad.append(f"{test_id} passes on the target branch but is not collected on the PR")
        elif head[test_id] != "passed":
            bad.append(f"{test_id} passes on the target branch but is {head[test_id]} on the PR")
    return _cap(bad, "tests pass on the target branch but not on the PR")


def check_done_when(ctx, results: dict | None) -> list[str]:
    import guards

    tc = guards.ticket_context(ctx)
    if tc is not None:
        wanted = [(tc[0], t) for t in tc[1]["done_when"]]
    elif ctx.base_ref == "main" and re.fullmatch(r"milestone/M\d+", ctx.head_ref):
        milestone = ctx.head_ref.split("/", 1)[1]
        wanted = []
        for path in guards.tree_files(ctx, ctx.head, "docs/tickets"):
            if not re.fullmatch(r"docs/tickets/T-\d+\.md", path):
                continue
            meta = guards.parse_ticket(guards.show(ctx, ctx.head, path) or "")
            if meta.get("milestone") == milestone:
                tid = path.rsplit("/", 1)[1][:-3]
                wanted += [(tid, t) for t in meta["done_when"]]
    else:
        return []
    if results is None:
        return ["no JUnit report, so done_when can't be checked (a missing report fails)"]
    bad = []
    for tid, test_id in wanted:
        if test_id not in results:
            bad.append(f"{tid}: done_when test {test_id} was not run")
        elif results[test_id] != "passed":
            bad.append(f"{tid}: done_when test {test_id} is {results[test_id]}")
    return bad


def _cap(problems: list[str], summary: str) -> list[str]:
    if len(problems) > MAX_LISTED:
        return problems[:MAX_LISTED] + [f"... {len(problems)} in total: {summary}"]
    return problems
