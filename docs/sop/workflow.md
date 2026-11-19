# 工作流程 / Workflow

角色、milestone 與 ticket 的生命週期、升級、修正輪與證據。平行開發的規則在 [`parallel.md`](parallel.md)，角色怎麼跑起來在 [`dispatch.md`](dispatch.md)，CI 檢查在 [`ci-contract.md`](ci-contract.md)。

> **EN:** Roles, the milestone and ticket lifecycle, escalation, fix rounds and evidence. Parallelism is in `parallel.md`, how roles run is in `dispatch.md`, CI checks are in `ci-contract.md`.

## 1. 角色與權限 / Roles and permissions

| 角色 | 是誰 | 做什麼 | 不做什麼 | 生命週期 |
| --- | --- | --- | --- | --- |
| **Owner** | 人（`owner.github`） | 核准 milestone 計畫、回答升級 issue、審查並合併 `milestone/* → main`、指定各角色的模型、核准啟動閘門與範本更新 | — | 永久 |
| **Chief of Staff** | 一個 Claude Code session | 切 ticket、排平行批次、開子 session、合併 ticket PR 進 milestone 分支、維護看板、寫 milestone 報告 | 不寫產品程式、不合併 `main` | 一個 milestone；中斷時由新 session 從 repo 接手 |
| **Builder** | 每張 ticket 一個全新 session | 先紅再綠、開 PR、附證據 | 不改唯讀路徑、不改範圍外檔案、不合併、不弱化測試 | 一張 ticket（含第一輪修正） |
| **Verifier** | 每個 PR 每一輪一個全新 session | 乾淨重跑、逐項檢查、變異抽查、寫 PASS / FAIL 留言 | 不修產品程式、不看 Builder 的對話、不合併 | 一輪驗證 |
| **Researcher**（可選） | Chief 內的 subagent | 規劃時的唯讀調查，回傳結論 | 不寫任何檔案 | 一次呼叫 |

`bootstrap-project` 與 `sop-sync` 不是常駐角色，而是由 Owner 開的單次 session 執行，產出的 PR 一律由 Owner 合併。

**每條限制都有執行點：**

| 限制 | 執行點 |
| --- | --- |
| 只有 Owner 合併 `main` | GitHub ruleset：機器帳號無法更新 `main`（啟動時查證 B3） |
| Builder 不改範圍外檔案 | CI `path-scope` |
| Builder 不改規則、規格、看板 | CI `readonly-paths` |
| 不弱化測試 | CI `no-weakened-tests` |
| 只有機器帳號提交 | CI `commit-author` |
| Verifier 獨立 | dispatch 規則：全新 session，prompt 只給 PR 編號與 ticket 路徑 |
| 設定不完整時不能開工 | CI `sop-ready` 與每個 skill 開頭的檢查 |
| Chief 只在 PASS 後合併 ticket PR | milestone 分支的 ruleset 要求 CI 全綠；PASS 本身目前由流程保證 |

> **EN:** Five roles: Owner (human), Chief of Staff (one session per milestone, resumable from the repo), Builder (fresh session per ticket), Verifier (fresh session per PR per round), optional Researcher (read-only subagent). Bootstrap and sync are one-off Owner-started sessions whose PRs the Owner merges. Every "does not" has an enforcement point: a ruleset, a CI guard, or a dispatch rule.

## 2. Milestone 的生命週期 / Milestone lifecycle

```text
plan-milestone      Chief 讀需求、切 ticket、算批次，開計畫 issue
  → Owner 核准計畫   （關卡 1：Owner 同時指定 Builder / Verifier 的模型）
  → 建立 milestone/Mx 分支
  → 分批開 Builder → 每個 PR 開 Verifier → PASS 則 Chief 合併進 milestone/Mx
  → milestone-report Chief 寫報告，開 milestone/Mx → main 的 PR
  → Owner 合併 main （關卡 2）
```

每個 milestone 只有兩個 Owner 關卡。其餘時間 Owner 只在收到 `needs-owner` issue 時介入。

> **EN:** Each milestone has two Owner gates: approving the plan (including model assignments) and merging the milestone PR into `main`. Otherwise the Owner only answers `needs-owner` issues.

## 3. Ticket 狀態機 / Ticket state machine

| 從 | 到 | 觸發 | 誰 |
| --- | --- | --- | --- |
| todo | building | 依賴都已 merged，且被排進當前批次 | Chief |
| building | verifying | PR 已開且 CI 全綠 | Builder |
| verifying | passed | Verifier 判定 PASS | Verifier |
| verifying | fixing | Verifier 判定 FAIL | Verifier |
| fixing | verifying | 修正推送且 CI 全綠 | Builder |
| passed | merged | Chief 合併進 milestone 分支 | Chief |
| building / fixing | escalated | 規格問題、未授權變更、第二輪仍 FAIL | 任何角色經 Chief |
| escalated | building | Owner 回覆，Chief 記錄決定 | Chief |
| todo | blocked | 依賴的 ticket 被 escalated | Chief |

狀態只記在 `docs/board.md`，**Chief 是唯一寫入者**。其他角色回報給 Chief（PR 留言、session 結果），由 Chief 更新看板。因此新的 Chief 只要讀看板和 PR 狀態就能接手，不需要舊的對話。

> **EN:** States live only in `docs/board.md`, and only the Chief writes it; other roles report through PR comments and session results. A new Chief resumes from the board and PR state alone.

## 4. Ticket 契約 / The ticket contract

Ticket 檔（`docs/tickets/T-xxx.md`）是 Chief 與 Builder 之間唯一的契約，也是 CI 的輸入。front matter 使用 `.sop/config.yml` 同一套限制版 YAML（清單一律逐行寫 `- 項目`，空清單寫 `[]`）：

```yaml
---
id: T-012                    # 與分支 ticket/T-012 對應（CI branch-ticket）
title: 一句話
milestone: M2
depends_on:                  # 排程用
  - T-010
allowed_paths:               # CI path-scope；排程時判斷重疊
  - "src/billing/**"
  - "tests/billing/**"
  - "docs/evidence/T-012/**"
append_only: []              # 須同時列在 allowed_paths，且在 append_only_files 內
readonly_override: []        # 允許改動預設唯讀路徑，須 Owner 在計畫中核准
serial:                      # 序列化資源，須在 serial_resources 內
  - db-schema
evidence: cli                # cli | screens | none
done_when:                   # 這些測試 ID 必須在 JUnit 結果中存在且通過
  - "tests/billing/test_invoice.py::test_rounding"
status: todo                 # 只由 Chief 修改；實際狀態以 board.md 為準
---
```

本文的固定段落：`## 目標`、`## 要讀的檔案`（只讀這些，保護 Builder 的 context）、`## 完成條件`（與 `done_when` 一一對應的人讀版本）、`## 不在範圍內`。

完成條件只寫在 ticket 檔，而且以 `done_when` 的形式可被機器判定。

> **EN:** The ticket file is the only Chief–Builder contract and CI's input. Its front matter uses the same restricted YAML as the config (lists one item per line, `[]` when empty). "Done" lives only in the ticket, as machine-checkable `done_when` test IDs.

## 5. 升級 / Escalation

**什麼時候停下來找 Owner：**

1. 規格不清楚或互相矛盾。
2. 需要改資料模型或公開介面，而 ticket 沒有授權。
3. 第二輪修正後 Verifier 仍判定 FAIL。
4. `sensitive_areas` 列出的領域沒有測試涵蓋。

**怎麼升級：** 唯一的管道是 GitHub issue（`needs-owner` 標籤），由機器帳號用 `ask-owner` skill 開立，Owner 會收到通知。每個 issue：

- 說明卡在哪裡、已經試過什麼。
- 給兩到三個選項，每個選項寫出後果與反悔成本，並標出建議。
- **不替 Owner 決定，也不先照建議實作。**

等待期間，Chief 把該 ticket 設為 `escalated`，依賴它的 ticket 設為 `blocked`，不依賴它的 ticket 繼續進行。Owner 回覆後，Chief 把決定寫進 `docs/decisions.md`，再把 ticket 改回 `building`。

> **EN:** Stop for unclear specs, unauthorized data-model or interface changes, a second failed fix round, or untested sensitive areas. Escalate only via a `needs-owner` issue opened with the `ask-owner` skill: what's blocked, what was tried, two or three options with consequences and reversal cost, and a marked recommendation. Never decide or pre-implement. Unrelated tickets keep going; the Chief records the Owner's answer in `docs/decisions.md`.

## 6. 修正輪 / Fix rounds

| 輪次 | 誰修 | 為什麼 |
| --- | --- | --- |
| 第一輪 | 原 Builder session | 它有實作的 context，修小問題最快 |
| 第二輪 | 新的 Builder session，用 Owner 指定的較強模型 | 同一個 session 兩次都沒修好，通常是理解有偏差，換新 context 才能跳出 |
| 之後 | 停止，升級給 Owner | 避免子 session 空轉燒成本 |

每一輪都由新的 Verifier session 驗證。Chief 在看板記錄輪次與各輪使用的模型。

> **EN:** Round 1 is fixed by the original Builder; round 2 by a fresh Builder on a stronger Owner-chosen model; after that, escalate. Each round gets a fresh Verifier. The Chief records rounds and models on the board.

## 7. 證據與署名 / Evidence and attribution

- 任何「已驗證」「已通過」都附證據：CLI 指令與輸出；有畫面的附截圖。證據存在 `docs/evidence/T-xxx/`，或直接寫在 PR 說明的「證據」一節。
- 「先紅」的失敗輸出也是證據：它證明測試真的能偵測到問題。
- PR 說明裡的說法不算證據。Verifier 必須自己重跑。
- Builder 與 Verifier 的留言寫明模型名稱與版本，從 session 的實際設定取得，取不到就寫「無法取得 / unavailable」。

> **EN:** Every verification claim carries evidence (commands and output, screenshots when there's a UI) in `docs/evidence/T-xxx/` or the PR's evidence section. The failing "red" output counts too. Claims in a PR description are not evidence; the Verifier re-runs. Builders and Verifiers name the model from the session's actual configuration, or write "unavailable".

## 8. 記憶與狀態 / Memory and state

Context window 是短期記憶，用完即丟；要留下的事一律寫進 repo。

| 檔案 | 內容 | 寫入者 | 規則 |
| --- | --- | --- | --- |
| `docs/board.md` | ticket 狀態、輪次、各輪模型 | Chief | 單一事實來源；固定欄位的表格 |
| `docs/decisions.md` | Owner 的決定 | Chief | 只增不改；推翻時新增一列並註明取代哪列；編號 `D-001` 起 |
| `docs/pitfalls.md` | 下一個 agent 不知道就會再犯的事 | Chief（milestone 結束時） | 上限 30 條 |
| `docs/tickets/*.md` | 任務契約 | Chief | 完成條件只在這裡 |
| `docs/milestones/Mx.md` | 給 Owner 的報告 | Chief | 數字可重算；每個「已驗證」都連到證據 |
| `docs/learning.md` | 學習紀錄（僅在 `modules.learning` 開啟時存在） | Chief | 只增不改 |

> **EN:** Anything that must outlive a context window goes into the repo: the board (single source of truth), the append-only decision log (IDs from `D-001`), pitfalls (max 30), tickets, milestone reports, and, with the learning module on, `docs/learning.md`.
