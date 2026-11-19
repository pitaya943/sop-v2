# 角色的執行方式 / Dispatch

[`workflow.md`](workflow.md) 定義「誰做什麼」，本檔定義「怎麼跑起來」。工具改變時只改本檔。

> **EN:** `workflow.md` defines who does what; this file defines how roles are run. When tooling changes, only this file changes.

## 1. 機制 / Mechanisms

| 機制 | 隔離 | 成本 | 用於 |
| --- | --- | --- | --- |
| **獨立 cloud session**（建立 session 並傳送任務） | 最高：各自容器、context、資料庫 | 高 | Builder、Verifier |
| **同 session 的 subagent**（必要時用 worktree 隔離） | 中：共用容器 | 中 | Researcher |
| **Workflow 腳本** | 中 | 可能很高 | 預設不用；僅在 Owner 明確要求的固定批次 |

> **EN:** Builders and Verifiers run as separate cloud sessions (highest isolation); the Researcher as an in-session subagent; workflow scripts are off by default and used only when the Owner explicitly asks.

## 2. Verifier 為什麼一定是獨立 session / Why the Verifier is always a separate session

Verifier 的價值在於「不知道 Builder 怎麼想」。若能看到 Builder 的推理，它會傾向確認 Builder 的說法（anchoring）。所以：

- Verifier 的 prompt 只包含 PR 編號、ticket 檔路徑與 `verify-ticket` skill 的指示。
- Verifier 不讀 Builder 的對話或 session 紀錄。
- PR 說明裡的說法不算證據，Verifier 必須自己重跑。

> **EN:** A Verifier that can see the Builder's reasoning tends to confirm it (anchoring). Its prompt holds only the PR number, the ticket path and the `verify-ticket` instructions; it never reads the Builder's session and re-runs everything itself.

## 3. Dispatch prompt 的固定格式 / Fixed dispatch prompt

Chief 開子 session 時使用固定格式，不加入其他背景說明（保護子 session 的 context，也避免把 Chief 的判斷帶進去）：

```text
角色：Builder
Ticket：docs/tickets/T-012.md
分支：從 milestone/M2 開 ticket/T-012
模型：（Owner 在本 milestone 指定的 Builder 模型）
步驟：使用 build-ticket skill。只讀 ticket「要讀的檔案」列出的內容。
完成時：PR 開好、CI 全綠、交付留言已寫，然後結束。
遇到 AGENTS.md「什麼時候停下來」的情況：用 ask-owner skill，回報 issue 連結後結束。
```

```text
角色：Verifier
PR：#<編號>
Ticket：docs/tickets/T-012.md
模型：（Owner 在本 milestone 指定的 Verifier 模型）
步驟：使用 verify-ticket skill。不要讀 Builder 的對話。
完成時：在 PR 留下 PASS 或 FAIL 判定（附證據與模型署名），然後結束。
```

模型由 Owner 在計畫核准時指定，Chief 照抄，不自行選擇。

> **EN:** The Chief uses these fixed prompts and adds no other background, to protect the child's context and keep the Chief's opinions out. Models come from the Owner's plan approval; the Chief copies them and never picks its own.

## 4. Chief 如何得知進度 / How the Chief tracks progress

- **Builder 訂閱自己的 PR**，CI 結果會叫醒它，直到全綠。一個 PR 同時只能被一個 session 訂閱，所以 Chief 不訂閱 ticket PR。
- **Chief 在子 session 結束或失敗時收到通知**，並以 session 狀態與 PR 的 CI 結果重建進度。
- **Chief 只讀摘要：** PR 說明、Verifier 判定、CI 結果；不讀子 session 的完整對話，以保護自己的 context。
- **Chief 中斷時：** 新的 Chief session 讀 `docs/board.md`、開著的 PR 與 `needs-owner` issue 就能接手。

> **EN:** Builders subscribe to their own PR (one subscriber per PR, so not the Chief). The Chief is notified when child sessions end or fail and rebuilds progress from session status and CI. It reads only PR descriptions, verdicts and CI results, never full child transcripts. A replacement Chief resumes from the board, open PRs and `needs-owner` issues.

## 5. 目前的工具對應 / Current tool mapping

本節是唯一會隨工具版本改變的地方。

| 需求 | 目前的做法（Claude Code on the web） |
| --- | --- |
| 確認 GitHub 登入帳號 | 查詢目前登入的使用者（GitHub MCP 的 `get_me`，或 `gh api user`），與 `bot.github` 比對 |
| 設定 commit 作者 | `python3 scripts/sop/config.py --git-identity` |
| 開 Builder / Verifier | 建立新的 cloud session，傳送第 3 節的 prompt |
| 等待 CI | Builder 訂閱自己 PR 的活動 |
| 得知子 session 結束 | 子 session 的結束或失敗事件；必要時查詢 session 狀態 |
| Researcher | 同 session 的 subagent |
| 找 Owner | 機器帳號開 `needs-owner` issue |

> **EN:** The only part that changes with tool versions: today, identity is checked by querying the signed-in user and comparing with `bot.github`, the commit author is set with `--git-identity`, Builders and Verifiers are new cloud sessions sent the fixed prompt; Builders subscribe to their PR for CI; the Chief learns of child completion from session events; the Researcher is a subagent; the Owner is reached through `needs-owner` issues.
