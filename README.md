# sop-v2

一個 harness 的 repo 範本：把「多個 agent 在人類監督下協作開發」的規則、角色、流程與機器檢查寫在一個 repo 裡。任何專案都能從它開始，依自己的需要客製化，並在範本改進時取得更新。

A repo template for a harness: the rules, roles, process and machine checks that let several agents develop under human supervision, packaged in one repo. Any project can start from it, customize it, and pick up template improvements later.

> **狀態 / Status：設計階段。** 目前 repo 只有設計文件，範本本身（`.sop/`、skills、檢查程式）還沒實作，所以下面的步驟**還不能使用**，要等 `v2.0.0` 發布。進度見 [設計文件第 19 節](docs/design/sop-v2-design.md#19-實作計畫)。
>
> **Design phase.** This repo currently holds only the design document; the template itself (`.sop/`, skills, guard scripts) isn't implemented yet, so the steps below **don't work yet** and will from `v2.0.0`. See [design doc section 19](docs/design/sop-v2-design.md#19-實作計畫).

## 它提供什麼 / What you get

- **四個角色：** Owner（人）、Chief of Staff、Builder、Verifier，各自的權限邊界都有對應的機器檢查。
- **平行開發規則：** ticket 宣告依賴、可修改的路徑和序列化資源；Chief 依此排出不會互相衝突的批次。
- **CI 防護：** Builder 只能改自己範圍內的檔案、不能削弱測試、沒有證據不算完成。
- **與技術棧無關：** 專案只需提供一支能輸出 JUnit XML 的測試腳本。
- **啟動閘門：** 所有必要資訊都填好、repo 設定都查證過，才能開始開發。
- **可客製化：** 五層客製化，專案特有的內容不會被範本更新蓋掉。

&nbsp;

- **Four roles:** Owner (human), Chief of Staff, Builder, Verifier, each with permission boundaries backed by machine checks.
- **Parallel-development rules:** tickets declare dependencies, allowed paths and serialized resources; the Chief schedules batches that can't collide.
- **CI guards:** Builders can change only files in scope, can't weaken tests, and nothing counts as done without evidence.
- **Stack-neutral:** a project only has to provide one test script that writes JUnit XML.
- **Bootstrap gate:** development can't start until every required value is filled in and the repo settings are verified.
- **Customizable:** five customization layers; project-specific content is never overwritten by template updates.

完整設計見 [`docs/design/sop-v2-design.md`](docs/design/sop-v2-design.md)。/ Full design: [`docs/design/sop-v2-design.md`](docs/design/sop-v2-design.md).

## 套用範本 / Use the template

### 1. 事前準備 / Prerequisites

| 項目 | 說明 |
| --- | --- |
| 兩個 GitHub 帳號 | 你自己的帳號（Owner），以及一個給 agent 使用的**機器帳號**。兩者不能相同。 |
| Claude Code | 用機器帳號連接 GitHub。沒有 Claude 也可以用備用腳本（見第 3 步）。 |

| Item | Notes |
| --- | --- |
| Two GitHub accounts | Your own (the Owner) and a **machine account** for agents. They must differ. |
| Claude Code | Connected to GitHub as the machine account. Without Claude, use the fallback script (step 3). |

不需要在本機安裝任何工具。/ Nothing needs to be installed locally.

### 2. 建立 repo / Create the repo

在本 repo 的 GitHub 頁面按 **Use this template → Create a new repository**，由 Owner 帳號建立。

On this repo's GitHub page, click **Use this template → Create a new repository**, as the Owner.

新 repo 一開始是「未啟動」狀態：`.sop/config.yml` 的欄位全部未填，CI 的 `sop-ready` 會失敗，任何開發都無法合併。這是刻意的。

The new repo starts "not bootstrapped": every field in `.sop/config.yml` is unset, CI's `sop-ready` fails, and no development can be merged. That's intentional.

### 3. 執行啟動流程 / Run the bootstrap

在新 repo 開一個 Claude Code session（登入機器帳號），說：

Open a Claude Code session on the new repo (signed in as the machine account) and say:

```text
Run the bootstrap-project skill.
```

它會**一次問一題**：專案名稱與目標、Owner 和機器帳號、文件語言、平行上限、唯讀路徑、序列化資源、只增檔案、敏感領域、要停用的檢查，以及每個可選模組要開或關。**每一題都沒有預設值**；它會說明選項和建議，但由你決定。

It asks **one question at a time**: project name and goal, Owner and machine accounts, doc language, parallel cap, read-only paths, serialized resources, append-only files, sensitive areas, guards to disable, and whether each optional module is on or off. **None has a default**; it explains the options and suggests values, but you decide.

每個答案都會**立刻查證**。例如機器帳號是否存在、是否有 Write 權限、`main` 的 ruleset 是否擋住它。不通過時，它會告訴你去哪個設定頁修正。

Each answer is **checked immediately**, for example whether the machine account exists, has Write access, and is blocked by the `main` ruleset. If a check fails, it tells you which settings page fixes it.

它也會協助你把 `scripts/sop/test` 接上你的測試，並移除只屬於範本的檔案（這份 README、LICENSE、設計文件等）。最後它會開一個啟動 PR。

It also helps you wire `scripts/sop/test` to your tests and removes template-only files (this README, the LICENSE, the design doc and so on). Finally it opens a bootstrap PR.

沒有 Claude 時，執行備用腳本，它會做同樣的格式驗證和可用 token 完成的查證：

Without Claude, run the fallback script, which does the same format validation and whatever checks a token allows:

```bash
python3 scripts/sop/bootstrap
```

### 4. 在 GitHub 上完成設定 / Configure GitHub

啟動流程會要求你完成這些設定（檔案無法帶入），並逐項查證：

The bootstrap asks you to complete these settings (files can't carry them) and verifies each:

1. 把機器帳號加為 collaborator，權限 **Write**（不是 Admin）。
2. 為 `main` 建立 ruleset：機器帳號不能直接更新，只有 Owner 能合併。
3. 為 `milestone/*` 建立 ruleset：必須透過 PR，且 CI 必須全綠。
4. 如果開啟了 `@claude` review 模組，新增它需要的 repo secret。

&nbsp;

1. Add the machine account as a collaborator with **Write** (not Admin).
2. Create a ruleset for `main`: the machine account can't update it; only the Owner merges.
3. Create a ruleset for `milestone/*`: changes must go through a PR, and CI must be green.
4. If you enabled the `@claude` review module, add the repo secret it needs.

### 5. 合併啟動 PR / Merge the bootstrap PR

**由 Owner 審查並合併啟動 PR 後，閘門才會打開**，之後才能用 `plan-milestone` 開始第一個 milestone。

**The gate opens only after the Owner reviews and merges the bootstrap PR**; only then can `plan-milestone` start the first milestone.

## 客製化 / Customizing

| 層 Layer | 改什麼 What | 放哪裡 Where |
| --- | --- | --- |
| C1 設定值 Config | 帳號、語言、平行上限、模組開關等<br>Accounts, language, parallel cap, modules | `.sop/config.yml` |
| C2 專案規則 Project rules | 技術棧、指令、專案規則<br>Stack, commands, project rules | `AGENTS.md` 的專案段落、`docs/project/`<br>Project section of `AGENTS.md`, `docs/project/` |
| C3 擴充 Extensions | 專案專屬 skill、CI、腳本<br>Project skills, CI, scripts | `.claude/skills/project/`、`.github/workflows/project-*.yml`、`scripts/project/` |
| C4 停用範本檢查 Disable a guard | 關掉不需要的檢查，需附原因和決策紀錄<br>Turn off a guard, with a reason and a decision record | `.sop/config.yml` 的 `overrides.disabled_guards` |
| C5 修改範本本身 Change the template | 流程、角色、skill 的內容<br>Process, roles, skill content | fork 本 repo，把 `template.source` 指向你的 fork<br>Fork this repo and point `template.source` at your fork |

C1–C4 都在專案擁有的位置，範本更新不會覆寫。能用低層解決的，就不要用高層。詳見設計文件第 14.6 節。

C1–C4 live in project-owned locations, so template updates never overwrite them. Prefer the lowest layer that works. See design doc section 14.6.

## 更新到新版範本 / Updating to a newer template

在專案中開一個 Claude session，執行 `sop-sync` skill 並指定版本。它會：

Open a Claude session in the project and run the `sop-sync` skill with a version. It:

- 用新版覆寫範本擁有的檔案（`docs/sop/`、範本 skills、`scripts/sop/` 等），只包含你開啟的模組。
- 新版若新增設定欄位，逐題詢問你，同樣沒有預設值。
- 開一個 PR 給 Owner 審查合併。

&nbsp;

- Overwrites template-owned files (`docs/sop/`, template skills, `scripts/sop/`, etc.) with the new version, enabled modules only.
- Asks you any new config questions, again with no defaults.
- Opens a PR for the Owner to review and merge.

要退回舊版，就同步回前一個版本。你的客製化（C1–C4）不會受影響。

To roll back, sync to the previous version. Your customizations (C1–C4) are unaffected.

## 會寫進你專案的資訊 / What gets written into your project

你的答案會存在 `.sop/config.yml`，包括 Owner 與機器帳號的 GitHub 名稱。如果你的專案是公開的，這些值也會公開。範本 repo 本身不含任何個人資訊。用「Use this template」建立的 repo 不包含本範本的 git 歷史。

Your answers are stored in `.sop/config.yml`, including the Owner's and machine account's GitHub names. If your project is public, these values are public too. The template repo itself contains no personal data, and repos created with "Use this template" don't include this template's git history.

## 授權 / License

[MIT-0（MIT No Attribution）](LICENSE)。你可以自由使用、複製、修改、散布本範本，包括商業用途；**不需要**在你的專案中保留本範本的著作權聲明或授權檔。本範本按現狀提供，不附任何擔保。

啟動流程會移除本範本的 `LICENSE`，你的專案要用什麼授權由你自己決定。唯一的例外：如果你開啟的可選模組內含第三方檔案，那些檔案的原始授權檔會放在該模組的資料夾中，必須保留。

[MIT-0 (MIT No Attribution)](LICENSE). You may use, copy, modify and distribute this template freely, including commercially, and you **don't** need to keep this template's copyright notice or license file in your project. The template is provided as is, without warranty.

The bootstrap removes this template's `LICENSE`; you choose your project's license. The one exception: if an optional module you enable contains third-party files, their original license files sit in that module's folder and must be kept.
