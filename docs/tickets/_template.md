---
id: T-000
title: 一句話說明這張 ticket 做什麼
milestone: M0
depends_on: []
screens: false
allowed_paths:
  - "src/example/**"
  - "tests/example/**"
  - "docs/evidence/T-000/**"
append_only: []
serial: []
done_when:
  - "tests/example/test_example.py::test_example"
status: todo
---

# T-000 標題 / Title

<!--
樣板：Chief 在 plan-milestone 時複製成 docs/tickets/T-xxx.md。欄位說明見 docs/sop/workflow.md 第 6 節。
- depends_on、append_only、serial：可以寫 [T-001, T-002] 或逐行清單；沒有就寫 []。
- screens：有畫面要截圖時寫 true。這個欄位不可省略（CI evidence）。
- allowed_paths：需要修改唯讀路徑時，明確列出該檔案（不含萬用字元），並在計畫中說明。
- done_when：測試 ID（classname::name），與「完成條件」一一對應。

Template: the Chief copies this to docs/tickets/T-xxx.md during plan-milestone. Fields are explained in
docs/sop/workflow.md section 6. Lists may be [a, b] or one item per line; [] when empty. screens is
required. Read-only paths must be listed exactly. done_when holds test IDs matching the conditions below.
-->

## 目標 / Goal

（一兩句話：完成後使用者或系統能做到什麼。）

## 要讀的檔案 / Files to read

只讀這些，不要載入其他檔案。

- `AGENTS.md`
- （規格中與這張 ticket 有關的段落）
- （要重用的既有程式）
- `docs/decisions.md` 的（相關 D 編號）

## 完成條件 / Done when

1. （對應 `done_when` 的第一個測試 ID：行為、輸入、預期結果。）在實作前先確認它會失敗。
2. 錯誤路徑的測試斷言三件事：結果類別、完整錯誤訊息、狀態沒有任何變動。
3. 比規格更嚴格的斷言要在 PR 說明逐條列出。
4. CI 全綠。

## 不在範圍內 / Out of scope

- （明確不做的事，以及由哪張 ticket 處理。）
