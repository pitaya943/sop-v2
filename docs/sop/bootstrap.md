# 啟動閘門 / Bootstrap gate

用「Use this template」建立的專案，在開始任何開發之前，必須先填完並查證所有設定（P2：先完整，才開工）。本檔說明閘門怎麼運作、怎麼打開。

> **EN:** A project created with "Use this template" must fill in and verify every setting before any development starts (P2: complete before start). This file explains how the gate works and how it opens.

## 1. 三層閘門 / Three layers

| 層 | 機制 | 防的情況 | 擋不到的情況 |
| --- | --- | --- | --- |
| **L1 啟動流程** | `bootstrap-project` skill 逐題詢問，依 `.sop/schema.json` 驗證格式，並向 GitHub 即時查證事實 | 漏填、格式錯、帳號不存在、權限錯誤、ruleset 沒設 | 使用者不跑啟動流程，直接手改設定 |
| **L2 repo 層** | CI `sop-ready`，對所有目標為 `main` 或 `milestone/*` 的 PR 執行 | 手改後不符合 schema、`ready` 未核准、僅範本檔案沒刪 | agent 不開 PR、直接在本機開工 |
| **L3 agent 層** | 每個 skill 的第一步都是讀 `.sop/bootstrap.yml`，`ready` 不是 `true` 就停止 | agent 在閘門通過前就開始規劃或實作 | 有人刻意繞過 skill（此時 L2 仍會擋住合併） |

> **EN:** L1, the bootstrap skill, asks, validates against the schema and live-checks facts with GitHub. L2, CI `sop-ready`, runs on every PR into `main` or `milestone/*`. L3: every skill first reads `.sop/bootstrap.yml` and stops if `ready` isn't `true`. Each layer covers a gap in the others.

## 2. 設定欄位 / Config fields

所有值放在 `.sop/config.yml`，規則在 `.sop/schema.json`。範本中每個欄位都是 `null`，**沒有預設值**：啟動流程可以說明與建議，但必須由使用者明確回答。

| 欄位 | 用途 |
| --- | --- |
| `project.name`、`project.goal` | 文件標題；`AGENTS.md` 的專案段落 |
| `owner.display_name`、`owner.github` | 文件中如何稱呼 Owner；計畫 issue 與 milestone PR 的指派對象 |
| `bot.github`、`bot.github_id` | 機器帳號；`commit-author` 與身分查證。不可等於 `owner.github` |
| `doc_language` | 專案產出（PR、issue、報告）的語言 |
| `max_parallel` | 同時進行的 ticket 上限（1–5；經驗值 2–3） |
| `spec_paths` | 額外的唯讀路徑（規格） |
| `serial_resources` | 序列化資源的名稱 |
| `append_only_files` | 共用的只增檔案 |
| `sensitive_areas` | 沒有測試涵蓋就必須升級的領域 |
| `modules.learning`、`modules.claude_review`、`modules.docs_lint` | 可選模組的開關 |
| `template.source` | `sop-sync` 的來源（`owner/repo`） |
| `overrides.disabled_guards` | 停用的範本檢查（見 [`ci-contract.md`](ci-contract.md#5-停用檢查--disabling-a-check)） |

清單欄位可以是空清單 `[]`，但不可為 `null`。檢查格式：

```bash
python3 scripts/sop/config.py
```

> **EN:** Every value lives in `.sop/config.yml`, validated by `.sop/schema.json`. Every field starts as `null` with no default: bootstrap may explain and suggest, but the user must answer. Lists may be `[]`, never `null`. Run `python3 scripts/sop/config.py` to check the format.

## 3. 啟動流程的互動原則 / How bootstrap asks

- 一次問一題，附上說明、為什麼需要、建議值（如果有），但**不得替使用者填入**。
- 每個答案立刻驗證；不通過時說明原因，並指出去哪個設定頁修正，再重問。
- 使用者說「不知道」時，解釋選項與後果，請使用者決定；仍無法決定就停在該題，不跳過。
- 全部答完後，列出完整設定讓使用者確認，再寫入檔案。

> **EN:** One question at a time, with an explanation and any suggestion, but never filling in an answer. Validate each answer immediately and point to the fix on failure. On "I don't know", explain the options and stop there rather than skip. Confirm the full config before writing it.

## 4. Repo 設定的查證（B1–B7）/ Repo checks (B1–B7)

這些是 GitHub repo 的設定，不是檔案；每一項怎麼設定見 [`setup.md`](setup.md)。結果寫進 `.sop/bootstrap.yml`，每項附證據（API 回應或指令輸出）。狀態只有 `pending`、`passed`、`failed`、`not_applicable`。

| # | 檢查 | 驗證方式 |
| --- | --- | --- |
| B1 | 目前 session 的 GitHub 身分等於 `bot.github` | 查詢目前登入的使用者 |
| B2 | 機器帳號是 collaborator，權限是 Write（不是 Admin） | repo collaborator API |
| B3 | `main` 有 ruleset：機器帳號無法直接更新 | branch rules API；無法讀取時由 Owner 提供設定畫面截圖 |
| B4 | `main` 的 ruleset 把 CI 的必要檢查設為必須通過（`milestone/*` 不設必要檢查，Chief 直接推送紀錄） | 同上 |
| B5 | `scripts/sop/test` 已實作，能產生 JUnit XML | 實際執行 |
| B6 | （`modules.claude_review` 開啟時）repo secret `ANTHROPIC_API_KEY` 已設定；關閉時為 `not_applicable` | secret 名稱清單 API（不讀值）；機器帳號讀不到時由 Owner 提供截圖 |
| B7 | 僅範本檔案（`.sop/template-only.txt`）已移除；關閉的模組已移除 | 檔案清單比對 |

> **EN:** (How to set each one up: `setup.md`.) B1–B7 check GitHub settings and the working tree, each recorded in `.sop/bootstrap.yml` with evidence and a status of pending, passed, failed or not_applicable.

## 5. 閘門如何打開 / How the gate opens

1. `bootstrap-project` 在 `sop/bootstrap` 分支寫入設定、查證結果，刪除僅範本檔案與關閉的模組，填寫 `AGENTS.md` 的專案段落。
2. 全部通過時把 `ready` 設為 `true`，並開 PR 到 `main`。`ready: true` 時，B1–B7 每項都必須是 `passed`（附證據）或 `not_applicable`，否則 `sop-ready` 失敗。
3. 只有 Owner 能合併 `main`（B3），所以**閘門最後一定經過 Owner 核准**。agent 自己無法把閘門打開。
4. 合併後，`sop-ready` 在 `main` 上為綠，`plan-milestone` 才能開始第一個 milestone。

之後若有人把設定改壞（例如手改 `.sop/config.yml`），`sop-ready` 會在下一個 PR 失敗，閘門自動關上。

> **EN:** Bootstrap writes config and check results on `sop/bootstrap`, removes template-only files and disabled modules, fills the project section of `AGENTS.md`, sets `ready: true` only when every check passed or is not applicable, and opens a PR to `main`. Only the Owner can merge it, so an agent can never open the gate alone. If the config is later broken, `sop-ready` fails on the next PR and the gate closes again.

## 6. 怎麼執行 / How to run it

有 Claude Code 時，開一個 session 使用 `bootstrap-project` skill，它會帶你走完全部步驟。不使用 Claude 時，直接用同一支腳本：

```bash
scripts/sop/bootstrap ask
```

```bash
scripts/sop/bootstrap apply
```

接著實作 `scripts/sop/test`（[`ci-contract.md`](ci-contract.md#4-測試介面--the-test-interface)），再查證並完成：

```bash
GITHUB_TOKEN=<機器帳號的 token> scripts/sop/bootstrap check
```

```bash
scripts/sop/bootstrap finalize
```

`check` 讀不到的項目（例如 ruleset）用 `scripts/sop/bootstrap record B3 --status passed --evidence "<截圖路徑>"` 記錄。腳本不會推送或開 PR；完成後自己在 `sop/bootstrap` 分支 commit、推送，並開 PR 到 `main`。

> **EN:** With Claude Code, use the `bootstrap-project` skill. Without it, run the same script: `ask`, `apply`, implement `scripts/sop/test`, `check` (with the machine account's token), record anything it can't read with `record`, then `finalize`. The script never pushes or opens PRs; commit on `sop/bootstrap`, push, and open a PR to `main` yourself.

## 7. 檢查目前的狀態 / Checking the gate

```bash
python3 scripts/sop/guards.py sop-ready
```

輸出會列出每一個未完成的項目，以及目前停用的檢查。

> **EN:** `python3 scripts/sop/guards.py sop-ready` lists every unfinished item and the currently disabled guards.
