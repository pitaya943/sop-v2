---
name: bootstrap-project
description: "從 sop-v2 範本建立的專案，逐題詢問並即時查證所有設定（B1–B7），完成後開啟動 PR 給 Owner 合併。由 Owner 開的單次 session 使用。/ Bootstrap a project created from the sop-v2 template: ask for and live-check every setting (B1-B7), then open the bootstrap PR for the Owner to merge."
---

# 啟動專案 / Bootstrap a project

這個 skill 讓啟動閘門（[`docs/sop/bootstrap.md`](../../../docs/sop/bootstrap.md)）可以打開。對話與判斷由你負責；所有確定性的步驟都交給 `scripts/sop/bootstrap`，不要手動改 `.sop/` 的檔案。

這是唯一可以在 `.sop/bootstrap.yml` 的 `ready` 不是 `true` 時使用的 skill（另一個是 `sop-sync`）。

> **EN:** This skill opens the bootstrap gate. You handle the conversation and the judgment; every deterministic step goes through `scripts/sop/bootstrap`, never hand edits under `.sop/`. It's one of only two skills that run while `ready` isn't `true`.

## 互動原則 / How to ask

- **一次問一題**，附上說明、為什麼需要、建議值（如果有）。**不得替使用者填入答案。**
- 每個答案立刻驗證（規則在 `.sop/schema.json`）；不通過時說明原因，並指出去哪個設定頁修正，再重問。
- 使用者說「不知道」時，解釋選項與後果，請使用者決定；仍無法決定就停在該題，不跳過。
- 全部答完後，列出完整設定讓使用者確認，再寫入檔案。

> **EN:** One question at a time, with an explanation and any suggestion, but never fill in an answer. Validate each answer at once and point to the fix on failure. On "I don't know", explain the options and stop there rather than skip. Confirm the full config before writing it.

## 步驟 / Steps

1. **身分。** 確認目前的 GitHub 登入帳號就是使用者要用的機器帳號（方法見 [`docs/sop/dispatch.md`](../../../docs/sop/dispatch.md#5-目前的工具對應--current-tool-mapping)）。從 `main` 開 `sop/bootstrap` 分支。
2. **先教設定。** 請 Owner 依 [`docs/sop/setup.md`](../../../docs/sop/setup.md) 完成第 1–6、8–10 步（第 7 步的必要檢查要等 CI 跑過一次，在第 9 步之後做）。逐步確認，有問題就停在那一步。
3. **逐題詢問設定。** 依 `.sop/schema.json` 的順序問每一個欄位（`python3` 可以用 `scripts/sop/bootstrap` 的 `fields()` 取得清單）：
   - `template.source`：先查這個 repo 在 GitHub API 上的 `template_repository`，請使用者確認；查不到就請使用者輸入。
   - `bot.github_id`：查機器帳號的使用者資料取得，請使用者確認。
   - `max_parallel`：可以說明經驗值是 2–3，但由使用者決定。
   - `overrides.disabled_guards`：問「要不要停用任何檢查」；要的話，每一項都需要原因與 `docs/decisions.md` 的決策編號。
4. **確認後寫入。** 把答案寫成 JSON（欄位路徑對應值），執行 `scripts/sop/bootstrap write <answers.json>`。有錯誤就回到該題重問。
5. **專案段落。** 問使用者的技術棧、額外的專案規則、目錄約定、常用指令，整理成 Markdown，執行 `scripts/sop/bootstrap apply --notes <notes.md>`。它會移除僅範本檔案與關閉的模組、寫入專案 README 與 `AGENTS.md` 的專案段落。
6. **測試介面（B5）。** 依使用者的技術棧協助寫出 `scripts/sop/test`（規格見 [`docs/sop/ci-contract.md`](../../../docs/sop/ci-contract.md#4-測試介面--the-test-interface)），並加入至少一個冒煙測試。實際執行，確認產生 `build/sop/junit.xml`。
7. **查證（B1–B7）。** 執行 `scripts/sop/bootstrap check`。有 `GITHUB_TOKEN` 時它會查 B1–B4、B6；沒有，或讀不到（例如機器帳號讀不到 ruleset），就用你可用的工具查證，或請 Owner 提供設定畫面的截圖（存在 `docs/evidence/bootstrap/`），再用 `scripts/sop/bootstrap record Bx --status passed --evidence "<證據>"` 記錄。**沒有證據不得記為 passed。**
8. **完成。** 執行 `scripts/sop/bootstrap finalize`。它只在 B1–B7 都完成時把 `ready` 設為 `true`，並跑一次 `sop-ready`。
9. **開 PR。** 執行 `python3 scripts/sop/config.py --git-identity` 設定 commit 作者（設定已經寫好，所以現在可以用），commit、推送 `sop/bootstrap`，開 PR 到 `main`，指派給 `owner.github`。PR 說明列出完整設定與 B1–B7 的證據。CI 跑過一次之後，請 Owner 完成 `setup.md` 第 7 步（必要檢查），再合併。**只有 Owner 合併。**

> **EN:** (1) Confirm the machine-account identity and branch `sop/bootstrap` from `main`. (2) Walk the Owner through `setup.md` steps 1–6 and 8–10 (step 7 after CI has run once). (3) Ask every field in schema order; read `template_repository` and the bot's user ID from the API and have the user confirm; give the 2–3 guidance for `max_parallel` without choosing; disabling a check needs a reason and a decision ID. (4) Write the confirmed answers as JSON with `bootstrap write`. (5) Gather stack, rules, directories and commands as notes and run `bootstrap apply --notes`. (6) Help write `scripts/sop/test` with at least one smoke test and run it. (7) Run `bootstrap check`; verify what it can't read with your tools or an Owner screenshot under `docs/evidence/bootstrap/`, and `bootstrap record` it; never record passed without evidence. (8) `bootstrap finalize`. (9) Run `python3 scripts/sop/config.py --git-identity` (the config now exists), commit, push `sop/bootstrap`, and open a PR to `main` assigned to the Owner with the full config and the B1–B7 evidence; after CI has run once, the Owner does `setup.md` step 7, then merges.

## 不要做 / Don't

- 不要替使用者選任何值，也不要「先填一個之後再改」。
- 不要手動修改 `.sop/config.yml` 或 `.sop/bootstrap.yml`；一律透過 `scripts/sop/bootstrap`。
- 不要修改範本擁有的路徑（`.sop/managed.txt`）。啟動 PR 只能刪除關閉的模組的檔案（CI `path-scope`）。
- 不要合併啟動 PR。

> **EN:** Never pick a value for the user or fill one in "for now"; never hand-edit `.sop/config.yml` or `.sop/bootstrap.yml`; never change template-owned paths (the bootstrap PR may only delete disabled modules' files); never merge the bootstrap PR.
