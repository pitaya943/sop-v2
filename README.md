# sop-v2

一個通用的專案範本：讓一個 Chief of Staff session 帶著多個 Builder 和 Verifier subagent 平行開發，由人類 Owner 只負責決策。範本不含任何產品內容，也不綁定程式語言。

A general-purpose project template: one Chief of Staff session leads multiple Builder and Verifier subagents developing in parallel, while a human Owner only makes decisions. The template contains no product content and isn't tied to any programming language.

> **狀態 / Status：設計階段。** 目前 repo 只有設計文件，範本本身（`copier.yml`、`template/`）還沒實作，所以下面的「套用範本」步驟**還不能使用**，要等 `v2.0.0` 發布。進度見 [設計文件第 19 節](docs/design/sop-v2-design.md#19-實作計畫)。
>
> **Design phase.** This repo currently holds only the design document; the template itself (`copier.yml`, `template/`) isn't implemented yet, so the "Use the template" steps below **don't work yet** and will from `v2.0.0`. See [design doc section 19](docs/design/sop-v2-design.md#19-實作計畫) for progress.

## 它提供什麼 / What you get

- **四個角色：** Owner（人）、Chief of Staff、Builder、Verifier，各自的權限邊界都有對應的機器檢查。
- **平行開發規則：** ticket 宣告依賴、可修改的路徑和序列化資源；Chief 依此排出不會互相衝突的批次。
- **CI 防護：** Builder 只能改自己範圍內的檔案、不能削弱測試、沒有證據不算完成。
- **與技術棧無關：** 專案只需提供一支能輸出 JUnit XML 的測試腳本。
- **啟動閘門：** 所有必要資訊都填好、repo 設定都驗證過，才能開始開發。

&nbsp;

- **Four roles:** Owner (human), Chief of Staff, Builder, Verifier, each with permission boundaries backed by machine checks.
- **Parallel-development rules:** tickets declare dependencies, allowed paths and serialized resources; the Chief schedules batches that can't collide.
- **CI guards:** Builders can change only files in scope, can't weaken tests, and nothing counts as done without evidence.
- **Stack-neutral:** a project only has to provide one test script that writes JUnit XML.
- **Bootstrap gate:** development can't start until every required value is filled in and the repo settings are verified.

完整設計見 [`docs/design/sop-v2-design.md`](docs/design/sop-v2-design.md)。/ Full design: [`docs/design/sop-v2-design.md`](docs/design/sop-v2-design.md).

## 套用範本 / Use the template

本範本只能用 [Copier](https://copier.readthedocs.io/) 套用。**請不要用 GitHub 的「Use this template」或直接複製檔案**：那樣會拿到未填值的範本檔，啟動閘門也會擋住後續開發。

This template is applied only with [Copier](https://copier.readthedocs.io/). **Don't use GitHub's "Use this template" or copy files by hand**: you'd get unfilled template files, and the bootstrap gate would block development.

### 1. 事前準備 / Prerequisites

| 項目 | 說明 |
| --- | --- |
| 兩個 GitHub 帳號 | 你自己的帳號（Owner），以及一個給 agent 使用的**機器帳號**。兩者不能相同。 |
| 新的空 repo | 在 GitHub 建立，由 Owner 擁有。 |
| Python 3.9+ 與 Copier | `pipx install copier` |
| Claude Code | 已連接機器帳號的 GitHub，且 Claude GitHub App 已安裝在新 repo 上。 |

| Item | Notes |
| --- | --- |
| Two GitHub accounts | Your own (the Owner) and a **machine account** for agents. They must differ. |
| A new empty repo | Created on GitHub, owned by the Owner. |
| Python 3.9+ and Copier | `pipx install copier` |
| Claude Code | Connected to GitHub as the machine account, with the Claude GitHub App installed on the new repo. |

### 2. 產生專案 / Generate the project

```bash
copier copy --vcs-ref v2.0.0 <這個 repo 的網址 / this repo's URL> my-project
```

Copier 會逐一詢問所有注入點。**每一題都沒有預設值，必須自己回答**，包括：專案名稱與目標、Owner 和機器帳號、文件語言、平行上限、唯讀路徑、序列化資源、只增檔案、敏感領域，以及每個可選模組要開或關。完整清單見設計文件第 14.2 節。

Copier asks every injection-point question. **None has a default; you must answer each one**, including the project name and goal, the Owner and machine accounts, the doc language, the parallel cap, read-only paths, serialized resources, append-only files, sensitive areas, and whether each optional module is on or off. Full list: design doc section 14.2.

### 3. 推送並設定 repo / Push and configure the repo

```bash
cd my-project
git init -b main
git add -A
git commit -m "Generate from sop-v2"
git remote add origin <新 repo 的網址 / new repo URL>
git push -u origin main
```

接著在 GitHub 上完成這些設定（範本無法用檔案帶入）：

1. 把機器帳號加為 collaborator，權限 **Write**（不是 Admin）。
2. 為 `main` 建立 ruleset：機器帳號不能直接更新，只有 Owner 能合併。
3. 為 `milestone/*` 建立 ruleset：必須透過 PR，且 CI 必須全綠。
4. 如果開啟了 `@claude` review 模組，新增它需要的 repo secret。

Then configure these on GitHub (files can't carry them):

1. Add the machine account as a collaborator with **Write** (not Admin).
2. Create a ruleset for `main`: the machine account can't update it; only the Owner merges.
3. Create a ruleset for `milestone/*`: changes must go through a PR, and CI must be green.
4. If you enabled the `@claude` review module, add the repo secret it needs.

### 4. 實作測試介面 / Implement the test interface

範本附的 `scripts/sop/test` 預設會失敗。請改成執行你的測試並輸出 `build/sop/junit.xml`，規格見設計文件第 10.2 節。

The shipped `scripts/sop/test` fails by default. Change it to run your tests and write `build/sop/junit.xml`; see design doc section 10.2.

### 5. 通過啟動閘門 / Pass the bootstrap gate

在新 repo 開一個 Claude Code session（登入機器帳號），請它執行 `bootstrap-project` skill。它會逐項檢查身分、權限、ruleset、測試介面等設定，並開一個 PR 到 `main`。

**由 Owner 審查並合併這個 PR 後，閘門才會打開**，之後才能用 `plan-milestone` 開始第一個 milestone。

Open a Claude Code session on the new repo (signed in as the machine account) and ask it to run the `bootstrap-project` skill. It checks identity, permissions, rulesets, the test interface and more, then opens a PR to `main`.

**The gate opens only after the Owner reviews and merges that PR**; only then can `plan-milestone` start the first milestone.

## 更新到新版範本 / Updating to a newer template

```bash
git checkout -b sop/update-<新版本 / new version>
copier update --vcs-ref <新版本 / new version>
```

新版本如果新增了注入點，Copier 會要求你回答，同樣沒有預設值。更新會改到唯讀檔案（例如 `AGENTS.md`、`docs/sop/`），所以請開 PR 由 Owner 審查合併。要退回舊版時，用 `copier update --vcs-ref <舊版本 / old version>`。

If the new version adds injection points, Copier asks you to answer them, again with no defaults. Updates touch read-only files (such as `AGENTS.md` and `docs/sop/`), so open a PR for the Owner to review and merge. To roll back, run `copier update --vcs-ref <old version>`.

## 會寫進你專案的資訊 / What gets written into your project

產生的專案會把你的答案存在 `.copier-answers.yml` 和 `.sop/config.yml`，包括 Owner 與機器帳號的 GitHub 名稱。如果你的專案是公開的，這些值也會公開。範本 repo 本身不含任何個人資訊。

The generated project stores your answers in `.copier-answers.yml` and `.sop/config.yml`, including the Owner's and machine account's GitHub names. If your project is public, these values are public too. The template repo itself contains no personal data.

## 為什麼這個 repo 不是 GitHub template repository / Why this isn't a GitHub template repository

GitHub 的「Use this template」只會原樣複製檔案：不會詢問問題，也不會填值，無法保證「所有資訊都選好才開工」。而且之後範本改進時，用這種方式建立的專案也拿不到更新。所以本 repo 只支援 Copier（設計文件決策 D2、D7）。

GitHub's "Use this template" copies files as-is: it asks no questions and fills in no values, so it can't guarantee that everything is chosen before work starts, and projects created that way never receive later template improvements. This repo therefore supports Copier only (design decisions D2 and D7).

## 授權 / License

尚未決定（設計文件第 20 節）。/ Not yet chosen (design doc section 20).
