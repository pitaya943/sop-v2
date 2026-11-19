---
name: sop-sync
description: "把專案更新到範本的另一個版本（或回滾到前一版），新增的設定欄位逐題詢問，完成後開 sync PR 給 Owner 合併。由 Owner 開的單次 session 使用。/ Update the project to another template version (or roll back), ask for any new config fields, and open a sync PR for the Owner to merge."
---

# 同步範本 / Sync the template

更新的規則在 [`docs/sop/sync.md`](../../../docs/sop/sync.md)。確定性的步驟交給 `scripts/sop/sync` 與 `scripts/sop/bootstrap`；你負責說明、詢問與開 PR。

這個 skill 可以在 `.sop/bootstrap.yml` 的 `ready` 不是 `true` 時使用（新版新增欄位時，閘門會暫時關上）。

> **EN:** The rules are in `docs/sop/sync.md`. `scripts/sop/sync` and `scripts/sop/bootstrap` do the deterministic work; you explain, ask and open the PR. This skill may run while `ready` isn't `true` (a new version that adds fields closes the gate until they're answered).

## 步驟 / Steps

1. 讀 `.sop/bootstrap.yml`（記下 `ready` 的狀態）與 `.sop/config.yml`。依 `AGENTS.md`「GitHub 身分」確認登入帳號，並執行 `python3 scripts/sop/config.py --git-identity`。
2. 問 Owner 要更新到哪一個版本（tag，例如 `v2.1.0`）。說明目前的版本（`.sop/version`），並請 Owner 先讀該版本的 release notes：特別是有沒有新增設定欄位、有沒有改變檢查。
3. 從 `main` 開 `sop/sync-<tag>` 分支，執行 `scripts/sop/sync <tag>`（來源預設是 `template.source`）。
4. 讀它的輸出，向 Owner 摘要：更新了哪些檔案、移除了哪些、哪些模組因為關閉而略過。
5. **新增的欄位：** 輸出列出的每一個欄位，依 `bootstrap-project` 的互動原則逐題詢問（一次一題、不得替使用者填入、立刻驗證），確認後用 `scripts/sop/bootstrap write <answers.json>` 寫入。
6. 執行 `python3 scripts/sop/guards.py sop-ready`。只有新欄位造成的失敗可以在這個 PR 解決；其他失敗要先停下來告訴 Owner。
7. commit、推送，開 PR 到 `main`，指派給 `owner.github`。PR 說明寫明：從哪個版本到哪個版本、release notes 的重點、更新與移除的檔案、新欄位的答案。**只有 Owner 合併。**

> **EN:** (1) Read the gate state and config; confirm identity and run `--git-identity`. (2) Ask the Owner which tag, state the current version, and have them read that release's notes (new fields? changed checks?). (3) Branch `sop/sync-<tag>` from `main` and run `scripts/sop/sync <tag>`. (4) Summarize what was updated, removed, or skipped for disabled modules. (5) Ask each new field one at a time under the bootstrap rules and write the answers with `bootstrap write`. (6) Run `sop-ready`; only failures from new fields may be fixed here, anything else stops and goes to the Owner. (7) Commit, push, and open a PR to `main` assigned to the Owner with the versions, release-note highlights, file changes and new answers. Only the Owner merges.

## 回滾 / Rolling back

同樣的步驟，版本換成前一個 tag。新版新增、舊版沒有的欄位會從設定中移除。

> **EN:** Same steps with the previous tag. Fields that only the newer version had are dropped from the config.

## 不要做 / Don't

- 不要手動修改範本擁有的檔案來「修正」同步結果；有問題就停下來，回報給 Owner，必要時回饋到範本。
- 不要在 sync PR 夾帶其他變更（CI `path-scope` 只允許範本擁有的路徑、`AGENTS.md`、`.sop/config.yml`）。
- 不要替新欄位填預設值。
- 不要合併 sync PR。

> **EN:** Don't hand-edit template-owned files to "fix" a sync (stop, tell the Owner, feed it back to the template); don't carry other changes in the sync PR (`path-scope` allows only template paths, `AGENTS.md` and `.sop/config.yml`); don't default new fields; don't merge the sync PR.
