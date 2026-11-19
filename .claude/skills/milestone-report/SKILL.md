---
name: milestone-report
description: "在 milestone 的 ticket 全部合併後，寫給 Owner 的 HTML 報告並開 milestone PR。只有 Chief 使用。/ After every ticket is merged, write the HTML report for the Owner and open the milestone PR. Chief only."
---

# 寫 milestone 報告 / Write the milestone report

## 前提 / Preconditions

- `.sop/bootstrap.yml` 的 `ready` 是 `true`；登入帳號是 `bot.github`，並已執行 `python3 scripts/sop/config.py --git-identity`。
- 該 milestone 的每張 ticket 都是 `merged`，`milestone/Mx` 的 CI 全綠。

> **EN:** The gate is open, identity is confirmed and the git author is set; every ticket is merged and `milestone/Mx` is green.

## 步驟 / Steps

1. 複製 `docs/milestones/report-template.html` 為 `docs/milestones/Mx.html`。
2. 依樣板的每一節填寫。資料來源只用 repo 與 GitHub 上看得到的東西：ticket 檔、PR 說明、Verifier 留言、CI 結果、`docs/decisions.md`。不要憑印象寫。
3. 數字要能被重算：寫「通過 47 個測試」時，附上產生這個數字的指令與輸出。報告中每一個「已驗證」的說法都連到證據：CLI 輸出，或 `docs/evidence/` 下的截圖。
4. 「如何驗證」一節寫成 Owner 可以照做的步驟：指令、預期輸出、手動操作的流程。Owner 會用自己選的模型與環境驗證，所以不要假設他用的是這個 repo 的 agent。
5. 「為何這樣設計」一節寫出真的比較過的選項與放棄的理由。只有一種合理做法的地方不用硬湊選項。
6. 「agent 自行做的判斷」一節不可省略。列出規格沒有明說、由 agent 決定的每一件事；沒有就寫「無」。
7. 整理 `docs/pitfalls.md`：從各 PR 的提議中挑選，遵守上限 30 條；超過時先刪掉已經被 CI 檢查或 skill 取代的條目，刪除的條目不重新編號。
8. 更新 `docs/board.md` 這個 milestone 的段落（結果、報告路徑、未決 issue），把以上變更直接推送到 `milestone/Mx`。
9. 開 `milestone/Mx → main` 的 PR，指派給 `owner.github`。PR 說明簡短，並指向報告的路徑。
10. 關閉這個 milestone 所有已完成的子 session。

> **EN:** Copy the template to `Mx.html` and fill every section only from what's visible in the repo and on GitHub. Make numbers recomputable and link every "verified" claim to evidence. Write "how to verify" as steps the Owner can follow with their own model and environment. In "why this design", list only options really compared. "Judgments the agent made" is mandatory ("none" if none). Curate pitfalls (max 30, superseded first, never renumber). Update the board's milestone section and push to `milestone/Mx`. Open `milestone/Mx → main` assigned to the Owner with a short description pointing at the report. Close the milestone's finished child sessions.

## 寫作規則 / Writing rules

- 使用 `doc_language`，專業術語除外。
- 先講結論。讀者是 Owner，他沒有看過任何一張 ticket 的過程。
- 沒做到的事直接寫沒做到，不要寫成「後續可以改善」。
- 不要誇大。測試通過只代表符合規格，不代表規格是對的。

> **EN:** Write in `doc_language`. Conclusions first; the Owner hasn't followed any ticket. Say plainly what wasn't done. Don't exaggerate: passing tests mean the spec is met, not that the spec is right.
