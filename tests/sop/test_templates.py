"""S1c templates: the formats S2's guards will parse and the skills rely on (D24, D25)."""

from __future__ import annotations

import re
from html.parser import HTMLParser

import config
from conftest import REPO_ROOT

FRONT_MATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
TICKET_KEYS = ["id", "title", "milestone", "depends_on", "screens", "allowed_paths",
               "append_only", "serial", "done_when", "status"]


def front_matter(path):
    match = FRONT_MATTER_RE.match(path.read_text())
    assert match, f"{path} has no front matter"
    return config.parse_yaml(match.group(1))


def test_ticket_template_fields():
    meta = front_matter(REPO_ROOT / "docs" / "tickets" / "_template.md")
    assert list(meta) == TICKET_KEYS
    assert isinstance(meta["screens"], bool)  # D25: required, true/false
    for key in ("depends_on", "allowed_paths", "append_only", "serial", "done_when"):
        assert isinstance(meta[key], list), key
    assert all("::" in test_id for test_id in meta["done_when"])
    assert meta["status"] == "todo"


def test_ticket_template_sections():
    text = (REPO_ROOT / "docs" / "tickets" / "_template.md").read_text()
    for heading in ("## 目標", "## 要讀的檔案", "## 完成條件", "## 不在範圍內"):
        assert heading in text


def test_workflow_ticket_example_uses_the_template_fields():
    text = (REPO_ROOT / "docs" / "sop" / "workflow.md").read_text()
    block = re.search(r"```yaml\n---\n(.*?)\n---\n```", text, re.DOTALL).group(1)
    assert list(config.parse_yaml(block)) == TICKET_KEYS


def table_header(path):
    return next(line for line in path.read_text().splitlines() if line.startswith("| "))


def test_board_table_columns():
    """D24: S2's board parser reads exactly these columns."""
    assert table_header(REPO_ROOT / "docs" / "board.md") == \
        "| Ticket | Milestone | 標題 | 狀態 | PR | 修正輪數 | 備註 |"


def test_decision_log_columns():
    assert table_header(REPO_ROOT / "docs" / "decisions.md") == "| # | 問題 | 決定 | 理由 | 日期 | 備註 |"


def test_pitfalls_columns():
    assert table_header(REPO_ROOT / "docs" / "pitfalls.md") == "| # | 情況 | 該怎麼做 | 來源（PR） | 加入於 |"


def test_issue_templates_carry_their_labels():
    root = REPO_ROOT / ".github" / "ISSUE_TEMPLATE"
    assert front_matter(root / "needs-owner.md")["labels"] == "needs-owner"
    assert front_matter(root / "plan-approval.md")["labels"] == "plan-approval"
    assert "## 選項" in (root / "needs-owner.md").read_text()
    assert "## 模型" in (root / "plan-approval.md").read_text()


def test_pr_template_sections():
    text = (REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md").read_text()
    for heading in ("## 完成了什麼", "## 如何驗證", "## 證據", "## 比規格更嚴格的斷言",
                    "## Milestone 報告", "## 未解問題與提議"):
        assert heading in text


class _Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.h2 = [], []
        self._in_h2 = False

    def handle_starttag(self, tag, attrs):
        if tag not in ("meta", "br", "img", "link"):
            self.stack.append(tag)
        self._in_h2 = tag == "h2"

    def handle_endtag(self, tag):
        assert self.stack and self.stack[-1] == tag, f"unbalanced </{tag}>"
        self.stack.pop()
        self._in_h2 = False

    def handle_data(self, data):
        if self._in_h2:
            self.h2.append(data.strip())


def test_report_template_structure():
    parser = _Collector()
    parser.feed((REPO_ROOT / "docs" / "milestones" / "report-template.html").read_text())
    assert parser.stack == [], "unclosed tags"
    assert [h.split(".")[0] for h in parser.h2] == [str(i) for i in range(1, 11)]
    assert any("Agent 自行做的判斷" in h for h in parser.h2)  # mandatory section
