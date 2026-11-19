# 範本更新與客製化 / Template updates and customization

專案從範本建立後，要能依自己的需要客製化，又能在範本改進時取得更新。本檔說明兩者怎麼共存。

> **EN:** Projects customize the template and still receive its improvements. This file explains how both coexist.

## 1. 誰擁有哪些檔案 / Who owns what

| 擁有者 | 檔案 | `sop-sync` 時 |
| --- | --- | --- |
| **範本** | `.sop/managed.txt` 列出的路徑：`.sop/schema.json`、`.sop/version`、`scripts/sop/`（`scripts/sop/test` 除外）、`docs/sop/`、`.claude/skills/` 的範本 skill、`.github/` 的範本 workflow 與樣板 | 覆寫 |
| **範本與專案共用** | `AGENTS.md`：專案段落（`<!-- sop:project:begin -->` 與 `<!-- sop:project:end -->` 之間）屬於專案，其餘屬於範本 | 只更新範本段落 |
| **專案** | `.sop/config.yml`、`.sop/bootstrap.yml`、`scripts/sop/test`、`docs/board.md`、`docs/decisions.md`、`docs/pitfalls.md`、`docs/tickets/`、`docs/milestones/`、`docs/evidence/`、`docs/project/`、各個 `project/` 擴充目錄 | 不覆寫 |

> **EN:** Template-owned paths (listed in `.sop/managed.txt`) are overwritten by sync. `AGENTS.md` is shared: the marked project section belongs to the project, the rest to the template. Config, gate state, the test runner, records and project extensions are never overwritten.

## 2. 客製化層級 / Customization layers

客製化不能破壞兩件事：P2 的閘門，以及之後能用 `sop-sync` 取得更新。所以分成五層，越往下越強、代價也越高：

| 層 | 能改什麼 | 放在哪裡 | 會不會被 `sop-sync` 覆寫 | 需要誰核准 |
| --- | --- | --- | --- | --- |
| **C1 設定值** | 帳號、語言、平行上限、唯讀路徑、序列化資源、模組開關 | `.sop/config.yml` | 不會 | 啟動時由 Owner；之後經 Owner 合併的 PR |
| **C2 專案規則** | 專案自己的規則、技術棧說明、指令、目錄約定 | `AGENTS.md` 的專案段落、`docs/project/**` | 不會 | Owner |
| **C3 擴充** | 專案專屬的 skill、額外的 CI 檢查、腳本 | `.claude/skills/project/**`、`.github/workflows/project-*.yml`、`scripts/project/**` | 不會 | Owner；擴充本身也是唯讀路徑，Builder 不能改 |
| **C4 停用範本規則** | 關掉某一項範本檢查 | `overrides.disabled_guards`，每項附原因與決策編號 | 不會 | Owner；`sop-ready` 檢查每項都有決策紀錄 |
| **C5 修改範本本身** | 改流程、角色、skill 的內容 | fork 範本，把 fork 設為 `template.source` | 會從 fork 同步 | fork 的維護者 |

原則：

- **先用低層：** 能用 C1–C3 解決的，不要用 C4、C5。
- **停用要留下紀錄：** C4 是寫進決策紀錄、有原因、可被審查的決定；`sop-ready` 會列出目前停用的檢查。
- **通用的改進回饋給範本：** 對所有專案都有用的客製化，應該回饋到範本，而不是留在單一專案。
- **C5 是逃生口：** 想要完全不同的流程時，fork 範本並把 `template.source` 指向自己的 fork。

> **EN:** Five layers, cheapest first: C1 config values; C2 project rules (the `AGENTS.md` project section, `docs/project/**`); C3 extensions under `project/` paths; C4 disabling a guard with a recorded decision; C5 forking the template and syncing from the fork. C1–C4 live in project-owned places, so sync never overwrites them. Prefer the lowest layer that works, record every disable, and send generally useful changes back to the template.

## 3. 更新流程：`sop-sync` / The update: `sop-sync`

1. 範本合併改進後打 semver tag（例如 `v2.1.0`），release notes 寫明是否新增設定欄位。
2. 專案中由 Owner 開一個 session 執行 `sop-sync` skill（不提供 workflow：用 `GITHUB_TOKEN` 開的 PR 不會觸發其他 workflow，必要檢查永遠不會出現）：
   - 從 `template.source` 抓指定 tag。
   - 用新版覆寫 `.sop/managed.txt` 列出的路徑，**只包含已開啟的模組**（`module:<name>` 標註）。
   - 更新 `AGENTS.md` 標記以外的範本段落。
   - 更新 `.sop/version`。
   - 新版 schema 若新增欄位，逐題詢問使用者，同樣沒有預設值。
   - 在 `sop/sync-<版本>` 分支開 PR。
3. PR 只能由 Owner 合併。

**回滾：** 用同一流程同步回前一個 tag。

**手動執行（不使用 Claude 時）：** 在 `sop/sync-<版本>` 分支執行下面的指令，依輸出回答新增的欄位（`scripts/sop/bootstrap write`），再 commit、推送並開 PR。

```bash
scripts/sop/sync v2.1.0
```

`scripts/sop/sync` 會覆寫範本擁有的路徑（只包含已開啟的模組）、移除新版不再列出的路徑、用新版的 `AGENTS.md` 重建範本段落並保留專案段落，並以新版的 `config.yml` 為底寫回既有的值；新版新增的欄位保持 `null`，`sop-ready` 會在回答之前失敗。它不 commit、也不推送。

**為什麼不需要三方合併：** 範本擁有的路徑在專案中是唯讀的（`readonly-paths`），專案不會改它們，所以直接覆寫不會蓋掉專案的修改。

> **EN:** The template tags releases. In the project, the Owner runs the `sop-sync` skill: fetch the tag from `template.source`, overwrite managed paths for enabled modules only, update the template sections of `AGENTS.md` and `.sop/version`, ask any new config questions (no defaults), and open a `sop/sync-<version>` PR for the Owner to merge. Roll back by syncing the previous tag. Without Claude, run `scripts/sop/sync <tag>` on a `sop/sync-<tag>` branch, answer any new fields with `scripts/sop/bootstrap write`, then commit, push and open the PR; the script never commits or pushes. No three-way merge is needed because managed paths are read-only in projects.

## 4. 開啟或關閉模組 / Turning a module on or off

1. 經 Owner 核准的 PR 修改 `modules.<name>`。
2. 執行 `sop-sync`：開啟時加入該模組的檔案，關閉時刪除。
3. 開啟 `claude_review` 時，B6 需要重新查證 repo secret。

> **EN:** Change `modules.<name>` through an Owner-approved PR, then run `sop-sync`, which adds or removes the module's files. Enabling `claude_review` requires re-checking B6.
