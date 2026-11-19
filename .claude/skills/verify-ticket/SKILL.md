---
name: verify-ticket
description: "Verifier: independently re-run and check one ticket PR, spot-check tests by mutation, and post a PASS or FAIL verdict with evidence. Use when dispatched as a Verifier with a PR number and ticket path."
---

# verify-ticket

Verifier 用這個 skill 獨立驗收一個 ticket PR。你的價值在於**不知道 Builder 怎麼想**（[`docs/sop/dispatch.md`](../../../docs/sop/dispatch.md#2-verifier-為什麼一定是獨立-session--why-the-verifier-is-always-a-separate-session)）。

> **EN:** The Verifier uses this skill to judge one ticket PR independently. Your value is not knowing how the Builder thought.

## 0. 閘門與獨立性 / Gate and independence

1. 讀 `.sop/bootstrap.yml`。`ready` 不是 `true` 就停止。
2. 讀 `.sop/config.yml` 的 `doc_language` 與 `sensitive_areas`。
3. **不要**讀 Builder 的對話或 session 紀錄。PR 說明裡的說法不算證據，你要自己重跑。
4. 你**不修**產品程式，也不合併。

> **EN:** Stop if the gate is closed. Read `doc_language` and `sensitive_areas`. Never read the Builder's session; claims in the PR description are not evidence. Never fix product code or merge.

## 1. 乾淨重跑 / Clean re-run

1. 在乾淨的環境 checkout PR 的 head commit（記下 SHA）。
2. 執行 `scripts/sop/test`，保存完整輸出。
3. 確認 `build/sop/junit.xml` 存在。

> **EN:** Check out the PR's head commit in a clean environment (record the SHA), run `scripts/sop/test`, keep the output, and confirm the JUnit XML exists.

## 2. 逐項檢查 / Item by item

對 ticket 的每一項 `done_when`：

- 測試 ID 存在於 JUnit 結果中，而且通過。
- 讀測試本身：它真的檢查了「完成條件」描述的行為，而不是只跑過程式碼。

另外檢查：

- 變更的檔案都在 `allowed_paths` 內；沒有改唯讀路徑（除非 ticket 有 `readonly_override`）。
- 沒有刪除、跳過或放寬既有測試。
- PR 的證據一節有「先紅」與「全綠」的輸出，或連到 `docs/evidence/T-xxx/`。
- 觸及 `sensitive_areas` 的變更有測試涵蓋。

> **EN:** For each `done_when` item, confirm the test ID exists and passes, and read the test to make sure it checks the described behaviour. Also check scope, read-only paths, weakened tests, the evidence section, and coverage of sensitive areas.

## 3. 變異抽查 / Mutation spot-check

至少挑一項 `done_when`：故意改壞對應的產品程式（例如反轉一個條件、改一個常數），重跑測試，確認對應的測試**會失敗**。然後還原。

測試在程式被改壞後仍然通過，就是「造假的測試」，判定 FAIL。

> **EN:** For at least one `done_when` item, deliberately break the product code (flip a condition, change a constant), re-run, and confirm the matching test fails; then revert. A test that still passes is a fake test: FAIL.

## 4. 判定 / Verdict

在 PR 留下一則判定留言，語言用 `doc_language`：

```text
判定：PASS | FAIL
Head SHA：<sha>
模型：<名稱與版本，從 session 設定取得；取不到寫「無法取得 / unavailable」>

完成條件：
- [x] <test id>：<說明>
- [ ] <test id>：<為什麼不通過>

變異抽查：<改了什麼、哪個測試失敗了>
其他檢查：範圍 / 唯讀路徑 / 測試弱化 / 證據 / 敏感領域
證據：<指令與輸出，或連結>
FAIL 的理由（逐項，可直接照著修）：
1. ...
```

- **PASS：** 所有項目都通過，變異抽查有抓到。
- **FAIL：** 任何一項不通過。理由要具體到 Builder 可以直接照著修。

留言後結束。狀態由 Chief 更新。

> **EN:** Post one verdict comment in `doc_language` with the head SHA, your model, the `done_when` checklist, the mutation result, the other checks, evidence, and, on FAIL, concrete numbered reasons. PASS only if everything passes and the mutation was caught. Then end; the Chief updates the board.
