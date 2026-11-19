---
name: ask-owner
description: "遇到規格不清楚、需要未授權的變更、修正兩輪失敗、或動到沒有測試涵蓋的敏感領域時，開 issue 請 Owner 決定。任何角色都可使用。/ Escalate a decision to the Owner through a needs-owner issue. Any role."
---

# 請 Owner 決定 / Ask the Owner

## 什麼時候用 / When

`AGENTS.md`「什麼時候停下來找 Owner」的四種情況。其他情況不要用；自己能從規格讀出答案的事不要問。

> **EN:** Only for the four situations in `AGENTS.md`. Don't ask what the spec already answers.

## 步驟 / Steps

1. 停止這張 ticket 上會受答案影響的工作。已完成且不受影響的部分先提交。
2. 找出確切的出處：規格的段落、檔案與行號、互相矛盾的兩段文字。
3. 想出兩到三個選項。每個選項寫清楚：做法、對使用者的後果、要改哪些測試或檔案、之後反悔的成本。
4. 選一個建議，寫出理由。**不要替 Owner 決定**，也不要先照建議實作。
5. 先搜尋開著的 `needs-owner` issue，同一個問題已經有 issue 就在那裡補充。否則用 `.github/ISSUE_TEMPLATE/needs-owner.md` 開 issue，用 `doc_language`，指派給 `owner.github`。
6. Builder 與 Verifier：把 issue 連結回報給 Chief，然後結束。Chief：把 ticket 標為 `escalated`，把依賴它的標為 `blocked`，繼續其他 ticket。

> **EN:** (1) Stop work the answer affects; commit unaffected finished work. (2) Cite the exact source: spec section, file and line, the two contradicting passages. (3) Two or three options, each with approach, user-facing consequence, tests or files to change, and reversal cost. (4) Recommend one with reasons; never decide or pre-implement. (5) Add to an existing open `needs-owner` issue, or open one from the template in `doc_language`, assigned to `owner.github`. (6) Builders and Verifiers report the link to the Chief and end; the Chief marks the ticket `escalated`, dependants `blocked`, and continues.

## 好問題的樣子 / A good question

> **問題**：停用一個帳號時，它建立的資料要一起隱藏嗎？
> **出處**：規格〈帳號〉第 4 條與〈資料保存〉第 2 條互相矛盾；`docs/tickets/T-012.md` 完成條件 3
> **選項 A（建議）**：資料保留且可見，只標示建立者已停用。不需改既有測試。反悔成本低。
> **選項 B**：資料一起隱藏。要新增兩個測試，並影響〈搜尋〉的結果。

> **EN:** State the question in one line, cite the exact source, and give options with their effect on tests and other rules, marking the recommended one.

## Owner 回覆之後（Chief）/ After the Owner answers (Chief)

1. 在 `docs/decisions.md` 新增一列。
2. 回覆改變規格時，在同一個 commit 修改規格與受影響 ticket 的完成條件。
3. 把 ticket 改回 `todo` 或 `building`，解除 `blocked`。
4. 推送後在 issue 留言寫明記錄在哪個 D 編號與 commit，然後關閉 issue。

> **EN:** Record a decision row; if the spec changes, update it and the affected tickets in the same commit; move the ticket back to `todo` or `building` and unblock dependants; push, comment the decision ID and commit on the issue, and close it.

## 這個 skill 在閘門未開時也能用 / Works with the gate closed

啟動閘門未開（`.sop/bootstrap.yml` 的 `ready` 不是 `true`）也是要告訴 Owner 的事，所以這個 skill 不因閘門未開而停止。設定本身無效、讀不到 `owner.github` 時，直接在對話中告訴使用者，不開 issue。

> **EN:** A closed bootstrap gate is itself something to report, so this skill runs anyway. If the config is invalid and `owner.github` can't be read, tell the user in the conversation instead of opening an issue.
