---
name: ask-owner
description: "Any role: escalate a decision to the Owner by opening a needs-owner issue with options, consequences and a recommendation, without deciding or pre-implementing. Use whenever AGENTS.md says to stop."
---

# ask-owner

任何角色遇到 [`AGENTS.md`](../../../AGENTS.md) 第 3 節「什麼時候停下來」的情況時，用這個 skill 找 Owner。唯一的管道是 GitHub issue。

> **EN:** Any role uses this skill when `AGENTS.md` section 3 says to stop. The only channel is a GitHub issue.

## 0. 閘門 / Gate

讀 `.sop/config.yml`，取得 `owner.github` 與 `doc_language`。

這個 skill 也用於「啟動閘門未開」的情況，所以 `.sop/bootstrap.yml` 的 `ready` 不是 `true` 時**仍然可以**使用；若設定本身無效、讀不到 `owner.github`，就直接在對話中告訴使用者，不開 issue。

> **EN:** Read `owner.github` and `doc_language` from `.sop/config.yml`. This skill also reports a closed gate, so it runs even when `ready` isn't `true`; if the config is invalid and `owner.github` is unreadable, tell the user in the conversation instead.

## 1. 先查重複 / Check for duplicates

搜尋開著的 `needs-owner` issue。同一個問題已經有 issue，就在那個 issue 補充新資訊，不要重開。

> **EN:** Search open `needs-owner` issues and add to an existing one rather than opening a duplicate.

## 2. 開 issue / Open the issue

使用 `.github/ISSUE_TEMPLATE/needs-owner.md`，加上 `needs-owner` 標籤，指派給 `owner.github`，語言用 `doc_language`。內容：

1. **卡在哪裡：** 哪張 ticket、哪一步、哪條規則讓你停下來。
2. **已經試過什麼：** 讀了哪些檔案、得到什麼結論。
3. **選項：** 兩到三個。每個選項寫出：
   - 會發生什麼；
   - 反悔的成本（之後要改回來有多難）；
   - 對其他 ticket 的影響。
4. **建議：** 標出你建議哪一個，以及理由。
5. **等待期間：** 哪些工作會停住，哪些可以繼續。

> **EN:** Use the needs-owner issue template, label `needs-owner`, assign `owner.github`, write in `doc_language`. Include: where you're stuck, what you tried, two or three options each with consequences, reversal cost and impact on other tickets, a marked recommendation with reasons, and what pauses meanwhile.

## 3. 不要做的事 / Don't

- **不替 Owner 決定。** 即使你很確定，也只寫成「建議」。
- **不先照建議實作。** 等 Owner 回覆。
- 不在 issue 寫入任何個人資料；人一律用角色稱呼。

> **EN:** Never decide for the Owner, never implement the recommendation in advance, and refer to people by role only.

## 4. 結束 / Finish

回報 issue 連結，然後結束目前的 session。Chief 會把 ticket 設為 `escalated`，依賴它的 ticket 設為 `blocked`；Owner 回覆後，由 Chief 把決定寫進 `docs/decisions.md`。

> **EN:** Report the issue link and end the session. The Chief marks the ticket `escalated` (and dependants `blocked`) and records the Owner's answer in `docs/decisions.md`.
