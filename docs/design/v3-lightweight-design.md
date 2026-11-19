# sop-v2 輕量化重新設計 / Lightweight redesign (v3)

- 版本：草稿 0.2（2026-11-19）
- 狀態：**待 Owner 審閱**。V1（plugin 骨架）、V2（5 個核心 skill 與 F1–F9 修正）已完成並推送；本版依 Owner 在 scratchbook 中的 26 個決定（T1–T26）重寫其餘設計，並重排步驟
- 依據：研究頁面「Agent Harness 藍圖」與 [scratchbook](v3-scratchbook.md)（前沿公司的官方文章與 mattpocock/skills、pstack、gstack 的分析）；給使用者的分級建議見 [`docs/suggestion.md`](../suggestion.md)
- 前一版：[`sop-v2-design.md`](sop-v2-design.md)（v0.12，重量版，凍結在 `v2.0.0-rc.1`）

> **EN:** Draft 0.2, awaiting Owner review. V1 (plugin skeleton) and V2 (five core skills plus fixes F1–F9) are done and pushed. This version rewrites the rest of the design from the Owner's 26 scratchbook decisions (T1–T26) and re-plans the steps. Basis: the "Agent Harness blueprint" research (frontier-lab guidance plus mattpocock/skills, pstack and gstack). The per-level guidance for users is in [`docs/suggestion.md`](../suggestion.md). The heavyweight v2 design is frozen at `v2.0.0-rc.1`.

## 目錄 / Contents

1. [為什麼重做](#1-為什麼重做--why-redo-it)
2. [設計原則](#2-設計原則--principles)
3. [等級](#3-等級--levels)
4. [Repo 結構](#4-repo-結構--repo-layout)
5. [Skill 清單](#5-skill-清單--the-skills)
6. [每個專案的設定](#6-每個專案的設定--per-project-config)
7. [Ticket 格式](#7-ticket-格式--ticket-format)
8. [Level 1 預設檔案](#8-level-1-預設檔案--level-1-defaults)
9. [護欄食譜](#9-護欄食譜--guardrail-recipes)
10. [發佈與更新](#10-發佈與更新--distribution-and-updates)
11. [已定案的決策](#11-已定案的決策--decisions)
12. [失效情境與最壞影響](#12-失效情境與最壞影響--failure-modes)
13. [實作計畫](#13-實作計畫--implementation-plan)
14. [待決問題](#14-待決問題--open-questions)

## 1. 為什麼重做 / Why redo it

**第一次修正（草稿 0.1）。** S4 試用顯示，v2 在寫第一行產品程式之前，就要求回答 16 題沒有預設值的設定、通過 B1–B7 七項查證，還要理解 11 項 CI 檢查與範本同步。重量來自強制機制：v2 的 skill 不到 400 行，閘門、檢查與同步程式加測試超過 5,000 行。Owner 決定改走輕量、可組合的 skill 包。

**第二次修正（本版）。** 研究前沿公司的 harness 文章與三個公開實作後，發現草稿 0.1 矯枉過正：

- 它把**所有**保證都變成選配文件。但每個來源都同意，沒有例外的規則要用機制保證，不能只寫成文字。
- 它和 v2 都漏了 **session 層的機制**：hooks 與權限設定。這一層在 agent 動手的當下就擋，比 CI 便宜。
- 它沒有測 harness 本身、沒有跨 session 的交接，也沒有淘汰元件的規則。

本版用**等級**取代 v2 的「全部或沒有」與草稿 0.1 的「全部選配」。Level 1 是便宜、所有來源都同意的預設。

> **EN:** First revision (draft 0.1): v2 demanded 16 default-less answers, seven repo checks and an understanding of 11 CI checks before any product code, and its weight was enforcement, so the Owner chose a lightweight skill pack. Second revision (this one): the research showed draft 0.1 overcorrected. It made every guarantee optional, although all sources agree zero-exception rules need mechanisms. Like v2, it missed session-level enforcement (hooks and permissions), which acts the moment an agent acts and costs less than CI. It also had no harness evals, no cross-session hand-off and no way to retire components. This version uses levels instead, with a cheap, universally endorsed Level 1 as the default.

## 2. 設計原則 / Principles

| # | 原則 | 意思 |
| --- | --- | --- |
| R1 | **流程在 skill，保證在機制** | skill 教 agent 怎麼做；沒有例外的規則由 hook、權限或 CI 保證，不靠文字 |
| R2 | **每個 skill 都能單獨用** | 只用 `/verify` 或只用 `tdd` 都可以 |
| R3 | **兩種 skill** | 使用者呼叫（編排，`disable-model-invocation: true`）與模型呼叫（紀律）。編排型可以呼叫紀律型，編排型之間不互相呼叫 |
| R4 | **沒有閘門，但有預設** | 不擋整個 repo；`/setup` 預設裝好 Level 1，更高等級照食譜自己加 |
| R5 | **三種強制力，挑最便宜夠用的** | 文字（agent 自律）→ session 機制（hooks、權限，當下擋）→ merge 機制（CI、分支保護，合併時擋） |
| R6 | **每個元件都寫怎麼拿掉** | 每個元件都假設模型做不到某件事；模型進步後要能證明它不再需要，然後拿掉 |
| R7 | **短** | 每個 `SKILL.md` ≤ 80 行，細節放同目錄的參考檔 |
| R8 | **P1 不變，一個例外** | 範本不含個人資訊；例外是 Owner 刻意選的 plugin 名稱 `pitaya`（T25） |

P2（先完整才開工）已取消（D44）。

> **EN:** R1 process lives in skills, guarantees in mechanisms. R2 every skill stands alone. R3 two kinds of skill; orchestrators never call each other. R4 no gate, but `/setup` installs Level 1 by default. R5 three strengths of enforcement (prose, session mechanisms, merge mechanisms); pick the cheapest that suffices. R6 every component says how to retire it. R7 skills ≤ 80 lines. R8 P1 holds, with one deliberate exception: the plugin name `pitaya` (T25). P2 stays dropped (D44).

## 3. 等級 / Levels

同一套模板，四個等級（T1）。每一級包含前一級。哪一級該有哪些元件、為什麼，給使用者的完整說明在 [`docs/suggestion.md`](../suggestion.md)。

| 等級 | 適合 | 組成 | 怎麼得到 |
| --- | --- | --- | --- |
| **Level 0** | 試用、不想改 repo | 只有 skill | 安裝 plugin |
| **Level 1**（預設） | 一個人配一個或少數 agent | AGENTS.md 地圖、harness.md、一行測試指令、CI 必要檢查、`main` 保護、`.claude/settings.json` 權限、3 個 hook、全新驗證者、決策紀錄 | `/setup` 複製 `templates/` |
| **Level 2** | 多 agent 平行 | 機器帳號與 commit 作者檢查、範圍、唯讀路徑、不弱化測試（JUnit 比對）、完成條件、只增檔案、序列化資源、證據檢查 | 照食譜加 |
| **Level 3** | 長時間自主 | 進度檔與固定開場流程、第二模型審查、agent 合併的自主政策、專案自己的 evals | 照食譜加 |

> **EN:** One template, four levels (T1), each including the one before. Level 0: skills only, via the plugin. Level 1 (default, installed by `/setup`): AGENTS.md map, harness.md, one test command, CI as a required check, `main` protection, settings.json permissions, three hooks, a fresh verifier and a decision log. Level 2 (parallel agents, recipes): machine accounts and author checks, scope, read-only paths, no weakened tests via JUnit comparison, done-when, append-only files, serial resources, evidence checks. Level 3 (long-running autonomy, recipes): progress file and start-up routine, second-model review, an agent-merge autonomy policy, project evals. Full guidance for users: `docs/suggestion.md`.

## 4. Repo 結構 / Repo layout

```text
.claude-plugin/
  plugin.json            # plugin "pitaya"：明列每個 skill 的路徑
  marketplace.json
skills/<name>/           # SKILL.md + 同目錄參考檔（plugin 發佈）
templates/               # /setup 複製進專案的 Level 1 檔案（檔頭寫來源版本）
  AGENTS.md  CLAUDE.md  docs/agents/harness.md  docs/decisions.md
  .claude/settings.json  .claude/hooks/*.py  .github/workflows/tests.yml
docs/
  suggestion.md          # 給使用者：每個等級該有哪些元件、為什麼
  concepts/              # 角色、自主程度、證據、升級
  guardrails/            # Level 2–3 食譜 + files/<Gx>/ 可複製檔
  design/                # 設計文件
evals/                   # 測 harness 本身的任務集（手動跑）
tests/                   # skill 檢查、hook 測試、食譜檔的失敗案例、連結與個資掃描
CHANGELOG.md
```

範本 repo 不再是「Use this template」的來源。使用者安裝 plugin，再用 `/setup` 把 `templates/` 複製進自己的 repo；複製後的檔案歸專案所有（T4）。

> **EN:** Plugin manifests (plugin `pitaya`), skills, `templates/` holding the Level 1 files that `/setup` copies (each with a source-version header), user docs (`suggestion.md`, concepts, guardrail recipes with copyable files), design docs, `evals/`, tests and a changelog. The repo stops being a "Use this template" source: users install the plugin and run `/setup`, and the copied files then belong to the project (T4).

## 5. Skill 清單 / The skills

### 使用者呼叫（編排）/ User-invoked

| Skill | 做什麼 | 對應角色（T21） | 狀態 |
| --- | --- | --- | --- |
| `/setup` | 探索 repo、問幾題、選等級，複製 Level 1 檔案，寫 harness.md；重跑時比對檔頭版本，找出過時的檔案 | Owner | V2 完成；W1 擴充 |
| `/plan` | 把需求切成可驗證的垂直切片 ticket，標出依賴，Owner 確認後寫到 ticket 位置 | Chief | W3 |
| `/build <ticket>` | 先紅後綠實作一張 ticket，附證據開 PR | Builder | V2 完成 |
| `/verify <PR>` | 派全新 subagent 冷讀重跑，依檢查表判 PASS / FAIL | Verifier | V2 完成 |
| `/report` | 把一批合併的工作整理成給 Owner 的報告 | Chief | W3 |
| `/handoff` | 中斷時寫交接文件：目標、已完成、進行中、下一步、證據位置（T11） | 任何角色 | W3 |
| `/retro` | 把重複出現的錯誤整理成「規則 → 由誰保證」的提議，並檢查哪些元件可以拿掉；Owner 核准後才改（T18、T19） | Chief | W3 |

### 模型呼叫（紀律）/ Model-invoked

| Skill | 做什麼 | 狀態 |
| --- | --- | --- |
| `tdd` | 先紅後綠；新模組先寫空殼；不弱化測試 | V2 完成 |
| `evidence` | 什麼算證據；模型名稱從 session 設定取得 | V2 完成 |
| `ask-owner` | 規格不清、需要未授權的變更、修正輪用完時，開 issue：兩三個選項、各自後果、建議 | W3 |
| `learning`（選配） | Owner 先回答四個問題，再比較與記錄；只在使用者呼叫或 harness.md 開啟時用（T22） | W3 |

所有 skill 第一步讀 `docs/agents/harness.md`；檔案不存在時提示一次 `/setup`，然後用安全的預設值繼續。

> **EN:** User-invoked: `/setup` (explore, ask, choose a level, copy Level 1 files, write harness.md, detect stale copies on re-run), `/plan` (vertical-slice tickets with dependencies), `/build`, `/verify` (fresh subagent, checklist), `/report`, `/handoff` (hand-off notes when work stops, T11) and `/retro` (turn repeated mistakes into rule-to-enforcer proposals and review what can be retired; the Owner approves, T18–T19). Model-invoked: `tdd`, `evidence`, `ask-owner`, and an opt-in `learning` (T22). Roles map to skills: plan and report are the Chief, build the Builder, verify the Verifier (T21). Every skill reads `docs/agents/harness.md` first and falls back to safe defaults.

## 6. 每個專案的設定 / Per-project config

`docs/agents/harness.md` 是給 agent 讀的 Markdown，不做 schema 驗證。比草稿 0.1 多了幾個欄位：

| 欄位 | 預設 | 決策 |
| --- | --- | --- |
| 等級 | 1 | T1 |
| Owner、機器帳號 | 由 `/setup` 問；機器帳號可以是「無」 | — |
| 自主程度 | 只有 Owner 合併 `main`；可改成「CI 綠 + 驗證 PASS 後 agent 合併」 | T3 |
| Ticket 位置 | 有 GitHub remote 時用 Issues（標籤 `ticket`），否則 `docs/tickets/<id>.md` | T9 |
| 測試指令 | 一個真的跑得通的指令，照實記錄；Level 2 起必須輸出 JUnit XML | T5 |
| 文件語言 | 由 `/setup` 問 | — |
| 驗證方式 | 全新 subagent；可改成另開 session、指定模型 | T13 |
| 修正輪數 | 2 | T16 |
| 紀錄檔 | `docs/decisions.md` 預設建立，`docs/pitfalls.md` 預設不建 | T12 |
| 敏感領域 | 由 `/setup` 問 | — |
| 已啟用的護欄 | Level 1 的元件；照食譜加的會寫在這裡 | — |
| learning | 關閉 | T22 |

> **EN:** `docs/agents/harness.md` gains fields for the level (default 1, T1), autonomy (default: only the Owner merges `main`, T3), ticket location (Issues when there's a GitHub remote, T9), a test command recorded exactly as it runs (JUnit XML from Level 2, T5), verification mode (fresh subagent, T13), fix rounds (2, T16), record files (decisions on, pitfalls off, T12), enabled guardrails, and learning (off, T22), alongside Owner, machine account, language and sensitive areas.

## 7. Ticket 格式 / Ticket format

依等級擴充（T10）。加哪個護欄，才需要哪個欄位。

| 欄位 | 等級 | 用途 |
| --- | --- | --- |
| 目標、完成條件、依賴、範圍 | Level 1 | 完成條件每條對應一個測試或可重跑的指令 |
| 完成條件的測試 ID | Level 2 | 食譜「完成條件」用來比對 JUnit 結果 |
| 序列化資源 | Level 2 | 食譜「序列化資源」：同一資源一次一張 ticket |
| 只增檔案 | Level 2 | 食譜「只增檔案」 |
| 是否截圖 | Level 2 | 食譜「證據」：有畫面時一定要截圖 |

> **EN:** Level 1 tickets have four fields: goal, done-when conditions (each tied to a test or re-runnable command), dependencies and scope. Level 2 recipes add test IDs for done-when, serial resources, append-only files and whether screenshots are required, each only when its recipe is adopted (T10).

## 8. Level 1 預設檔案 / Level 1 defaults

`/setup` 從 `templates/` 複製；每個檔案開頭註明來源版本（T20）。

| 檔案 | 內容 | 決策 |
| --- | --- | --- |
| `AGENTS.md` | ≤ 100 行的地圖：指向 harness.md、測試指令、完成的定義、文件位置 | T2 |
| `CLAUDE.md` | 只有一行，用 Claude Code 的匯入語法引入 `AGENTS.md` | T2 |
| `.claude/settings.json` | deny：讀取 `.env*`、金鑰檔、雲端憑證目錄；allow：測試指令與常用唯讀 git 指令；其他維持詢問。不含沙箱 | T8 |
| `.claude/hooks/no_push_main.py` | PreToolUse：拒絕 `git push` 到預設分支與任何 force push | T6 |
| `.claude/hooks/no_destructive.py` | PreToolUse：拒絕刪除根目錄或家目錄、`git reset --hard`、`git clean -fdx` 等 | T6 |
| `.claude/hooks/ask_on_rule_files.py` | PreToolUse：編輯 AGENTS.md、CLAUDE.md、harness.md、`.claude/**`、`.github/workflows/**` 時改成詢問 | T6 |
| `.github/workflows/tests.yml` | 一個 job 跑 harness.md 的測試指令；`/setup` 說明怎麼設成 `main` 的必要檢查 | T7 |
| `docs/decisions.md` | 只增不改的決策紀錄 | T12 |

Hook 的共同規則：

- 只用 Python 標準函式庫，讀 stdin 的 JSON，exit code 2 表示擋下。
- 擋下時，訊息要寫出原因與怎麼做才對（例如「開 PR，由 Owner 合併」）。
- 每個 hook 都有正反兩面的測試。
- 每個 hook 的檔頭寫「什麼證據顯示可以拿掉它」（R6）。
- Hook 只在 Claude Code 生效。其他工具從 AGENTS.md 讀到同樣的文字規則；擋推送到 `main` 的部分，另有 ruleset 在合併時把關（T2）。

> **EN:** `/setup` copies these from `templates/`, each headed with its source version (T20): an AGENTS.md map of at most 100 lines, a CLAUDE.md that imports it, settings.json (deny secrets, allow the test command and read-only git, ask for the rest, no sandbox; T8), three PreToolUse hooks (no pushes to the default branch or force pushes; no destructive commands; ask before editing rule files; T6), a one-job tests workflow (T7) and an append-only decision log (T12). Hooks use only the standard library, read JSON on stdin, exit 2 to block, say why and what to do instead, have tests both ways, and state what evidence would justify removing them. They work only in Claude Code; other tools get the same rules as prose in AGENTS.md, and the ruleset still guards `main` at merge (T2).

## 9. 護欄食譜 / Guardrail recipes

### 9.1 每篇食譜的格式 / Recipe format

每篇 `docs/guardrails/<id>-<name>.md` 有八節。比草稿 0.1 多了第 6、8 節：

1. **防什麼**：沒有它時會發生的具體事故。
2. **什麼時候值得加**：訊號，例如「開始有第二個 agent 同時工作」。
3. **怎麼加**：步驟，加上 `docs/guardrails/files/<id>/` 的可複製檔。
4. **怎麼證明有效**：一個會讓它失敗的操作，以及預期看到的輸出。
5. **代價與誤擋**：多花多少時間，哪些正常情況會被擋，被擋時怎麼處理。
6. **錯誤訊息**：失敗時印什麼，必須告訴 agent 怎麼修。
7. **完成後**：在 harness.md 的「已啟用的護欄」記一筆；需要時更新 ticket 格式。
8. **何時拿掉**：什麼證據顯示它不再需要（T18）。

> **EN:** Each recipe has eight sections: what it guards against, when it's worth adding, how to add it (with copyable files), how to prove it works, cost and false positives, the error message (which must tell the agent how to fix the problem), what to record afterwards, and when to remove it (T18).

### 9.2 清單 / Catalogue

| 等級 | 食譜 | 來源（v2） |
| --- | --- | --- |
| 1 | 保護 `main`：ruleset、只有 Owner 能合併、設定必要檢查（給 `/setup` 引用的步驟） | `setup.md`、B3、B4 |
| 2 | 機器帳號：建立、Write 權限、token、commit 作者 | B1、B2、`--git-identity` |
| 2 | Commit 作者檢查 | `commit-author` |
| 2 | 範圍：PR 只改 ticket 列出的路徑 | `path-scope` |
| 2 | 唯讀路徑：規則、規格、CI 設定不能被 agent 的 PR 改動 | `readonly-paths` |
| 2 | 不弱化測試：base 通過的測試，PR 上也要存在且通過（JUnit 比對） | `no-weakened-tests`、`compare_junit.py` |
| 2 | 完成條件：每個完成條件對應的測試 ID 都存在且通過 | `done-when` |
| 2 | 只增檔案（例如 CHANGELOG） | `append-only` |
| 2 | 序列化資源（例如 migration、lockfile 一次一張 ticket） | `serial-resource` |
| 2 | 證據：PR 說明一定有證據一節；有畫面時要截圖 | `evidence` |
| 3 | 第二模型審查（T14） | `claude_review` 模組 |
| 3 | 進度檔與固定開場流程（T11） | 新增 |
| 3 | 自主合併：CI 綠 + 驗證 PASS 後由 agent 合併，以及它需要的前置條件（T3） | 新增 |
| 3 | 專案自己的 evals | 新增 |
| — | 文件檢查（連結、雙語段落） | `docs_lint` 模組 |

v2 的啟動閘門（`sop-ready`）與 `branch-ticket` 不再需要（T26）。

> **EN:** Level 1 has one recipe the `/setup` skill points to: protecting `main`. Level 2 turns v2's checks into recipes: machine account, commit author, scope, read-only paths, no weakened tests, done-when, append-only files, serial resources and evidence (T26). Level 3 adds second-model review (T14), the progress file and start-up routine (T11), autonomous merging and its prerequisites (T3), and project evals. A docs-lint recipe sits outside the levels. The bootstrap gate and `branch-ticket` are no longer needed.

### 9.3 可複製檔的原則 / Copyable files

- 只用 Python 標準函式庫與 `git`。
- 每個檢查一個獨立檔案，複製一個不需要其他檔案。
- 設定寫在檔頭的常數或 workflow 的 `env:`。
- 檔頭寫來源版本。
- 範本的 `tests/` 為每個檔案保留 v2 的「會讓它失敗」測試。

> **EN:** Standard library and git only; one standalone file per check; configuration via header constants or workflow `env:`; a source-version header; and the template's tests keep v2's failing cases for every file.

## 10. 發佈與更新 / Distribution and updates

| 部分 | 怎麼到使用者手上 | 怎麼更新 |
| --- | --- | --- |
| Skill | plugin `pitaya`（`/plugin marketplace add <owner>/sop-v2`，再 `/plugin install pitaya@<marketplace>`）；也可以直接複製 `skills/<name>/` | plugin 版本號改變時自動更新 |
| Level 1 檔案 | `/setup` 從 `templates/` 複製 | 重跑 `/setup`：比對檔頭版本，列出過時的檔案與差異，由使用者決定要不要更新 |
| 食譜檔 | 使用者照食譜複製 | CHANGELOG 標出食譜修正；檔頭版本可以比對 |

版本（T20）：

- plugin 用 semver，`plugin.json` 的 `version` 和 git tag 一致。
- `CHANGELOG.md` 分 skill、Level 1 檔案、食譜三類列出改動。
- 破壞性變更只放在 major 版本。

> **EN:** Skills ship as plugin `pitaya` (or by copying) and auto-update on version bumps. Level 1 files come from `/setup`; re-running it compares version headers and lists stale files and diffs for the user to decide. Recipe files are copied by the user and tracked via the changelog and headers. Semver matches the git tag, the changelog splits changes into skills, Level 1 files and recipes, and breaking changes come only in major versions (T20).

## 11. 已定案的決策 / Decisions

D44–D47（2026-11-19）仍然有效：走輕量方向；護欄用文件加可複製檔；用 plugin 發佈；v2 凍結在 `v2.0.0-rc.1`。本版依 scratchbook 加入 T1–T26，其中有兩項修正了它們：

- **T4 取代 D46 的「直接複製 skill」為主要途徑：** skill 用 plugin 發佈，`/setup` 負責複製 Level 1 檔案。直接複製 skill 仍然可以。
- **T6–T8 修正 D44 的「全部選配」：** Level 1 的 hooks、權限與 CI 預設安裝。

| # | 決定 |
| --- | --- |
| T1 | 分級：同一套模板 Level 0–3 |
| T2 | Claude Code 優先，AGENTS.md 為入口，skill 用開放標準；hooks 只在 Claude Code 生效 |
| T3 | 自主程度是設定，預設只有 Owner 合併 `main` |
| T4 | Plugin 發佈 skill，`/setup` 複製 Level 1 檔案 |
| T5 | Level 1 只要一個跑得通的測試指令；Level 2 才要求 JUnit |
| T6 | Level 1 hooks：擋推送到 `main` 與 force push、擋危險指令、改規則檔要詢問 |
| T7 | Level 1 CI：一個 job 跑測試指令，設為必要檢查 |
| T8 | Level 1 權限：deny 機密，allow 常用指令，不含沙箱 |
| T9 | Ticket 位置由 `/setup` 選，預設 Issues |
| T10 | Ticket 欄位：Level 1 四個，Level 2 擴充 |
| T11 | 進度靠 issue、PR、git log，加 `handoff` skill；Level 3 加進度檔 |
| T12 | `docs/decisions.md` 預設建立，`docs/pitfalls.md` 預設不建 |
| T13 | 驗證者預設全新 subagent，可改成另開 session |
| T14 | 第二模型審查是 Level 3 食譜 |
| T15 | 證據寫在 PR；只有截圖進 repo |
| T16 | 修正兩輪後升級，可設定 |
| T17 | `evals/` 任務集，手動跑，第一個任務取自 sop-trial #3 |
| T18 | 每篇食譜、每個 hook 與 skill 都寫何時拿掉 |
| T19 | `retro` skill 提議改進，Owner 核准 |
| T20 | semver + CHANGELOG + 檔頭版本 |
| T21 | 四個角色保留為概念，對應到 skill |
| T22 | `learning` 是選配 skill |
| T23 | repo 維持 sop-v2，plugin 另取名 |
| T24 | 繼續在 PR #12 分支上實作 |
| T25 | Plugin 名稱 `pitaya`；Owner 同意這是 P1 的例外，帳號、email 等仍然禁止 |
| T26 | v2 的 CI 檢查改寫成 Level 2 食譜；不再需要啟動閘門與 `branch-ticket` |

> **EN:** D44–D47 still hold. T1–T26 come from the scratchbook. T4 replaces copying skills as the main route with plugin plus `/setup`, and T6–T8 revise D44's "everything optional" by installing Level 1 hooks, permissions and CI by default. The table lists all 26 decisions; T25 records the Owner's deliberate P1 exception for the plugin name `pitaya`.

## 12. 失效情境與最壞影響 / Failure modes

| 情境 | 最壞影響 | 緩解 |
| --- | --- | --- |
| 只裝 plugin（Level 0），沒跑 `/setup` | agent 可以推送到 `main`、刪測試讓 CI 變綠 | 每個 skill 提示一次 `/setup`；`/verify` 的檢查表比對測試數量與範圍 |
| 用 Claude Code 以外的工具 | hooks 不生效 | AGENTS.md 有同樣的文字規則；ruleset 在合併時仍然擋 `main` |
| Hook 誤擋正常操作 | 開發中斷 | 訊息寫出原因與替代做法；規則檔用「詢問」而不是拒絕；hook 都有測試 |
| `/setup` 複製的檔案蓋掉專案的版本 | 專案的修改遺失 | 檔案已存在時一律列出差異請使用者決定，不直接覆寫 |
| 複製的檔案過時 | 已修正的 bug 留在專案裡 | 檔頭版本；重跑 `/setup` 會列出過時的檔案 |
| plugin 自動更新改變 skill 行為 | 進行中的工作流程改變 | semver；破壞性變更只在 major 版本並寫進 CHANGELOG |
| 自主程度改成 agent 合併 | 未經人看的程式進入 `main` | 食譜列出前置條件（Level 2 的檢查、第二模型審查）；預設仍是人類合併 |
| P1 例外被擴大解讀 | 範本開始出現其他個資 | 個資掃描照常執行；例外只限 T25 的 plugin 名稱 |

> **EN:** Skills without `/setup` (Level 0) can push to `main` or delete tests; skills point to `/setup` and `/verify` compares test counts and scope. Other tools don't run hooks, but AGENTS.md carries the same rules and the ruleset still guards `main`. Hooks that block wrongly explain the alternative, rule files only ask, and every hook is tested. `/setup` never overwrites an existing file without showing the diff. Stale copies are caught by version headers. Plugin updates follow semver. Agent merging lists its prerequisites and is never the default. The P1 exception covers only the plugin name, and the personal-data scan still runs.

## 13. 實作計畫 / Implementation plan

已完成：V0（設計）、V1（plugin 骨架、`check_skills.py`、self-ci）、V2（`setup`、`tdd`、`evidence`、`build`、`verify`，F1–F9 修正，sop-trial 試跑 PASS）。以下取代草稿 0.1 的 V3–V6。每一步在 PR #12 分支上做，完成後請 Owner 看過再進下一步。

| 步驟 | 內容 | 完成條件 |
| --- | --- | --- |
| W0 | 本設計文件與 `docs/suggestion.md` | Owner 核准 |
| W1 | plugin 改名 `pitaya`；harness 範本加入 §6 的新欄位；README 更新 | `check_skills.py` 與全部測試通過；`claude plugin validate .` 通過 |
| W2 | `templates/` 的 Level 1 檔案：AGENTS.md、CLAUDE.md、settings.json、3 個 hook、tests.yml、decisions.md；`/setup` 依等級複製並比對檔頭版本 | 每個 hook 有擋下與放行的測試；`/setup` 在空 repo 與已有檔案的 repo 各試一次 |
| W3 | 其餘 skill：`plan`、`report`、`handoff`、`retro`、`ask-owner`、`learning`；`docs/concepts/` | 全部 ≤ 80 行；試用 repo 跑一次 `/plan` 與 `/handoff` |
| W4 | Level 2 食譜與可複製檔；保護 `main` 的 Level 1 食譜；每篇八節齊全 | 每個可複製檔都有會失敗的測試；錯誤訊息測試會檢查有寫修法 |
| W5 | Level 3 食譜；`evals/`（第一個任務取自 sop-trial #3）；`CHANGELOG.md`；刪除 v2 檔案（`.sop/`、`scripts/sop/`、`docs/sop/`、`.claude/skills/` 的 v2 skill、與閘門相關的測試）；個資掃描搬到 `tests/` | self-ci 只跑 v3 的測試且全綠 |
| W6 | 試用 repo：用 `/setup` 升到 Level 1，再加一個 Level 2 食譜，證明它會擋 | 有證據的試跑紀錄 |
| W7 | 發佈 `v3.0.0` | Owner 建立 release |

> **EN:** V0–V2 are done. Steps W0–W7 replace draft 0.1's V3–V6, each reviewed by the Owner before the next:
> - **W0:** this doc plus `suggestion.md`.
> - **W1:** rename the plugin to `pitaya`, add the new harness fields, update the README.
> - **W2:** the Level 1 templates (map, import, settings, three hooks with tests, workflow, decision log), with `/setup` copying them and comparing version headers.
> - **W3:** the remaining skills and the concept docs.
> - **W4:** Level 2 recipes and copyable files, with failing-case tests and checks that error messages give a fix.
> - **W5:** Level 3 recipes, `evals/`, the changelog, removal of v2 files, and the personal-data scan moved to `tests/`.
> - **W6:** move the trial repo to Level 1 and prove one Level 2 recipe blocks.
> - **W7:** the Owner releases `v3.0.0`.

## 14. 待決問題 / Open questions

| # | 問題 | 建議 |
| --- | --- | --- |
| O4 | 範本 repo 自己的 commit 是否改用機器帳號 | 仍等 Owner 決定 |
| O5 | 暫存中的 V3 測試改動（預期 4 個 skill）怎麼處理 | 捨棄；W3 依新清單重寫測試 |
| O6 | `/setup` 要不要自動幫使用者設定 ruleset | 不要：機器帳號沒有管理權限；`/setup` 只產生步驟與檢查方式（「保護 `main`」食譜） |

> **EN:** O4 (the template repo's own commit identity) is still open. O5: drop the stashed V3 test change and rewrite the test in W3 for the new skill list (recommended). O6: `/setup` shouldn't configure rulesets itself, since the machine account isn't an admin; it explains the steps and how to check them (recommended).
