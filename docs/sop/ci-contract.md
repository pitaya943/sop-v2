# CI 契約 / CI contract

角色之間的契約由 CI 判定，不靠 agent 自律。檢查分成兩層：**中立層**只需要 git、`.sop/` 設定與 GitHub API，與技術棧無關；**介面層**透過專案實作的一支測試腳本取得結果。

> **EN:** Contracts between roles are enforced by CI, not by agents' good behaviour. Stack-neutral checks need only git, `.sop/` and the GitHub API; interface checks go through one project-implemented test script.

## 1. 檢查清單 / The guards

| 檢查 | 層 | 內容 | 輸入 |
| --- | --- | --- | --- |
| `sop-ready` | 中立 | 啟動閘門：設定符合 schema、`ready` 為 true 且 B1–B7 都已完成、僅範本檔案已移除、停用的檢查有決策紀錄 | `.sop/*`、檔案清單、`docs/decisions.md` |
| `branch-ticket` | 中立 | 目標是 `milestone/*` 的 PR，來源分支必須是 `ticket/T-xxx`，且目標分支上有對應的 ticket 檔 | 分支名、檔案 |
| `path-scope` | 中立 | 每個變更檔案都符合 ticket 的 `allowed_paths` | `git diff --name-only` |
| `readonly-paths` | 中立 | 不得修改唯讀路徑（第 2 節）；`readonly_override` 例外 | diff、ticket |
| `append-only` | 中立 | `append_only` 檔案的 diff 只有新增行 | `git diff` |
| `serial-resource` | 中立 | 宣告的資源在 `serial_resources` 內，且沒有其他進行中的 ticket 宣告同一項 | ticket、`docs/board.md` |
| `evidence` | 中立 | PR 說明的「證據」一節有 code block 或連到 `docs/evidence/T-xxx/`；`evidence: screens` 時至少一張圖 | PR body、檔案 |
| `commit-author` | 中立 | 每個 commit 的 GitHub 作者都是 `bot.github` | GitHub API、`.sop/config.yml` |
| `tests` | 介面 | 執行 `scripts/sop/test`，必須產生 `build/sop/junit.xml` | 專案實作 |
| `no-weakened-tests` | 介面 | 目標分支上通過的每個測試 ID，在 PR 上都被收集且通過；沒有 XML 判為失敗 | 兩份 JUnit XML |
| `done-when` | 介面 | ticket 的 `done_when` 每一項都在 PR 的 JUnit 中存在且通過 | ticket、JUnit XML |

`sop-ready` 對所有目標為 `main` 或 `milestone/*` 的 PR 執行，並一律列出目前停用的檢查。

> **EN:** Eight stack-neutral guards (sop-ready, branch-ticket, path-scope, readonly-paths, append-only, serial-resource, evidence, commit-author) and three interface guards (tests, no-weakened-tests, done-when). `sop-ready` runs on every PR into `main` or `milestone/*` and always lists the disabled guards.

## 2. 唯讀路徑 / Read-only paths

Builder 的 PR 不得修改：

- `AGENTS.md`、`CLAUDE.md`
- `.sop/**`、`docs/sop/**`、`.claude/**`、`.github/**`
- `docs/board.md`、`docs/decisions.md`
- `spec_paths` 列出的規格路徑

例外：

- ticket 的 `readonly_override`（須 Owner 在計畫中核准）。
- 啟動 PR（`sop/bootstrap` 分支）與 `sop-sync` PR（`sop/sync-*` 分支）只能改各自允許的路徑。

範本擁有的路徑（`.sop/managed.txt`）在專案中是唯讀的，所以 `sop-sync` 覆寫時不會蓋掉專案的修改。

> **EN:** Builder PRs may not touch `AGENTS.md`, `CLAUDE.md`, `.sop/**`, `docs/sop/**`, `.claude/**`, `.github/**`, the board, the decision log, or `spec_paths`, except through an Owner-approved `readonly_override`. Bootstrap and sync PRs may change only their own allowed paths. Because template-owned paths are read-only in projects, `sop-sync` can overwrite them without losing project changes.

## 3. 測試介面 / The test interface

pytest、Jest、Go、JUnit、cargo-nextest 等主流測試工具都能輸出 JUnit XML。專案只需實作一支可執行檔：

```text
scripts/sop/test  — 由專案實作（專案擁有，sop-sync 不覆寫）
  退出碼：0 = 全部通過，非 0 = 有失敗
  輸出：build/sop/junit.xml
  測試 ID：classname + "::" + name，必須穩定（改名會被視為測試消失）
```

- 範本內附的 `scripts/sop/test` 故意失敗，訊息是「請實作測試介面」。接上測試是啟動閘門的一部分（B5）。
- 測試改名時 CI 不提供例外：Chief 在 ticket 寫明新舊對應，並記錄在 `docs/decisions.md`。

> **EN:** The project implements `scripts/sop/test` (project-owned, never overwritten by sync): exit 0 when all pass, write `build/sop/junit.xml`, keep test IDs (`classname::name`) stable. The shipped stub fails on purpose; wiring it up is bootstrap check B5. Renames get no CI exception: the Chief records the mapping in the ticket and the decision log.

## 4. 停用檢查 / Disabling a guard

專案可以停用某一項檢查（客製化層 C4），但必須：

1. 在 `docs/decisions.md` 新增一筆決定，說明原因（例如 `D-007`）。
2. 在 `.sop/config.yml` 的 `overrides.disabled_guards` 加入一項：`guard`、`reason`、`decision`。
3. 經 Owner 合併的 PR。

`sop-ready` 會檢查每一項都有對應的決策紀錄。`sop-ready` 本身不能停用。

> **EN:** A project may disable a guard (layer C4) by recording a decision in `docs/decisions.md`, adding `{guard, reason, decision}` to `overrides.disabled_guards`, and merging through the Owner. `sop-ready` checks every entry against the decision log and cannot itself be disabled.

## 5. 檢查本身也要被測試 / Guards are tested too

每一項檢查都至少有一個「會讓它失敗」的測試案例，證明檢查真的有效。這些測試在範本 repo 的 `tests/sop/`，屬於僅範本檔案，不會留在專案中。

> **EN:** Every guard has at least one test proving it can fail. Those tests live in the template repo's `tests/sop/` and are not copied into projects.
