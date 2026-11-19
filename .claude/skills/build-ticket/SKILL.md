---
name: build-ticket
description: "Builder: implement one ticket red-then-green on its ticket branch, open a PR with evidence, and keep it green. Use when dispatched as a Builder with a ticket path."
---

# build-ticket

Builder 用這個 skill 完成一張 ticket。規則來源：[`docs/sop/workflow.md`](../../../docs/sop/workflow.md)、[`docs/sop/ci-contract.md`](../../../docs/sop/ci-contract.md)。

> **EN:** The Builder uses this skill to complete one ticket, following `docs/sop/workflow.md` and `docs/sop/ci-contract.md`.

## 0. 閘門 / Gate

1. 讀 `.sop/bootstrap.yml`。`ready` 不是 `true` 就停止，回報「啟動閘門未開」後結束。
2. 讀 `.sop/config.yml`：之後用到的 `doc_language`、`sensitive_areas`、`append_only_files`、`serial_resources` 都從這裡取得。

> **EN:** Stop if `.sop/bootstrap.yml` has `ready` other than `true`. Read `doc_language`, `sensitive_areas`, `append_only_files` and `serial_resources` from `.sop/config.yml`.

## 1. 讀契約 / Read the contract

1. 讀 dispatch prompt 指定的 ticket 檔（`docs/tickets/T-xxx.md`）。
2. **只讀** ticket「要讀的檔案」列出的內容，加上 `AGENTS.md` 與 `docs/pitfalls.md`。不要為了「多了解一點」去讀整個 repo：context 是有限的。
3. 確認你理解每一項 `done_when`。有任何一項不清楚、互相矛盾，或需要改 ticket 沒有授權的資料模型或公開介面，就**停下來**，用 `ask-owner` skill 升級。

> **EN:** Read the ticket, then only the files it lists plus `AGENTS.md` and `docs/pitfalls.md`. If any `done_when` item is unclear, contradictory, or needs an unauthorized data-model or interface change, stop and escalate with `ask-owner`.

## 2. 開分支 / Branch

從 dispatch prompt 指定的 milestone 分支開 `ticket/T-xxx`（編號與 ticket 的 `id` 相同，CI `branch-ticket` 會檢查）。

> **EN:** Branch `ticket/T-xxx` (matching the ticket's `id`) from the milestone branch named in the dispatch prompt.

## 3. 先紅 / Red first

1. 為每一項 `done_when` 寫測試，測試 ID 必須與 `done_when` 完全相同。
2. 執行 `scripts/sop/test`，確認新測試**失敗**，而且失敗的原因正是功能尚未實作。
3. 保存失敗的輸出：它是證據的一部分。

如果新測試一開始就通過，代表測試沒有測到東西，或功能已存在。不要繼續，先釐清原因。

> **EN:** Write a test for every `done_when` item with exactly that test ID, run `scripts/sop/test`, and confirm the new tests fail for the right reason. Keep that output as evidence. A test that passes before any implementation is a red flag: find out why before continuing.

## 4. 再綠 / Then green

1. 實作到所有測試通過。
2. **只改 `allowed_paths` 內的檔案。** 需要改範圍外的檔案就停下來升級，不要「順手」修改。
3. `append_only` 列出的檔案只能新增行。
4. 不刪除、不跳過、不放寬任何既有測試（CI `no-weakened-tests`）。
5. 改到 `sensitive_areas` 列出的領域時，確認有測試涵蓋；沒有就升級。

> **EN:** Implement until everything passes, touching only `allowed_paths`, only adding lines to `append_only` files, never weakening existing tests, and escalating if a `sensitive_areas` item lacks coverage.

## 5. 開 PR / Open the PR

1. 執行 `scripts/sop/test`，確認全部通過，並產生 `build/sop/junit.xml`。
2. 開 PR：`ticket/T-xxx` → milestone 分支，使用 `.github/PULL_REQUEST_TEMPLATE.md`，語言用 `doc_language`。
3. 「證據」一節放：先紅的失敗輸出、最後全綠的輸出（code block），或連到 `docs/evidence/T-xxx/`。`evidence: screens` 時附截圖。
4. 寫明你的模型名稱與版本，從 session 的設定取得；取不到就寫「無法取得 / unavailable」。
5. 訂閱這個 PR 的活動，讓 CI 結果叫醒你。

> **EN:** Run the tests, open the PR from `ticket/T-xxx` to the milestone branch with the PR template in `doc_language`, put red and green output (or screenshots) in the evidence section, name your model from the session's configuration or write "unavailable", and subscribe to the PR so CI results wake you.

## 6. 直到全綠 / Until green

- CI 失敗時找出根本原因並修正。不跳過、不停用測試來讓 CI 變綠。
- CI 全綠後在 PR 留一則交付留言（摘要、完成條件對照、證據位置、模型署名），然後結束。狀態由 Chief 更新，你不改 `docs/board.md`。

> **EN:** Fix CI failures at the root, never by skipping tests. Once green, leave a hand-off comment (summary, `done_when` checklist, where the evidence is, your model) and end. The Chief updates the board, not you.

## 7. 第一輪修正 / Fix round 1

Verifier 判定 FAIL 時，你（原 Builder session）負責第一輪修正：逐項處理 FAIL 的理由，推送後同樣等到 CI 全綠，再留言說明修了什麼。第二輪由新的 Builder session 處理，你不需要繼續。

> **EN:** On a FAIL verdict you handle fix round 1: address each reason, push, wait for green CI, and explain the changes. Round 2 goes to a fresh Builder.
