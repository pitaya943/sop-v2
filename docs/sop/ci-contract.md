# CI 契約 / CI contract

角色之間的契約由 CI 判定，不靠 agent 自律。每一項檢查都要有一個「會讓它失敗」的測試案例，證明檢查真的有效。

> **EN:** Contracts between roles are judged by CI, not by agents' good behaviour. Every check has a test case that makes it fail.

## 1. 原則 / Principles

- **防護目標：** 這些檢查防的是 agent 的疏忽與常見的偷懶寫法，不是刻意的攻擊。刻意的繞過由 Verifier 審查 diff、Owner 審查 milestone 擋下。檢查以允許清單、禁止整類寫法、比對結果的方式設計，不靠列舉禁止的語法。
- **來源分支（fail-closed）：** 目標是 `milestone/*` 的 PR，來源分支必須是 `ticket/T-xxx`，而且目標分支上要有對應的 `docs/tickets/T-xxx.md`，否則下列每一項都判為失敗。
- **兩層：** 中立層只需要 git、`.sop/` 設定與 GitHub API，與技術棧無關；介面層透過專案實作的 `scripts/sop/test` 取得結果。
- **檢查跑的是 PR 上的程式碼：** 依防護目標，這是可以接受的；但範本擁有的路徑（`.sop/managed.txt`，包含 `scripts/sop/` 與 workflow）都是唯讀路徑，PR 改動它們會被 `readonly-paths` 擋下。Ticket 與設定一律從目標分支讀取，PR 無法放寬自己的範圍或停用自己的檢查。
- **在哪裡必須通過：** 必要的檢查只設在 `main`（啟動時查證 B4；設定步驟見 [`setup.md`](setup.md#7-必要檢查--required-status-checks)）。CI 在每個 PR、以及推送到 `milestone/**` 與 `main` 時執行；Ticket PR 合併進 milestone 前由 Chief 確認全綠。

> **EN:** Checks guard against agent carelessness and common shortcuts, not deliberate attacks (the Verifier and the Owner catch those); they use allowlists, ban whole classes of constructs, and compare results. PRs into `milestone/*` must come from `ticket/T-xxx` with a matching ticket file, or every check fails. Stack-neutral checks need only git, `.sop/` and the GitHub API; interface checks go through `scripts/sop/test`. Checks run the PR's own code, which is acceptable under this goal, but template-managed paths (`scripts/sop/`, the workflows) are read-only, and tickets and config always come from the target branch, so a PR can neither widen its scope nor disable its own checks. Required checks are set only on `main` (B4; see `setup.md`); CI runs on every PR and on pushes to milestone branches and `main`, and the Chief confirms green before merging a ticket PR.

## 2. 檢查清單 / The checks

| 檢查 | 層 | 內容 | 失敗時 |
| --- | --- | --- | --- |
| `sop-ready` | 中立 | 啟動閘門：設定符合 schema、`ready` 為 true 且 B1–B7 都已完成、僅範本檔案已移除、停用的檢查有決策紀錄；一律列出目前停用的檢查 | 任一條不符 |
| `branch-ticket` | 中立 | 目標是 `milestone/*` 的 PR，來源分支是 `ticket/T-xxx`，且目標分支上有對應的 ticket 檔 | 不符時其他檢查也一律失敗 |
| `readonly-paths` | 中立 | 目標是 `milestone/*` 的 PR 不得修改唯讀路徑（第 3 節）；例外是 ticket 的 `allowed_paths` 明確列出（不含萬用字元）的路徑 | 有任何一個被修改 |
| `path-scope` | 中立 | 從分支名稱找到 ticket 檔，PR 修改的每個檔案都要符合它的 `allowed_paths` | 有範圍外的檔案 |
| `append-only` | 中立 | ticket 的 `append_only` 檔案，diff 只有新增行；檔案必須在 `append_only_files` 內 | 有刪除或修改的行 |
| `serial-resource` | 中立 | ticket 的 `serial` 都在 `serial_resources` 內，且看板上沒有另一張進行中的 ticket 宣告同一項 | 有未知或衝突的資源 |
| `evidence` | 中立 | PR 說明的「證據」一節至少有一個 code block（CLI 輸出）或一個指向 `docs/evidence/<ticket 編號>/` 的連結；ticket 為 `screens: true` 時，該目錄至少有一張截圖；ticket 沒有 `screens` 欄位時判為失敗 | 缺少證據 |
| `commit-author` | 中立 | PR 中每個 commit 的作者帳號（GitHub API 的 `author.login`）都是 `bot.github`，包含 GitHub 產生的 merge commit；不比對 email | 有其他作者，或作者無法對應到帳號 |
| `tests` | 介面 | 執行 `scripts/sop/test`，必須產生 `build/sop/junit.xml` | 任何一個失敗，或沒有產生結果 |
| `no-weakened-tests` | 介面 | 以結果判斷：目標分支上通過的每個測試 ID，在 PR 上都必須被收集而且通過；沒有產生結果報告就判為失敗。測試改名會被判為原測試消失而失敗，CI 不提供例外 | 任一條不符 |
| `done-when` | 介面 | ticket 的 `done_when` 每一項都在 PR 的 JUnit 結果中存在且通過 | 有缺漏或沒被執行 |

**Milestone PR**（`milestone/Mx → main`）另外檢查：該 milestone 每張 ticket 的 `done_when` 都在 JUnit 結果中存在且通過。

專案自己的檢查（例如 lint、資料庫 migration 的範圍、使用者可見字串）放在 `.github/workflows/project-*.yml`（客製化層 C3）。

> **EN:** Stack-neutral: `sop-ready`, `branch-ticket` (fail-closed for every check), `readonly-paths`, `path-scope`, `append-only`, `serial-resource`, `evidence` (always required; screenshots when `screens: true`; a missing `screens` field fails), `commit-author` (GitHub `author.login`, merge commits included, emails not compared). Interface: `tests`, `no-weakened-tests` (result comparison; renames count as disappearance), `done-when`. Milestone PRs also check every ticket's `done_when`. Project-specific checks go under `.github/workflows/project-*.yml` (layer C3).

## 3. 唯讀路徑 / Read-only paths

目標是 `milestone/*` 的 PR 不得修改：

- `AGENTS.md`、`CLAUDE.md`
- `.sop/**`、`docs/sop/**`、`.claude/**`、`.github/**`
- `docs/board.md`、`docs/decisions.md`
- `spec_paths` 列出的規格路徑
- `.sop/managed.txt` 列出的範本路徑（例如 `scripts/sop/` 的檢查程式）

例外：

- ticket 的 `allowed_paths` **明確列出**（不含萬用字元）的路徑，由 Owner 在計畫核准時同意。
- 啟動 PR（`sop/bootstrap` 分支）與 `sop-sync` PR（`sop/sync-*` 分支）的目標是 `main`，由 `path-scope` 限制：啟動 PR 不能修改範本擁有的路徑，只能刪除關閉的模組的檔案；sync PR 只能改範本擁有的路徑、`AGENTS.md` 與 `.sop/config.yml`。

Chief 的紀錄直接推送到 `milestone/Mx`，不經過 PR，所以不受這項檢查限制；Chief 只改紀錄檔，由流程與 Owner 的 milestone 審查保證。

範本擁有的路徑（`.sop/managed.txt`）在專案中是唯讀的，所以 `sop-sync` 覆寫時不會蓋掉專案的修改。

> **EN:** PRs into `milestone/*` may not touch `AGENTS.md`, `CLAUDE.md`, `.sop/**`, `docs/sop/**`, `.claude/**`, `.github/**`, the board, the decision log, `spec_paths` or template-managed paths, except paths a ticket's `allowed_paths` lists exactly (approved by the Owner in the plan). Bootstrap and sync PRs target `main` and are limited by `path-scope`: a bootstrap PR may not change template-owned paths except deleting disabled modules' files; a sync PR may change only template-owned paths, `AGENTS.md` and `.sop/config.yml`. The Chief's direct pushes of records aren't PRs and aren't checked here; the process and the Owner's milestone review cover them. Template-owned paths are read-only in projects, so sync can overwrite them safely.

## 4. 測試介面 / The test interface

主流測試工具（pytest、Jest、Go、JUnit、cargo-nextest 等）都能輸出 JUnit XML。專案只需實作一支可執行檔：

```text
scripts/sop/test  — 由專案實作（專案擁有，sop-sync 不覆寫）
  退出碼：0 = 全部通過，非 0 = 有失敗
  輸出：build/sop/junit.xml
  測試 ID：classname + "::" + name，必須穩定（改名會被視為測試消失）
```

- 範本內附的 `scripts/sop/test` 故意失敗，訊息是「請實作測試介面」。接上測試是啟動閘門的一部分（B5）。
- **它必須能在乾淨的 `ubuntu-24.04` runner 上直接執行**：自己安裝需要的套件、準備需要的拋棄式資源。`sop-guards` 的 `tests` job 直接呼叫它；`no-weakened-tests` 會在目標分支上執行**目標分支自己的** `scripts/sop/test`，再在 PR 上執行一次。
- 測試真的需要改名時，由 Chief 在 ticket 寫明舊名對新名的對應，並記錄在 `docs/decisions.md`。

> **EN:** The project implements `scripts/sop/test` (project-owned, never overwritten by sync): exit 0 when all pass, write `build/sop/junit.xml`, keep test IDs (`classname::name`) stable. The shipped stub fails on purpose (bootstrap check B5). It must run as-is on a clean `ubuntu-24.04` runner, installing what it needs; `no-weakened-tests` runs the target branch's own script there, then the PR's. Necessary renames are mapped in the ticket and recorded in the decision log by the Chief.

## 5. 停用檢查 / Disabling a check

專案可以停用某一項檢查（客製化層 C4），但必須：

1. 在 `docs/decisions.md` 新增一筆決定，說明原因（例如 `D-007`）。
2. 在 `.sop/config.yml` 的 `overrides.disabled_guards` 加入一項：`guard`、`reason`、`decision`。
3. 經 Owner 合併的 PR。

`sop-ready` 會檢查每一項都有對應的決策紀錄。`sop-ready` 本身不能停用。

> **EN:** A project may disable a check (layer C4) by recording a decision, adding `{guard, reason, decision}` to `overrides.disabled_guards`, and merging through the Owner. `sop-ready` verifies each entry against the decision log and cannot itself be disabled.
