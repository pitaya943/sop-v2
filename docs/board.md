# 進度看板 / Board

Chief 是唯一能修改這個檔案的角色。Chief 每次開始工作時先讀這個檔案，不依賴對話紀錄。

狀態：`todo` → `building` → `verifying` → `fixing` → `passed` → `merged`，或 `escalated`（已開 issue 等 Owner）、`blocked`（依賴的 ticket 尚未完成或被擋住）。

> **EN:** Only the Chief edits this file, and reads it first at the start of every session instead of relying on conversation history. States: `todo` → `building` → `verifying` → `fixing` → `passed` → `merged`, or `escalated` (waiting on the Owner) and `blocked` (a dependency isn't done).

<!--
每個 milestone 在計畫核准後新增一段，格式如下（Mx 換成實際編號）：
Add one section per milestone after its plan is approved:

## Mx（計畫：issue #N，D-xxx）

- 順序：T-x01 → T-x02 ‖ T-x03。
- 同時進行上限：2 張（不超過 max_parallel）。
- 模型：Chief （模型）；Builder （模型）；Verifier （模型）；修正第二輪 Builder （模型）。
- 結果：（milestone 結束時填寫：merged 張數、報告路徑、未決 issue。）

下表每張 ticket 一列。備註欄記下各輪使用的模型、Verifier 的判定與相關 issue。
One row per ticket below; the notes column records each round's model, verdicts and related issues.
-->

| Ticket | Milestone | 標題 | 狀態 | PR | 修正輪數 | 備註 |
| --- | --- | --- | --- | --- | --- | --- |
