# AGENTS.md — 永遠適用的規則 / Rules that always apply

這個檔案每個 session 都會載入，所以只放規則與連結。做法在 skills（`.claude/skills/`），細節在 [`docs/sop/workflow.md`](docs/sop/workflow.md)。兩者不一致時以 `docs/sop/` 為準。

> **EN:** Loaded by every session, so it holds only rules and links. How-to lives in the skills; details in `docs/sop/workflow.md`, which wins on any conflict.

## 0. 開工前 / Before anything

1. 讀 [`.sop/bootstrap.yml`](.sop/bootstrap.yml)。`ready` 不是 `true` 就**停止**，告訴 Owner 要先完成啟動流程（[`docs/sop/bootstrap.md`](docs/sop/bootstrap.md)）。只有執行 `bootstrap-project`、`sop-sync` 時例外。
2. 所有人名、帳號、語言、上限都從 [`.sop/config.yml`](.sop/config.yml) 讀取，**不寫死在任何檔案、commit、PR 或 issue 中**。
3. 依第 3 節確認 GitHub 身分並設定 commit 作者。

> **EN:** (1) Stop if the bootstrap gate isn't open (except for bootstrap and sync). (2) Read every name, account, language and limit from `.sop/config.yml`; never hard-code them. (3) Check your GitHub identity and set the commit author (section 3).

## 1. 角色 / Roles

| 角色 | 做什麼 | 不做什麼 |
| --- | --- | --- |
| **Owner**（`owner.github`） | 啟動 Chief session 並指定各角色的模型、核准每個 milestone 的計畫、回答 issue、審查並合併 `milestone/Mx → main` | — |
| **Chief** | 切 ticket、排順序、開子 session、更新 `docs/board.md`、合併 ticket PR 進 milestone 分支、寫 milestone 報告 | 不寫產品程式、不合併 `main` |
| **Builder** | 一張 ticket 一個全新 session：先讓完成條件的測試失敗，再實作到通過，開 PR | 不改規格、不改範圍外的檔案、不合併 |
| **Verifier** | 一個 PR 一個全新 session：從乾淨 checkout 重跑，依檢查表判定 PASS 或 FAIL | 不修產品程式、不合併 |

Verifier 永遠是全新的 session，只看 ticket、規格、diff 與自己執行的結果，不看 Builder 的對話。

> **EN:** The Owner starts the Chief session and assigns models, approves each milestone plan, answers issues, and merges `milestone/Mx → main`. The Chief splits and schedules tickets, dispatches sessions, keeps the board, merges ticket PRs into the milestone branch, and writes reports, but writes no product code and never merges `main`. A Builder is a fresh session per ticket: failing tests first, then implementation, then a PR. A Verifier is a fresh session per PR that re-runs from a clean checkout and judges PASS or FAIL without seeing the Builder's conversation.

## 2. 不可違反 / Never

1. **只有 Owner 合併 `main`。** Chief 只在 CI 全綠且 Verifier 判定 PASS 時，把 ticket PR 合併進 `milestone/Mx`。不 force-push，不改寫別人的分支歷史。
2. **Builder 不得修改** `AGENTS.md`、`CLAUDE.md`、`.sop/**`、`docs/sop/**`、`.claude/**`、`.github/**`、`docs/decisions.md`、`docs/board.md`、`spec_paths` 列出的規格，也不得修改 ticket 的 `allowed_paths` 以外的檔案。唯一的例外：ticket 的 `allowed_paths` **明確列出**（不含萬用字元）的路徑。
3. **不得為了通過而弱化測試**：不跳過、不標記預期失敗、不刪除測試、不放寬斷言。
4. **先寫會失敗的測試，再寫實作。**
5. **CI 是唯一的裁判。** 「我在本地跑過了」不算完成。
6. **有驗證就要有證據。** 任何「已驗證」「已通過」都附證據：CLI 的指令與輸出；有畫面的功能附截圖，存在 `docs/evidence/<ticket 編號>/` 並在 PR 中連結。沒有證據的說法視為沒有驗證。
7. **驗證留言要寫明模型。** Builder 的交付留言與 Verifier 的判定留言，寫出完成這項工作的模型名稱與版本。名稱從 session 的實際設定取得，不可憑印象填寫；取不到時寫「無法取得 / unavailable」並說明原因。
8. **不輸出機密。** 程式、紀錄、PR、issue 都不印出金鑰、密碼或其他憑證。
9. **不連線到共用或正式環境。** 開發、測試、CI 只用拋棄式的本機資源；碰正式環境的步驟由 Owner 親自執行。

> **EN:** (1) Only the Owner merges `main`; the Chief merges a ticket PR into `milestone/Mx` only with green CI and a PASS; no force-pushes or rewriting others' history. (2) Builders never touch the read-only paths or anything outside `allowed_paths`, except paths a ticket lists exactly (no wildcards). (3) Never weaken tests. (4) Failing test first. (5) CI is the only judge. (6) Every verification claim has evidence. (7) Verification comments name the model from the session's configuration, or "unavailable" with a reason. (8) Never print secrets. (9) Never connect to shared or production environments; only the Owner runs steps that touch them.

## 3. GitHub 身分 / GitHub identity

- 所有 GitHub 操作（push、開 PR、開 issue、留言、合併進 `milestone/*`）都以機器帳號 `bot.github` 進行。Owner 的帳號（`owner.github`）只由 Owner 本人使用。
- 開始工作前，確認目前的 GitHub 登入帳號是 `bot.github`（方法見 [`docs/sop/dispatch.md`](docs/sop/dispatch.md#5-目前的工具對應--current-tool-mapping)）。不是的話停止，告訴 Owner，不要用其他身分繼續。
- 第一次 commit 之前，設定 commit 作者並確認設定成功：

  ```bash
  python3 scripts/sop/config.py --git-identity
  ```

  它會把作者設成機器帳號與它的 GitHub noreply 位址（由 `bot.github_id` 與 `bot.github` 組成）。
- 機器帳號只有寫入權限，不能更新 `main`。不要嘗試繞過。

> **EN:** Every GitHub action is done as the machine account `bot.github`; the Owner's account is used only by the Owner. Before working, confirm you're signed in as `bot.github`, otherwise stop and tell the Owner. Before the first commit, run `python3 scripts/sop/config.py --git-identity` to set the author to the machine account's noreply address. The machine account can't update `main`; never try to bypass that.

## 4. 什麼時候停下來找 Owner / When to stop

遇到以下任一情況，停止這張 ticket，依 `ask-owner` skill 開一個標 `needs-owner` 的 issue：

1. 規格不清楚或互相矛盾。
2. 需要改資料模型或公開介面，而 ticket 沒有授權。
3. 修正兩輪後 Verifier 仍判定 FAIL。
4. 要動到 `sensitive_areas` 列出的領域，而沒有測試涵蓋。

**不確定的事不要自己決定。** Issue 裡給出兩到三個選項，說明各自的後果，並標出建議的那一個。不依賴這張 ticket 的其他 ticket 繼續進行。

> **EN:** Stop and open a `needs-owner` issue with the `ask-owner` skill when the spec is unclear or contradictory, an unauthorized data-model or interface change is needed, the Verifier still says FAIL after two fix rounds, or a `sensitive_areas` item lacks test coverage. Never decide uncertain things yourself: give two or three options with consequences and mark a recommendation. Unrelated tickets continue.

## 5. 記憶 / Memory

Context window 用完即丟；要留下的東西一律寫進 repo。

| 檔案 | 內容 | 誰能寫 |
| --- | --- | --- |
| `AGENTS.md`、`spec_paths` 的規格 | 規則與規格 | Owner 核准後由 Chief 修改 |
| `docs/decisions.md` | Owner 的決定，只增不改 | Chief |
| `docs/board.md`、`docs/tickets/*.md` | 進度與任務 | Chief |
| PR 說明 | 這張 ticket 做了什麼、證據、未解問題 | Builder、Verifier |
| `docs/pitfalls.md` | 下一個 agent 該知道的坑 | Chief 在 milestone 結束時整理；Builder 與 Verifier 只能在 PR 說明裡提議 |
| `docs/milestones/Mx.html` | 給 Owner 的 milestone 報告 | Chief |

每個 session 只載入自己那張 ticket「要讀的檔案」列出的內容，不要載入整份規格。

> **EN:** Anything that must outlive a context window goes into the repo: rules and specs (changed by the Chief after Owner approval), the append-only decision log, the board and tickets (Chief), PR descriptions (Builder, Verifier), pitfalls (curated by the Chief; others only propose), milestone reports (Chief). Each session loads only the files its ticket lists.

## 6. 語言 / Language

- 報告、PR、issue、`docs/**` 的說明文字：使用 `doc_language`。
- 程式碼識別字、commit 訊息：英文。

> **EN:** Reports, PRs, issues and docs are written in `doc_language`; code identifiers and commit messages in English.

## 7. Skills

| Skill | 誰用 | 何時 |
| --- | --- | --- |
| `plan-milestone` | Chief | milestone 開始前 |
| `build-ticket` | Builder | 做一張 ticket |
| `verify-ticket` | Verifier | 驗證一個 PR |
| `ask-owner` | 任何角色 | 遇到第 4 節的情況 |
| `milestone-report` | Chief | milestone 的 ticket 全部合併後 |

專案自己的 skill 放在 `.claude/skills/project/`。

> **EN:** `plan-milestone` (Chief, before a milestone), `build-ticket` (Builder), `verify-ticket` (Verifier), `ask-owner` (anyone, in the section 4 situations), `milestone-report` (Chief, after every ticket merged). Project-specific skills live in `.claude/skills/project/`.

## 8. 專案 / Project

以下標記之間是專案自己的內容（客製化層 C2），由啟動流程寫入，之後經 Owner 核准修改。`sop-sync` 只更新標記**以外**的內容。標記本身不可刪除或改名。

> **EN:** Between the markers is the project's own content (layer C2), written at bootstrap and changed only with Owner approval. `sop-sync` updates only what is outside the markers. Don't remove or rename the markers.

<!-- sop:project:begin -->
（尚未填寫。`bootstrap-project` 會依使用者的回答寫入以下各節：）

- **專案：** `project.name` 與 `project.goal`；規格的位置（`spec_paths`），規格不清楚時停下來問，不要猜。
- **技術：** 語言、框架、資料庫、測試工具。
- **專案規則：** 這個專案額外的「不可違反」。
- **目錄約定：** 主要目錄與用途。
- **指令：** 安裝、啟動、測試（`scripts/sop/test`）、其他常用指令。

(Not filled in yet. `bootstrap-project` writes these from the user's answers: project and spec location, stack, extra project rules, directory conventions, commands.)
<!-- sop:project:end -->
