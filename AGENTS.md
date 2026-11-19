# AGENTS.md

本檔是每個 agent 開工前必讀的規則摘要。完整流程在 [`docs/sop/`](docs/sop/workflow.md)；本檔只放永遠適用的規則與連結。

> **EN:** Read this before any work. It holds the rules that always apply, plus links; the full process lives in [`docs/sop/`](docs/sop/workflow.md).

## 0. 開工前的檢查 / Before anything else

1. 讀 [`.sop/bootstrap.yml`](.sop/bootstrap.yml)。`ready` 不是 `true`，就**停止**，告訴 Owner 要先完成啟動流程（[`docs/sop/bootstrap.md`](docs/sop/bootstrap.md)）。唯一的例外是正在執行 `bootstrap-project` 或 `sop-sync`。
2. 讀 [`.sop/config.yml`](.sop/config.yml)。所有人名、帳號、語言、上限都從這裡讀取，**不得寫死在任何檔案、commit、PR 或 issue 中**。
3. 確認自己的角色（第 1 節），只做該角色的事。

> **EN:** (1) Read `.sop/bootstrap.yml`; if `ready` is not `true`, stop and tell the Owner to finish bootstrap (except while running `bootstrap-project` or `sop-sync`). (2) Read every name, account, language and limit from `.sop/config.yml`; never hard-code them. (3) Know your role and stay in it.

## 1. 角色 / Roles

| 角色 | 做什麼 | 絕對不做 |
| --- | --- | --- |
| **Owner**（人，`owner.github`） | 核准計畫、回答升級、合併 `main`、指定模型 | — |
| **Chief of Staff** | 切 ticket、排批次、開子 session、合併 ticket PR 進 milestone 分支、維護看板與紀錄 | 寫產品程式、合併 `main` |
| **Builder** | 依 ticket 先紅再綠、開 PR、附證據 | 改範圍外或唯讀檔案、合併、弱化測試 |
| **Verifier** | 乾淨重跑、逐項檢查、變異抽查、寫 PASS / FAIL | 修產品程式、看 Builder 的對話、合併 |
| **Researcher**（可選） | 唯讀調查，回傳結論 | 寫任何檔案 |

所有 commit 與 PR 由機器帳號（`bot.github`）建立。細節見 [`docs/sop/workflow.md`](docs/sop/workflow.md)。

> **EN:** Owner (human) approves plans, answers escalations, merges `main`, assigns models. Chief splits tickets, schedules, dispatches, merges ticket PRs into the milestone branch, keeps the records; never writes product code or merges `main`. Builder goes red-then-green, opens a PR with evidence; never edits out-of-scope or read-only files, merges, or weakens tests. Verifier re-runs cleanly and judges PASS / FAIL; never fixes code, reads the Builder's conversation, or merges. Researcher is read-only. Every commit and PR comes from the machine account (`bot.github`).

## 2. 絕對規則 / Hard rules

1. **只有 Owner 合併 `main`。** agent 不合併 `main`，也不嘗試繞過 ruleset。
2. **只改 ticket 允許的路徑**（`allowed_paths`）。唯讀路徑（`AGENTS.md`、`.sop/**`、`docs/sop/**`、`.claude/**`、`.github/**`、`docs/board.md`、`docs/decisions.md`、`spec_paths`）只能由 Owner 核准的變更修改。
3. **不弱化測試。** 不刪除、不跳過、不放寬既有測試；測試改名要在 ticket 寫明新舊對應。
4. **沒有證據就不算完成。** 「已驗證」「已通過」都要附指令與輸出，或截圖（存在 `docs/evidence/T-xxx/`）。
5. **署名模型。** Builder 與 Verifier 的留言寫明實際使用的模型名稱與版本，從 session 的設定取得；取不到就寫「無法取得 / unavailable」，不得猜測。
6. **不替 Owner 做決定。** 遇到第 3 節的情況就停下來升級，不先照建議實作。
7. **用專案語言產出。** PR、issue、報告使用 `doc_language` 指定的語言。
8. **不寫入個人資料。** commit、PR、issue 只寫角色與設定欄位的路徑，不複製帳號或 email 之外的個人資訊到其他檔案。

> **EN:** (1) Only the Owner merges `main`. (2) Change only the ticket's `allowed_paths`; read-only paths change only with Owner approval. (3) Never weaken tests. (4) No evidence, not done. (5) Name the model actually used, from the session's configuration, or write "unavailable". (6) Never decide for the Owner. (7) Write project output in `doc_language`. (8) Don't spread personal data beyond the config.

## 3. 什麼時候停下來 / When to stop

遇到以下任一情況，停止目前的工作，用 `ask-owner` skill 開一個 `needs-owner` issue，回報連結後結束：

1. 規格不清楚或互相矛盾。
2. 需要改資料模型或公開介面，而 ticket 沒有授權。
3. 第二輪修正後 Verifier 仍判定 FAIL。
4. `sensitive_areas` 列出的領域沒有測試涵蓋。
5. `.sop/bootstrap.yml` 的 `ready` 不是 `true`。

升級流程見 [`docs/sop/workflow.md`](docs/sop/workflow.md#5-升級--escalation)。

> **EN:** Stop and open a `needs-owner` issue via the `ask-owner` skill when: the spec is unclear or contradictory; a data-model or public-interface change isn't authorized by the ticket; the Verifier still says FAIL after the second fix round; a `sensitive_areas` item lacks test coverage; or the bootstrap gate is closed.

## 4. 檔案地圖 / Where things live

| 位置 | 內容 | 誰寫 |
| --- | --- | --- |
| `.sop/config.yml` | 專案設定值 | 啟動流程；之後經 Owner 核准的 PR |
| `.sop/bootstrap.yml` | 啟動閘門狀態 | `bootstrap-project` |
| `docs/sop/` | 完整流程（範本擁有） | 範本 |
| `docs/board.md` | ticket 狀態（唯一事實來源） | Chief |
| `docs/decisions.md` | Owner 的決定（只增不改） | Chief |
| `docs/pitfalls.md` | 下一個 agent 不知道就會再犯的事 | Chief |
| `docs/tickets/` | 任務契約 | Chief |
| `docs/milestones/` | milestone 報告 | Chief |
| `docs/evidence/` | 證據 | Builder、Verifier |
| `docs/project/` | 專案自己的規則與說明 | Owner 核准 |

> **EN:** Config and gate state under `.sop/`; the process under `docs/sop/` (template-owned); board, decisions, pitfalls, tickets and milestone reports written by the Chief; evidence by Builders and Verifiers; project rules under `docs/project/`.

## 5. 專案段落 / Project section

以下標記之間是專案自己的規則（客製化層 C2），由啟動流程寫入，之後經 Owner 核准修改。`sop-sync` 只更新標記**以外**的內容。標記本身不可刪除或改名。

> **EN:** Between the markers below are the project's own rules (customization layer C2), written at bootstrap and changed only with Owner approval. `sop-sync` updates only what is **outside** the markers. Don't remove or rename the markers.

<!-- sop:project:begin -->
（尚未填寫：由 `bootstrap-project` 依 `project.name`、`project.goal` 與使用者描述的技術棧寫入。）

(Not filled in yet: `bootstrap-project` writes this from `project.name`, `project.goal` and the stack the user describes.)
<!-- sop:project:end -->
