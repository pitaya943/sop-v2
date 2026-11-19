# 護欄設定教學 / Setting up the guardrails

這份文件一步一步教 Owner 在 GitHub 上設定 sop-v2 需要的護欄：機器帳號、權限、ruleset、必要檢查、標籤與通知。這些是 GitHub 的設定，不是檔案，所以範本無法替你完成；`bootstrap-project` 會逐項查證（B1–B7，見 [`bootstrap.md`](bootstrap.md)），但設定本身要由 Owner 在網頁上操作。

為什麼需要：整個協作模式的安全性靠「機器帳號不能更新 `main`」與「CI 檢查每個 PR」。只要其中一項沒設好，所有防護就只剩 agent 的自律。

> **EN:** A step-by-step guide for the Owner to set up the GitHub side of sop-v2: the machine account, permissions, rulesets, required checks, labels and notifications. These are GitHub settings, not files, so the template can't do them for you; `bootstrap-project` verifies each one (B1–B7), but the Owner makes the changes in the web UI. Why it matters: the model's safety rests on "the machine account can't update `main`" and "CI checks every PR"; if either is missing, only the agents' good behaviour is left.

## 0. 總覽 / Overview

| 步驟 | 設定 | 查證 |
| --- | --- | --- |
| 1 | 建立機器帳號，開啟 email 隱私 | B1 |
| 2 | 從範本建立 repo | — |
| 3 | 邀請機器帳號為 Write collaborator | B2 |
| 4 | Actions 的權限 | — |
| 5 | `main` 的 ruleset | B3、B4 |
| 6 | `milestone/**` 的 ruleset | — |
| 7 | 必要檢查（第一次 CI 跑完之後） | B4 |
| 8 | 合併方式 | — |
| 9 | 標籤與通知 | — |
| 10 | 模組需要的 secret | B6 |

> **EN:** Steps: (1) machine account with email privacy (B1); (2) create the repo from the template; (3) invite the machine account with Write (B2); (4) Actions permissions; (5) the `main` ruleset (B3, B4); (6) the `milestone/**` ruleset; (7) required checks after CI has run once (B4); (8) merge methods; (9) labels and notifications; (10) module secrets (B6).

## 1. 機器帳號 / The machine account

所有 agent 都以這個帳號操作 GitHub（`bot.github`）。它必須是**另一個** GitHub 帳號，不能是 Owner 自己（`owner.github`）。

1. 用一個只給這個用途的 email 註冊新的 GitHub 帳號，開啟兩步驟驗證。
2. 用機器帳號登入 → **Settings → Emails**：
   - ✅ **Keep my email addresses private**：網頁上的 git 操作（例如合併 PR）改用 GitHub 的 noreply 位址（網域是 `users.noreply.github.com`）。**沒開的話，機器帳號合併 PR 時，真實 email 會永遠留在 git 歷史裡**，只能改寫歷史才能清除。
   - ✅ **Block command line pushes that expose my email**。
3. 記下機器帳號的數字 ID（`bot.github_id`），例如執行 `gh api users/<機器帳號> --jq .id`，或在 GitHub REST API 的「取得使用者」回應中看 `id` 欄位。
4. 讓 agent 的 session 以這個帳號登入（各工具的做法見 [`dispatch.md`](dispatch.md#5-目前的工具對應--current-tool-mapping)）。

> **EN:** Every agent acts on GitHub as this account (`bot.github`), which must be a different account from the Owner's. Register it with a dedicated email and 2FA. In its Settings → Emails, turn on "Keep my email addresses private" (otherwise its real email is baked into git history whenever it merges on the web) and "Block command line pushes that expose my email". Note its numeric ID (`bot.github_id`) from the users API. Sign the agent sessions in as this account.

## 2. 從範本建立 repo / Create the repo

在 sop-v2 的頁面按 **Use this template → Create a new repository**。新的 repo 從一個全新的 commit 開始，不帶範本的 git 歷史。

> **EN:** On the sop-v2 page, choose Use this template → Create a new repository. The new repo starts from a fresh commit without the template's history.

## 3. 邀請機器帳號 / Invite the machine account

1. Owner：repo 的 **Settings → Collaborators → Add people**，輸入機器帳號，角色選 **Write**。
2. 機器帳號：到通知或 email 接受邀請。

**不要給 Admin 或 Maintain。** Admin 可以修改 ruleset，也可能落在 ruleset 的 bypass 名單裡，整個防護就失效了。

> **EN:** Add the machine account under Settings → Collaborators with the **Write** role, and accept the invitation as the machine account. Never give it Admin or Maintain: admins can change rulesets and may fall into a bypass list.

## 4. Actions 的權限 / Actions permissions

**Settings → Actions → General**：

- **Actions permissions**：允許 GitHub Actions（至少允許 GitHub 官方的 actions）。
- **Workflow permissions**：選 **Read repository contents and packages permissions**。範本的 workflow 會在需要的 job 自己宣告額外的權限（例如 `commit-author` 只多要 `pull-requests: read`）。
- ❌ 不要勾 **Allow GitHub Actions to create and approve pull requests**。

> **EN:** Under Settings → Actions → General: allow GitHub Actions; set workflow permissions to read-only (the template's jobs request anything extra themselves, e.g. `commit-author` adds only `pull-requests: read`); and leave "Allow GitHub Actions to create and approve pull requests" off.

## 5. `main` 的 ruleset / The ruleset for `main`

**Settings → Rules → Rulesets → New ruleset → New branch ruleset**：

| 欄位 | 設定 | 為什麼 |
| --- | --- | --- |
| Ruleset name | `protect-main` | — |
| **Enforcement status** | **Active** | 選 **Evaluate** 時規則只會記錄、不會阻擋，機器帳號仍然可以合併 `main`。這是最常見的設定錯誤 |
| **Bypass list** | 只加 **你自己**（Owner），模式選 **For pull requests only** | 開啟「Restrict updates」後，只有 bypass 名單上的人能更新 `main`，所以 Owner 必須在名單上。機器帳號**絕對不能**在名單上；若改用「Repository admin」角色，要確認機器帳號不是 Admin |
| Target branches | **Include default branch** | — |
| ✅ Restrict creations、Restrict updates、Restrict deletions | 開啟 | 只有 bypass 名單上的人能更新或刪除 `main` |
| ✅ Require a pull request before merging | 開啟；Required approvals 可以是 0 | 所有變更都經過 PR，CI 才會執行 |
| ✅ Block force pushes | 開啟 | 歷史不能被改寫 |
| ✅ Require status checks to pass | 第一次 CI 跑完之後再設定（第 7 步） | — |

**Owner 怎麼合併（重要）：** 因為「Restrict updates」只允許 bypass 名單更新 `main`，**Owner 每次合併都是在使用 bypass**。合併頁面會出現 **Merge without waiting for requirements to be met (bypass rules)** 的勾選框。正確的做法是：

> **先確認所有 sop-guards 的檢查都是綠的，再勾選 bypass，然後合併。**

這代表必要檢查擋得住其他人，但擋不住 Owner；「CI 通過才合併」對 Owner 來說是紀律，不是系統強制。機器帳號不在 bypass 名單上，所以完全被擋住（B3）。

> **EN:** Create a branch ruleset named `protect-main`: Enforcement **Active** (Evaluate only logs, the most common mistake); bypass list **only you**, mode "For pull requests only" (with Restrict updates, only bypass actors can update `main`, so the Owner must be on it, and the machine account must never be); target the default branch; turn on Restrict creations, updates and deletions, Require a pull request (0 approvals is fine), and Block force pushes; add required status checks in step 7. **How the Owner merges:** with Restrict updates, every Owner merge is a bypass merge, and the merge page offers "Merge without waiting for requirements to be met (bypass rules)". Confirm every sop-guards check is green first, then tick it and merge. Required checks therefore bind everyone except the Owner; for the Owner, "green before merge" is discipline. The machine account, not on the list, is fully blocked (B3).

## 6. `milestone/**` 的 ruleset / The ruleset for `milestone/**`

再建立一個 branch ruleset：

| 欄位 | 設定 |
| --- | --- |
| Ruleset name | `protect-milestones` |
| Enforcement status | **Active** |
| Bypass list | 空 |
| Target branches | **Include by pattern**：`milestone/**` |
| ✅ Restrict deletions、✅ Block force pushes | 開啟 |
| Require a pull request、Require status checks | **不要開** |

為什麼不要求 PR 與必要檢查：Chief 會把紀錄（看板、ticket、決策、報告）直接推送到 milestone 分支（D22，與參考專案相同）。Ticket PR 合併前由 Chief 確認 CI 全綠且 Verifier PASS；最後一道機器把關是 `main` 的必要檢查，以及 Owner 對 milestone PR 的審查。

> **EN:** A second ruleset, `protect-milestones`, Active, empty bypass list, targeting `milestone/**`, with Restrict deletions and Block force pushes only. Don't require PRs or status checks: the Chief pushes its records directly to milestone branches (D22, as in the reference harness). The Chief confirms green CI and a PASS before merging ticket PRs; the last machine gate is `main`'s required checks plus the Owner's milestone review.

## 7. 必要檢查 / Required status checks

GitHub 只會列出**最近 7 天內跑過**的檢查，所以要等 `sop-guards` 第一次執行之後才能加（啟動 PR 就會觸發它）。回到 `protect-main` → **Require status checks to pass** → **Add checks**，逐一加入以下名稱，來源選 **GitHub Actions**（指定來源可以防止別的 app 用同名的狀態冒充）：

```text
sop-ready
branch-ticket
readonly-paths
path-scope
append-only
serial-resource
evidence
commit-author
tests
no-weakened-tests
done-when
```

- 建議勾選 **Require branches to be up to date before merging**：PR 必須包含最新的 `main` 並重新通過 CI，避免兩個各自通過的 PR 合併後才出錯。
- 停用的檢查（`overrides.disabled_guards`）不用從清單移除：它的 job 會回報「已停用」並通過。
- 開啟 `modules.docs_lint` 時，想讓文件連結檢查也擋住合併，可以再加入 `docs-lint`。
- 名稱改了或 workflow 被刪除時，PR 會一直等一個不會出現的檢查。這時回到 ruleset 移除或修改那一項。

> **EN:** GitHub lists only checks that ran in the last 7 days, so add them after `sop-guards` has run once (the bootstrap PR triggers it). In `protect-main` → Require status checks → Add checks, add the eleven names above with source **GitHub Actions** (so no other app can impersonate them). Turn on "Require branches to be up to date". Disabled checks stay listed; their job reports "disabled" and passes. If a name changes or the workflow is removed, PRs wait forever; fix the list in the ruleset.

## 8. 合併方式 / Merge methods

**Settings → General → Pull Requests**：保留 **Allow merge commits**。Chief 用 merge commit 把 ticket PR 合併進 milestone 分支，`commit-author` 以 GitHub 帳號判斷作者，所以機器帳號建立的 merge commit 會通過；squash 或 rebase 會讓 commit 的對應關係更難追溯。

> **EN:** Keep "Allow merge commits" under Settings → General → Pull Requests. The Chief merges ticket PRs with merge commits; `commit-author` judges by GitHub account, so the machine account's merge commits pass, and squash or rebase would make commits harder to trace.

## 9. 標籤與通知 / Labels and notifications

1. **Issues → Labels → New label**，建立 `needs-owner` 與 `plan-approval`。Issue 樣板只會套用已經存在的標籤。
2. Owner：在 repo 頁面按 **Watch → All Activity**（或 Custom 勾選 Issues 與 Pull requests）。機器帳號開的 issue 與 PR 才會通知你；這是 agent 找你的唯一管道。

> **EN:** Create the `needs-owner` and `plan-approval` labels (issue templates only apply labels that exist). As the Owner, Watch the repo (All Activity, or Custom with Issues and Pull requests): issues and PRs from the machine account are the agents' only way to reach you.

## 10. 模組需要的 secret / Module secrets

只有開啟 `modules.claude_review` 時才需要：**Settings → Secrets and variables → Actions → New repository secret**，名稱是 `ANTHROPIC_API_KEY`，值是 Anthropic 的 API key。之後在 PR 留言提及 `@claude` 就會請 Claude 審查；只有 collaborator 的留言會觸發。這個審查只是參考，**不取代 Verifier，也不是合併的條件**。`bootstrap-project` 只檢查名稱存在（B6），不會讀取值。

> **EN:** Only with `modules.claude_review` on: add the repository secret `ANTHROPIC_API_KEY` (an Anthropic API key) under Settings → Secrets and variables → Actions. Mentioning `@claude` in a PR comment then asks Claude for a review; only collaborators' comments trigger it. The review is advisory: it never replaces the Verifier and is never a merge condition. Bootstrap checks only that the name exists (B6), never the value.

## 11. 疑難排解 / Troubleshooting

| 症狀 | 原因 | 修法 |
| --- | --- | --- |
| 機器帳號合併了 `main` | Enforcement 是 Evaluate；或機器帳號在 bypass 名單；或它是 Admin 而名單有「Repository admin」 | 改成 Active；從名單移除；把角色降為 Write。到 **Settings → Rules → Insights** 找那次合併的紀錄確認原因 |
| Owner 無法合併 PR，也沒有 bypass 勾選框 | Owner 不在 bypass 名單，而 Restrict updates 擋住所有人 | 把自己加進 bypass 名單，模式 For pull requests only |
| 必要檢查一直顯示 `Expected — Waiting for status to be reported` | 名稱拼錯，或來源不是 GitHub Actions，或 workflow 沒有執行 | 名稱必須與 job 名稱完全相同；來源選 GitHub Actions；確認 Actions 已開啟 |
| `Add checks` 找不到檢查 | 這個檢查最近 7 天沒跑過 | 先開一個 PR 讓 `sop-guards` 跑一次 |
| 機器帳號的真實 email 出現在 commit 歷史 | 第 1 步的 email 隱私沒開 | 開啟它（只影響之後的操作）；已經在歷史裡的只能改寫歷史清除 |

> **EN:** The machine account merged `main`: enforcement is Evaluate, it's on the bypass list, or it's an Admin covered by a role bypass (check Settings → Rules → Insights). No bypass checkbox for the Owner: add yourself to the bypass list. A check stuck at "Expected": wrong name, wrong source, or Actions not running. A check missing from "Add checks": it hasn't run in 7 days. The machine account's real email in history: turn on email privacy; past commits can only be fixed by rewriting history.
