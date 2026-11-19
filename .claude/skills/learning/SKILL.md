---
name: learning
description: "學習模組（modules.learning 開啟時才存在）：在 milestone 報告後，請 Owner 先回答四個問題，再比較 Chief 的答案並記錄。只有 Chief 使用。/ Learning module: after a milestone report, the Owner answers four questions first, then the Chief compares and records. Chief only."
---

# 學習回顧 / Learning review

這個 skill 屬於可選的學習模組，只在 `.sop/config.yml` 的 `modules.learning` 為 `true` 時存在。目的是讓 Owner 理解並檢驗 agent 做的事，而不是只接受結果。

> **EN:** Part of the optional learning module; present only when `modules.learning` is `true`. Its purpose is for the Owner to understand and test what the agents did, not just accept the result.

## 什麼時候用 / When

`milestone-report` 完成、milestone PR 開好之後；或 Owner 在某個重要決定後要求時。

> **EN:** After `milestone-report` has opened the milestone PR, or when the Owner asks after an important decision.

## 步驟 / Steps

1. 讀 `.sop/bootstrap.yml`：`ready` 不是 `true` 就停止。確認 `modules.learning` 為 `true`；不是就停止。依 `AGENTS.md` 的「GitHub 身分」確認登入帳號，並執行 `python3 scripts/sop/config.py --git-identity`。
2. 在 milestone PR（或 Owner 指定的 issue）留言，用 `doc_language`，請 Owner **先**回答四個問題：
   - **Q1** 這個 milestone 做了什麼，為什麼要做？
   - **Q2** 為什麼選這個做法，而不是其他選項？
   - **Q3** 在什麼情況下它會失效？
   - **Q4** 你學到了什麼？
3. **等 Owner 回答。** 在那之前不要給出自己的答案，以免 Owner 照抄。
4. Owner 回答後，寫出 Chief 的建議答案，並逐題指出 Owner 的答案與建議答案不同的地方。不同不代表 Owner 錯：說明差異的原因，必要時引用報告或決策紀錄。
5. 在 `docs/learning.md` 新增一節（只增不改）：milestone 或決定的編號、日期、四題的 Owner 最終答案、主要差異與結論。直接推送到目前的 milestone 分支；milestone 已合併時，推送到下一個 milestone 分支。

> **EN:** Stop if the gate is closed or the module is off; confirm identity and run `--git-identity`. Ask the Owner, in `doc_language`, to answer four questions first (what and why; why this approach; when it breaks; what you learned). Don't give your answers until they reply, so they aren't copied. Then give the Chief's suggested answers and point out each difference, explaining why rather than marking the Owner wrong. Append a section to `docs/learning.md` with the milestone or decision ID, the date, the Owner's final answers and the main differences, pushed to the current (or next) milestone branch.

## 不要做 / Don't

- 不要在 Owner 回答前公布答案。
- 不要修改已經寫進 `docs/learning.md` 的內容。
- 不要把四個問題當成核准的條件；milestone 的合併只由 Owner 決定。

> **EN:** Don't reveal answers first; don't edit past entries; don't make the questions a merge condition.
