---
name: build-ticket
description: "實作一張 ticket：先讓完成條件的測試失敗，再實作到通過，然後開 PR。只有 Builder 使用。/ Implement one ticket red-then-green and open a PR. Builder only."
---

# 做一張 ticket / Build a ticket

## 開始前 / Before you start

1. 讀 `.sop/bootstrap.yml`：`ready` 不是 `true` 就停止，告訴 Chief 啟動閘門未開。
2. 依 `AGENTS.md` 的「GitHub 身分」確認登入帳號是 `bot.github`，並執行 `python3 scripts/sop/config.py --git-identity` 設定 commit 作者。
3. 讀 ticket 檔，然後**只讀**它「要讀的檔案」列出的內容。
4. 從 `milestone/Mx` 開出 `ticket/T-xxx` 分支。
5. 有任何一條完成條件看不懂，或規格互相矛盾：停止，用 `ask-owner`。不要猜。

> **EN:** Stop if the bootstrap gate is closed. Confirm you're signed in as `bot.github` and run `--git-identity`. Read the ticket, then only the files it lists. Branch `ticket/T-xxx` from `milestone/Mx`. If a completion condition is unclear or the spec contradicts itself, stop and use `ask-owner`; don't guess.

## 步驟 / Steps

1. **先紅。** 為每一項 `done_when` 寫測試（測試 ID 與 `done_when` 完全相同），執行 `scripts/sop/test`，確認這些測試失敗，而且失敗的原因是功能不存在，不是測試寫錯。把失敗的輸出留下來，PR 說明要用。
2. **再綠。** 實作到全部通過。一次處理一項完成條件。
3. **錯誤路徑**的測試要斷言：結果的類別、完整的錯誤訊息、狀態沒有任何變動。
4. 執行全部測試，確認沒有弄壞先前完成的功能。
5. 檢查自己改過的檔案都在 `allowed_paths` 內；`append_only` 的檔案只有新增行。
6. 推送並開 PR，目標分支是 `milestone/Mx`。依 `.github/PULL_REQUEST_TEMPLATE.md` 填寫，用 `doc_language`。
7. 等 CI。CI 沒有全綠就繼續修，直到全綠才算交付。
8. 在 PR 留一則交付留言：完成條件逐條對應的證據，以及你的模型名稱與版本。模型名稱從 session 的實際設定取得，不要憑印象寫。

> **EN:** (1) Red: write a test per `done_when` item with that exact ID, run `scripts/sop/test`, and confirm they fail because the feature is missing; keep the output. (2) Green: implement until all pass, one condition at a time. (3) Error-path tests assert the outcome type, the full message, and no state change. (4) Run everything to catch regressions. (5) Stay within `allowed_paths`; append-only files only gain lines. (6) Open the PR to `milestone/Mx` with the template, in `doc_language`. (7) Keep fixing until CI is green. (8) Post a hand-off comment with evidence per condition and your model from the session's configuration.

## 證據 / Evidence

- 每一條完成條件都要有證據，沒有證據就不算完成。
- CLI：貼上指令與輸出。輸出太長時保留開頭、結尾與統計行。
- 有畫面的功能（ticket 為 `screens: true`）：實際操作並截圖，存到 `docs/evidence/<ticket 編號>/`，檔名說明內容，在 PR 中連結。
- 「先紅」的失敗輸出也是證據。

> **EN:** Every completion condition needs evidence: commands and output (keep head, tail and the summary line when long); for `screens: true`, real screenshots under `docs/evidence/<ticket>/` linked from the PR; the red output counts too.

## 不要做 / Don't

- 不要修改規格（`spec_paths`）或其他唯讀路徑，除非 ticket 的 `allowed_paths` **明確列出**該路徑（不含萬用字元）。規格看起來有錯時用 `ask-owner`。
- 不要跳過、標記預期失敗、刪除或放寬任何測試。
- 不要讓測試永遠通過。測試必須真的呼叫產品程式並檢查結果。
- 不要碰 `serial` 以外的序列化資源，也不要新增 ticket 沒有授權的資料模型變更。
- 不要連線到共用或正式環境。
- 不要合併自己的 PR。

> **EN:** Don't edit the spec or other read-only paths unless the ticket's `allowed_paths` names that exact path (otherwise use `ask-owner`); don't skip, xfail, delete or loosen tests; don't write tests that always pass; don't touch unauthorized serialized resources or data-model changes; don't connect to shared or production environments; don't merge your own PR.

## PR 說明要有 / The PR description includes

- 完成了什麼：ticket 編號、完成條件的數量。
- 如何驗證：指令與預期結果。
- 證據：每條完成條件的 CLI 輸出或截圖路徑；「先紅」時的失敗輸出。
- Milestone 報告的路徑。
- **比規格更嚴格的斷言：** 逐條列出。這類斷言會被 CI 保護，之後要放寬得經過 Owner。
- 未解問題，以及想加入 `docs/pitfalls.md` 的提議。

> **EN:** What was done (ticket, number of conditions); how to verify; evidence per condition plus the red output; the milestone report path; every assertion stricter than the spec, listed (CI will protect them, so loosening later needs the Owner); open questions and pitfall proposals.

## 修正第一輪 / Fix round 1

Verifier 判定 FAIL 時，你（原 Builder session）依報告逐項修正，推送後等到 CI 全綠，再留言說明修了什麼。第二輪由新的 Builder session 處理。

> **EN:** On FAIL, you fix round 1 item by item, wait for green CI, and comment what changed. Round 2 goes to a fresh Builder.
