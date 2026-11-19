# Milestone 計畫 / Milestone plan

**狀態：草稿。** 每個 milestone 開始前，Chief 依當時的 repo 狀態重新確認這份計畫中屬於該 milestone 的部分，開一個標 `plan-approval` 的 issue，Owner 回覆同意後才開工。

> **EN:** **Status: draft.** Before each milestone the Chief re-checks its part of this plan against the repo, opens a `plan-approval` issue, and starts only after the Owner agrees.

<!--
這個檔案屬於專案（sop-sync 不會覆寫）。Owner 與 Chief 在第一個 milestone 前一起寫好，之後依實際進度修訂。
This file belongs to the project (never overwritten by sop-sync). Write it with the Owner before the first
milestone and revise it as the project goes.
-->

## Milestone

| ID | 名稱 | 完成條件 | Ticket 數 |
| --- | --- | --- | --- |
| M0 | （例：基礎建設） | （例：專案骨架、測試介面 `scripts/sop/test` 與 CI 可用；一個冒煙測試從入口走到儲存層並通過。） | （數量） |

每個 milestone 的共同完成條件：該 milestone 所有 ticket 的狀態為 `merged`；`milestone/Mx` 分支的 CI 全綠；`docs/milestones/Mx.html` 報告完成；`milestone/Mx → main` 的 PR 已開並指派給 Owner。

> **EN:** Every milestone is done when all its tickets are `merged`, `milestone/Mx` is green, `docs/milestones/Mx.html` is written, and the `milestone/Mx → main` PR is open and assigned to the Owner.

## 順序的理由 / Why this order

（依規格的依賴關係說明順序：哪些能力必須先有、哪些可以平行。）

> **EN:** Explain the order from the spec's dependencies: what must exist first and what can run in parallel.

## Ticket

| Ticket | Milestone | 標題 | 依賴 | 完成條件數 | 序列化資源 |
| --- | --- | --- | --- | --- | --- |
| T-001 | M0 | （標題） | — | （數量） | — |
