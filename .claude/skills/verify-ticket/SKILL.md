---
name: verify-ticket
description: "驗證一個 ticket PR：從乾淨的 checkout 重跑、逐項檢查，判定 PASS 或 FAIL 並寫成 PR 留言。只有 Verifier 使用。/ Verify one ticket PR from a clean checkout and post PASS or FAIL. Verifier only."
---

# 驗證一個 ticket PR / Verify a ticket PR

你看不到 Builder 的對話，這是刻意的。只根據 ticket 檔、規格、diff 與你自己執行的結果判斷。Builder 在 PR 說明裡的說法不是證據。

> **EN:** You can't see the Builder's conversation, on purpose. Judge only from the ticket, the spec, the diff and what you run yourself. Claims in the PR description are not evidence.

## 開始前 / Before you start

1. 讀 `.sop/bootstrap.yml`：`ready` 不是 `true` 就停止。
2. 依 `AGENTS.md` 的「GitHub 身分」確認登入帳號是 `bot.github`，並執行 `python3 scripts/sop/config.py --git-identity`。
3. 讀 `.sop/config.yml` 的 `doc_language` 與 `sensitive_areas`。

> **EN:** Stop if the gate is closed. Confirm the machine-account identity and run `--git-identity`. Read `doc_language` and `sensitive_areas`.

## 檢查表 / Checklist

每一項寫出「通過」或「不通過」，並附證據：你自己執行的指令與輸出、檔案與行號；有畫面的功能要你自己操作並截圖，存到 `docs/evidence/<ticket 編號>/verify/`（把這些截圖提交到 PR 分支是你**唯一**可以推送的內容）。沒有證據的項目算不通過。Builder 提供的證據要重做一次，不能直接引用。

1. **乾淨重跑。** 從乾淨的 checkout 安裝、準備環境、執行 `scripts/sop/test`。結果與 CI 一致。
2. **完成條件。** ticket 的每一項 `done_when` 都在 JUnit 結果中被收集並通過；數量與 ticket 寫的相同。
3. **唯讀路徑沒被動。** 規格與其他唯讀路徑沒有變更（`allowed_paths` 明確列出的除外）。
4. **範圍。** 每個變更的檔案都在 `allowed_paths` 內。
5. **測試沒被弱化。** 沒有跳過或預期失敗的標記；沒有被刪除或放寬的斷言。
6. **測試是真的。** 逐一讀測試：真的呼叫產品程式；真的檢查結果；「沒有變動」比對的是實際的狀態。
7. **變異抽查。** 挑三項完成條件（優先挑 `sensitive_areas`、金額、權限、狀態轉移），各自在本地故意改壞對應的產品程式，確認對應的測試會失敗。做完還原，不要推送。
8. **錯誤路徑。** 抽查錯誤路徑的測試：結果類別、完整錯誤訊息、狀態沒有變動，三項都有斷言。
9. **繞過介面。** 直接對公開介面送出不合法的輸入（缺欄位、超出範圍、沒有權限的資料），確認被拒絕。
10. **規則本身。** 讀規格的文字，想兩個測試沒列出的邊界情況，實際試。結果不合規格時是 FAIL；規格沒有說清楚時不是 FAIL，寫進「規格問題」。
11. **不可違反的規則。** `AGENTS.md`「不可違反」的每一條。

> **EN:** Mark each item pass or fail with your own evidence; screenshots go under `docs/evidence/<ticket>/verify/`, the only thing you may push. No evidence means fail; redo the Builder's evidence yourself. (1) Clean re-run matching CI. (2) Every `done_when` ID collected and passing. (3) Read-only paths untouched. (4) In scope. (5) No weakened tests. (6) Tests are real. (7) Mutate three conditions (prefer sensitive areas, money, permissions, state transitions), confirm the tests fail, revert. (8) Error-path tests assert outcome, message and no state change. (9) Bypass the interface with invalid input and confirm rejection. (10) Try two unlisted edge cases against the spec text; unclear spec goes under "spec issues", not FAIL. (11) Every never-rule in `AGENTS.md`.

## 判定 / Verdict

- 全部通過：**PASS**。
- 任何一項不通過：**FAIL**，列出每個問題的位置、重現方式、預期與實際。**不要提供修正的程式碼。**

> **EN:** PASS only if everything passes. Otherwise FAIL, listing location, reproduction, expected and actual for each problem. Don't provide fix code.

## 輸出 / Output

一則 PR 留言，用 `doc_language`：

```text
## 驗證結果：PASS / FAIL

模型：（名稱與版本，從 session 的實際設定取得）
輪次：第 N 輪
Head commit：（SHA）

| # | 檢查 | 結果 | 證據 |
| --- | --- | --- | --- |

## 問題（FAIL 時）

## 規格問題（有的話）

## 想加入 docs/pitfalls.md 的提議（有的話）
```

> **EN:** One PR comment in `doc_language`: result, model, round, head commit, the checklist table, then problems, spec issues and pitfall proposals.

## 不要做 / Don't

- 不要修改產品程式或測試。
- 不要憑印象填寫模型名稱；取不到時寫「無法取得 / unavailable」並說明原因。
- 不要因為 CI 是綠的就判定 PASS。
- 不要合併 PR。

> **EN:** Don't change product code or tests; don't guess the model name; don't PASS because CI is green; don't merge.
