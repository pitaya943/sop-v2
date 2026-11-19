# sop-v2

一組小而可組合的 skill，讓 agent 在人類審查下開發：規劃成 ticket、先紅後綠地實作、用全新的 session 冷讀驗證、整理成報告。防護（CI gate、分支保護、範圍檢查）不是強制的閘門，而是**護欄食譜**：每一篇說明防什麼、什麼時候值得加、怎麼加、怎麼證明有效，需要時自己加上。

A set of small, composable skills for developing with agents under human review: plan work into tickets, build red-then-green, verify cold in a fresh session, and report. Protections (CI gates, branch protection, scope checks) aren't a mandatory gate. They're **guardrail recipes**, each explaining what it guards against, when it's worth adding, how to add it and how to prove it works, so you add them when you need them.

> **狀態 / Status：v3 開發中。** 已有 5 個核心 skill（`setup`、`build`、`verify`、`tdd`、`evidence`）；進度見 [設計文件第 13 節](docs/design/v3-lightweight-design.md#13-實作計畫--implementation-plan)。各等級建議具備哪些元件、各能達成什麼，見 [`docs/suggestion.md`](docs/suggestion.md)。舊的重量版（啟動閘門、11 項 CI 檢查、範本同步）凍結在 release `v2.0.0-rc.1`，設計見 [`sop-v2-design.md`](docs/design/sop-v2-design.md)。
>
> **v3 in development.** Five core skills exist (`setup`, `build`, `verify`, `tdd`, `evidence`). Which components each level should have, and what each achieves: [`docs/suggestion.md`](docs/suggestion.md). Progress: [design doc section 13](docs/design/v3-lightweight-design.md#13-實作計畫--implementation-plan). The previous heavyweight version (bootstrap gate, 11 CI checks, template sync) is frozen at release `v2.0.0-rc.1`; its design is in [`sop-v2-design.md`](docs/design/sop-v2-design.md).

## 安裝 / Install

Plugin 的名稱是 `pitaya`，安裝後 skill 顯示為 `/pitaya:setup`、`/pitaya:build` 等。兩種方式，擇一即可。

The plugin is named `pitaya`; once installed, skills appear as `/pitaya:setup`, `/pitaya:build` and so on. Pick one route.

**1. Plugin（自動更新）/ As a plugin (auto-updates)：** 在 Claude Code 中，把本 repo 加為 marketplace 再安裝。`<owner>` 換成本 repo 在 GitHub 上的擁有者。

In Claude Code, add this repo as a marketplace, then install. Replace `<owner>` with this repo's owner on GitHub.

```text
/plugin marketplace add <owner>/sop-v2
```

```text
/plugin install pitaya@sop-v2
```

**2. 複製（可自行修改）/ By copying (yours to edit)：** 把需要的 `skills/<name>/` 目錄複製到你專案的 `.claude/skills/`。之後的更新要自己比對。

Copy the `skills/<name>/` directories you want into your project's `.claude/skills/`. You pick up later changes yourself.

## Skill 一覽 / Skills

規劃中，從步驟 V2 開始陸續加入（[設計文件第 5 節](docs/design/v3-lightweight-design.md#5-skill-清單--the-skills)）。

Planned, arriving from step V2 ([design doc section 5](docs/design/v3-lightweight-design.md#5-skill-清單--the-skills)).

| Skill | 誰呼叫 / Invoked by | 做什麼 / What it does |
| --- | --- | --- |
| `/setup` | 使用者 / you | 問幾題，寫下專案設定，推薦第一個護欄 / Ask a few questions, write the project config, recommend a first guardrail |
| `/plan` | 使用者 / you | 把需求切成可驗證的 ticket / Split work into verifiable tickets |
| `/build` | 使用者 / you | 先紅後綠實作一張 ticket，附證據開 PR / Build one ticket red-then-green and open a PR with evidence |
| `/verify` | 使用者 / you | 全新 subagent 冷讀重跑，判 PASS / FAIL / A fresh subagent re-runs cold and judges PASS / FAIL |
| `/report` | 使用者 / you | 把合併的工作整理成報告 / Summarize merged work for the Owner |
| `tdd`、`evidence`、`ask-owner` | agent 自動 / the agent | 先紅後綠、證據規則、升級給 Owner / Red-green, evidence rules, escalating to the Owner |

## 護欄 / Guardrails

食譜從步驟 V4 開始放在 `docs/guardrails/`，建議從「CI 跑測試」和「保護 `main`」開始。

Recipes arrive in `docs/guardrails/` from step V4. Start with "CI runs the tests" and "protect `main`".

## 開發本 repo / Developing this repo

```bash
python3 scripts/check_skills.py
```

```bash
python3 -m pytest tests -q
```

第一個檢查 plugin 清單與每個 `SKILL.md`（frontmatter、名稱、最多 80 行）；第二個跑全部測試，不需要網路。

The first checks the plugin manifests and every `SKILL.md` (frontmatter, names, at most 80 lines); the second runs every test, with no network access needed.

## 授權 / License

[MIT No Attribution](LICENSE)
