---
name: plan-milestone
description: "在 milestone 開始前，把該 milestone 切成 ticket、確認依賴與平行安排，並開 issue 請 Owner 核准。只有 Chief 使用。/ Before a milestone, split it into tickets, plan dependencies and parallelism, and ask the Owner to approve. Chief only."
---

# 規劃一個 milestone / Plan a milestone

## 步驟 / Steps

1. 讀 `.sop/bootstrap.yml`：`ready` 不是 `true` 就停止，告訴 Owner 要先完成啟動流程。
2. 依 `AGENTS.md` 的「GitHub 身分」確認登入帳號是 `bot.github`，並執行 `python3 scripts/sop/config.py --git-identity`。
3. 讀 `docs/board.md`、`docs/milestones/README.md`、`docs/decisions.md` 的待決定事項、`docs/pitfalls.md`，以及 `.sop/config.yml` 的 `max_parallel`、`serial_resources`、`append_only_files`、`sensitive_areas`。
4. 這不是第一個 milestone 時，確認前一個 milestone 已合併進 `main`；還沒有就停止並告訴 Owner。第一個 milestone 沒有前一個，跳過這一步。
5. 依 `docs/milestones/README.md` 的計畫，為這個 milestone 建立或檢查每張 ticket 檔（樣板 `docs/tickets/_template.md`）：
   - 依賴的 ticket 是否都已 `merged`，或排在本 milestone 之內。
   - `allowed_paths` 是否符合 repo 現在的目錄結構；需要改唯讀路徑時，明確列出該檔案（不用萬用字元），並在計畫中說明。
   - 完成條件（`done_when`）是否都對應到規格中還存在的內容。
   - `screens` 是否已填。
   - 待決定的事項是否擋住這張 ticket。
6. 需要調整時修改 ticket 檔，並記下差異。一張 ticket 的完成條件超過 20 項，或需要改三個以上的模組時，考慮拆開。
7. 依 [`docs/sop/parallel.md`](../../../docs/sop/parallel.md) 排出平行安排：依賴都已完成、路徑不重疊、序列化資源不重疊的 ticket 可以同時進行；同時進行的數量不超過 `max_parallel`。
8. 用 `.github/ISSUE_TEMPLATE/plan-approval.md` 開 issue，用 `doc_language`，指派給 `owner.github`。請 Owner 在核准時確認各角色的模型（Chief、Builder、Verifier、修正第二輪的 Builder）。
9. **等 Owner 回覆同意。** 在那之前不開任何 Builder session。
10. Owner 回覆後：
    - 把核准、選項與模型記進 `docs/decisions.md`。
    - 依選項修改 ticket 檔。
    - 在 `docs/board.md` 新增這個 milestone 的段落（計畫 issue、順序、同時進行上限、各角色模型）與 ticket 列。
    - 從 `main` 開出 `milestone/Mx`，把以上變更直接推送到這個分支。
    - 在 issue 留言寫明 D 編號與 commit，然後關閉 issue。

> **EN:** Stop if the gate is closed; confirm identity and run `--git-identity`. Read the board, the milestone plan, open decisions, pitfalls and the relevant config. Unless this is the first milestone, make sure the previous one is merged into `main`. Create or check each ticket from the template (dependencies, `allowed_paths` against the current tree with read-only paths listed exactly, `done_when` against the spec, `screens` filled in, blocking open decisions); split tickets with more than 20 conditions or touching three or more modules. Plan parallelism per `parallel.md` within `max_parallel`. Open a `plan-approval` issue asking the Owner to confirm the models. Wait for approval. Then record the decision and models, update tickets, add the milestone section and rows to the board, cut `milestone/Mx` from `main` and push these changes to it, comment the decision ID and commit, and close the issue.

## 輸出 / Output

一個 `plan-approval` issue；核准後，`milestone/Mx` 分支上一個包含 ticket 檔、看板與決策紀錄的 commit。

> **EN:** A `plan-approval` issue; after approval, one commit on `milestone/Mx` with the tickets, the board and the decision record.

## 不要做 / Don't

- 不要改規格。發現規格問題時用 `ask-owner`。
- 不要自己決定 ticket 沒有授權的資料模型或公開介面變更。
- 不要自己選模型；模型由 Owner 指定。
- 不要在 Owner 核准前開 Builder session。

> **EN:** Don't change the spec (use `ask-owner`); don't authorize data-model or interface changes yourself; don't pick models; don't start Builders before approval.
