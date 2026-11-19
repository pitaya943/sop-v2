# SOP v2 設計文件

Chief of Staff 與 subagent 協作、平行開發的通用專案範本。草稿 v0.11，2026-11-19。

> **一句話：** 一個任何人都能拿來開新專案的範本。它定義「Chief 分派、Builder 實作、Verifier 獨立驗收、Owner 只做決策」的協作模式與平行開發規則，並用 CI 把角色之間的契約變成機器檢查。使用者在 GitHub 上按「Use this template」建立專案，再由一個 agent 引導的啟動流程逐項詢問、即時查證所有必要資訊；資訊不完整或查證不通過，就不能開始開發。範本本身不含任何個人或專案資訊。
>
> **EN:** A template anyone can use to start a project. It defines a collaboration model (the Chief dispatches, Builders build, Verifiers check independently, the Owner only decides) and parallel-development rules, with CI turning the contract between roles into machine checks. Users create a project with GitHub's "Use this template", then an agent-guided bootstrap asks for and live-checks every required value; development can't start until everything is complete and verified. The template carries no personal or project data.

## 目錄 / Contents

1. [範本定義](#1-範本定義)
2. [目標與非目標](#2-目標與非目標)
3. [來源](#3-來源)
4. [已定案的決策](#4-已定案的決策)
5. [角色與權限](#5-角色與權限)
6. [Milestone 與 ticket 的生命週期](#6-milestone-與-ticket-的生命週期)
7. [平行開發模式](#7-平行開發模式)
8. [角色的執行方式（dispatch）](#8-角色的執行方式dispatch)
9. [Ticket 契約](#9-ticket-契約)
10. [CI 契約](#10-ci-契約)
11. [記憶與狀態](#11-記憶與狀態)
12. [升級、修正輪與證據](#12-升級修正輪與證據)
13. [可選模組](#13-可選模組)
14. [發布、設定與更新](#14-發布設定與更新)
15. [啟動閘門](#15-啟動閘門)
16. [範本的個資衛生](#16-範本的個資衛生)
17. [Repo 結構](#17-repo-結構)
18. [失效情境與最壞影響](#18-失效情境與最壞影響)
19. [實作計畫](#19-實作計畫)
20. [待決問題](#20-待決問題)

---

## 1. 範本定義

**核心目的：** 把一套 harness（讓多個 agent 在人類監督下協作開發的規則、角色、流程與機器檢查）的概念與框架，寫成一個 GitHub repo template。之後任何專案（範本作者自己的，或其他使用者的）都能從它開始，依自己的需要**客製化**後進行開發，並在範本改進時取得更新。客製化的方式見第 14.6 節。

> **EN:** Core purpose: package a harness (the rules, roles, process and machine checks that let several agents develop under human supervision) as a GitHub repo template, so any project, the author's or anyone else's, can start from it, **customize** it, and still receive template updates. See section 14.6 for how customization works.

sop-v2 必須同時滿足兩個性質。之後的每個設計都要能回答「它怎麼維持這兩個性質」。

| 性質 | 定義 | 怎麼保證 |
| --- | --- | --- |
| **P1 可分享** | 範本 repo 內不含任何個人資訊：姓名、帳號、email、私人 repo、個人偏好、特定專案的內容。任何人拿到都能直接使用，不會看到或沿用別人的設定。 | 所有人和專案相關的值都是設定欄位，範本中一律未填（第 14 節）；範本 repo 的 CI 掃描個資樣式（第 16 節） |
| **P2 先完整，才開工** | 建立專案時，每一個設定欄位都必須被明確選定，**不提供預設值**。只要還有任何一項沒填、沒驗證，就不能開始開發。 | 三層啟動閘門：agent 引導的啟動流程（含即時查證）、repo 的 `sop-ready` CI 檢查、每個 skill 開頭的檢查（第 15 節） |

P2 的理由：協作模式的安全性依賴這些值（例如機器帳號決定誰能 commit、誰不能推 `main`）。一個「先用預設值、之後再改」的值，最常見的結局是從來沒被改，而錯的身分設定會讓所有防護失效。

> **EN:** Two properties. **P1 Shareable:** the template repo contains no personal data; every person- or project-specific value is a config field left unset in the template, and the template's own CI scans for personal-data patterns. **P2 Complete before start:** every config field must be chosen explicitly, with no defaults; development is blocked until all are filled and verified, via a three-layer bootstrap gate. Rationale: the model's safety depends on these values, and "use the default, change it later" usually means never changed.

## 2. 目標與非目標

**目標**

- **G1 協作模式可重用：** 角色、交接格式、狀態機、升級管道，在任何專案都一樣。
- **G2 平行開發安全：** 多個 Builder 同時工作時不互相覆寫；衝突在計畫階段排除，CI 是最後防線。
- **G3 契約可被機器檢查：** 「Builder 只能改自己的範圍」「不能弱化測試」「沒有證據不算完成」由 CI 判定，不靠 agent 自律。
- **G4 與技術棧無關：** 範本不假設語言、框架、資料庫；專案只需實作一個測試介面。
- **G5 可演進：** 範本改進後，既有專案能同步更新。
- **G6 = P1、G7 = P2**（第 1 節）。
- **G8 對新手友善：** 建立專案不需要在本機安裝任何工具；設定錯誤在當下就被指出，並告訴使用者怎麼修。

**非目標**

- 不含規格、產品程式、測試內容、資料庫 migration 的任何具體做法。
- 不取代 GitHub 的 repo 設定（ruleset、collaborator、secret）；範本只引導設定並驗證。
- 不做常駐的 orchestrator 服務：Chief 本身就是一個 Claude Code session。

> **EN:** Goals: reusable collaboration model; safe parallel development; machine-checkable contracts; stack-neutral; evolvable; P1 and P2; and G8 beginner-friendly (no local install to create a project; mistakes are caught on the spot with a fix). Non-goals: any product content; replacing GitHub repo settings; a standalone orchestrator service.

## 3. 來源

sop-v2 由兩個前身整理而來：一份以文件規範為主的單 session 範本（v1），以及一個在實戰中跑過多個 milestone 的參考專案。參考專案把 v1 發展成多 session、由 CI 強制執行的流程，平行上限 2–3 張 ticket，修正輪與升級都有紀錄。sop-v2 把參考專案拆成三層：

| 層 | 參考專案中的內容 | sop-v2 的處理 |
| --- | --- | --- |
| **A 協作模式** | Owner / Chief / Builder / Verifier 四角色、ticket 狀態機、兩輪修正後升級、用 issue 找 Owner、Chief 中斷後從 repo 接手 | 完整保留；人名、帳號、模型全部改成設定欄位 |
| **B 平行與防護** | `depends_on`、`allowed_paths`、migration 一次一張、同時上限、看板 / 決策 / 坑的紀錄、證據與模型署名、CI 檢查 | 保留並通用化：migration → **序列化資源**；CI 拆成與技術棧無關的檢查加一個 **JUnit XML 介面** |
| **C 專案內容** | 規格、產品程式、特定資料庫與測試框架、專案專屬的檢查與 skill | 全部刪除 |

> **EN:** sop-v2 consolidates a documentation-driven single-session template (v1) and a reference project that evolved it into a multi-session, CI-enforced process. Layer A is kept with every name, account and model turned into a config field; layer B is generalized; layer C is dropped.

## 4. 已定案的決策

| # | 問題 | 決定 | 後果 |
| --- | --- | --- | --- |
| D1 | 與 v1 的關係 | sop-v2 取代 v1；v1 的學習、`@claude` review、文件檢查收為可選模組 | 只維護一套範本 |
| D2 | 發布機制 | **GitHub template repository + agent 引導的啟動流程**（v0.5 改定，取代 Copier） | 使用者不需安裝工具；設定可即時向 GitHub 查證；更新改用 `sop-sync`（第 14 節） |
| D3 | 文件語言 | 專案選定（必填，無預設） | 範本自身文件只維護一份；語言設定決定專案產出（PR、issue、報告）的語言 |
| D4 | 機器帳號 | 設定欄位，必填，啟動時查證 | 見第 15 節 |
| D5 | 學習模組 | 可選模組，必須明確選開或關 | 見第 13 節 |
| D6 | 範本定義 | **P1 可分享、P2 先完整才開工** | 所有設定欄位無預設值；啟動閘門與範本個資掃描 |
| D7 | GitHub 的 template repository 設定 | **開啟**（v0.5 改定） | 「Use this template」是唯一的建立方式；P2 由啟動閘門保證，不靠建立工具 |
| D8 | 設計文件格式 | Markdown | 在 GitHub 上直接閱讀、diff 易讀 |
| D9 | 授權 | **MIT-0**，著作權人「sop-v2 contributors」 | 下游不需保留聲明；授權檔不含個人名字（P1）；保留免責條款。範本的 `LICENSE` 屬於「僅範本」檔案，啟動時移除，專案自行決定授權 |
| D10 | 範本自身的開發檔案 | **啟動時移除**（清單在 `.sop/template-only.txt`） | GitHub template 會複製整個 repo；設計文件、guards 的測試、範本自己的 CI、範本 README 與 LICENSE 由啟動流程刪除，`sop-ready` 確認已刪除 |
| D11 | 客製化方式 | **五層客製化 C1–C5**（第 14.6 節） | 專案特有的內容放在專案擁有的位置，不被 `sop-sync` 覆寫；停用範本檢查必須有決策紀錄 |
| D12 | 設定檔格式（S0） | **限制版 YAML 子集**，由 `scripts/sop/config.py` 自行解析與輸出 | 保留原生 `null`（TOML 沒有）與欄位旁的註解（JSON 沒有），只用標準函式庫；YAML 版本間有歧義的寫法（`yes`、`no`、`~`、`0123`、日期、`12:30`）一律報錯並提示加引號，不猜測 |
| D13 | Python 最低版本（S0） | **3.11**；自我 CI 測 3.11 與 3.13 | 3.10 已於 2026-10 停止支援；Ubuntu 22.04 內建 3.10 的使用者需另裝 Python |
| D14 | 測試依賴（S0） | **只用 pytest，鎖定版本**（`tests/sop/requirements.txt`） | 檢查程式本身仍只用標準函式庫；pytest 只在範本自己的測試中使用 |
| D15 | 範本歷史中已有一筆含機器帳號 email 的 merge commit（S0 發現） | **接受，不改寫歷史；改以設定防止再發生**：機器帳號開啟 email 隱私與「封鎖會暴露 email 的推送」，Owner 檢查 `main` 的 ruleset 不讓機器帳號合併 | 該 email 永久留在範本 repo 的歷史中；「Use this template」建立的專案不帶歷史，所以不影響下游（第 16 節）。PR 內的 commit 由 self CI 檢查作者；網頁合併產生的 merge commit 在 CI 之後才建立，只能靠帳號設定防範 |
| D16 | 範本內附文件的語言（S1） | **繁體中文本文，每節附 English 摘要**（與本設計文件相同） | 中文讀者與英文讀者都能使用；份量較大，兩種語言必須一起維護。專案產出的語言仍由 `doc_language` 決定 |
| D17 | Ticket front matter 的清單寫法（S1） | ~~逐行寫 `- 項目`~~ **已由 D23 取代** | — |
| D18 | 看板 `docs/board.md` 的格式（S1） | ~~固定欄位的 Markdown 表格（自訂欄位）~~ **已由 D24 取代** | — |
| D19 | 學習模組的紀錄位置（S1） | **獨立檔案 `docs/learning.md`**，不在 `docs/decisions.md` 加欄位 | 核心檔案的格式不隨模組開關改變；關閉模組只需刪檔（第 13 節已更新） |
| D20 | `AGENTS.md` 專案段落的標記（S1） | **`<!-- sop:project:begin -->` 與 `<!-- sop:project:end -->`**，各出現一次 | `sop-sync` 只更新標記以外的內容；標記一旦發布就不能改名 |
| D21 | harness 標準的來源（S1） | **對齊參考專案的 harness**：角色、流程、CI 規則、skill 步驟、紀錄格式都以參考專案為準，只把與其專案主題相關的部分通用化或刪除（第 3 節） | 範本不另創 harness 邏輯；與參考專案不同的地方必須是「通用化」並在本文件說明 |
| D22 | Chief 怎麼寫入紀錄（S1） | **Chief 直接推送到 `milestone/Mx`**（看板、ticket、決策、pitfalls、報告）；必要的 CI 檢查只設在 `main`，`milestone/*` 不設（參考專案 D-035、D-054）。CI 在推送到 `milestone/**` 與 `main` 時仍會執行 | 取代原本 B4「`milestone/*` 必須 PR、CI 全綠」。Ticket PR 合併進 milestone 的條件（CI 全綠、Verifier PASS、範圍內、唯讀路徑沒被改）由 Chief 確認；最後一道機器把關是 `main` 的必要檢查與 Owner 審查 |
| D23 | Ticket front matter 的清單寫法（S1，取代 D17） | **單行的 `[a, b]` 與逐行清單都可以**（參考專案寫 `depends_on: [T-010]`）；YAML 子集的 parser 支援只含純量的單行清單 | 巢狀、空項目、`]` 後面還有文字都會被拒絕 |
| D24 | 看板與報告的格式（S1，取代 D18） | **看板照參考專案：** 每個 milestone 一段（計畫 issue、順序、平行上限、各角色模型），下方一張表 `Ticket / Milestone / 標題 / 狀態 / PR / 修正輪數 / 備註`，各輪模型記在備註。**milestone 報告用 HTML**（`docs/milestones/report-template.html`） | S2 的看板 parser 依這張表解析 |
| D25 | 唯讀路徑的例外與證據規則（S1） | **照參考專案：** ticket 的 `allowed_paths` **明確列出**（不含萬用字元）某個唯讀路徑時，才允許修改它（參考專案 D-031），取代 `readonly_override`。證據一律必須提供；ticket 用 `screens: true / false` 標示是否需要截圖，沒有這個欄位判為失敗（參考專案 D-040），取代 `evidence: cli / screens / none` | Ticket 少一個欄位；不會有「不用附證據」的 ticket |
| D26 | 必要檢查的粒度（S2） | **每個檢查一個 job，job 名稱就是檢查名稱**（照參考專案）；`main` 的 ruleset 列出 11 個名稱 | 失敗時一眼看出是哪一項；名稱清單寫在 `docs/sop/setup.md`，由測試保證與程式一致 |
| D27 | 範本 repo 本身不執行專案的檢查（S2） | `sop-guards.yml` 的 `detect` job 看到僅範本檔案 `.github/workflows/self-ci.yml` 就跳過所有檢查 | job 層級的條件不能用 `hashFiles`；被跳過的 job 在 GitHub 上視為通過 |
| D28 | `no-weakened-tests` 的判斷方式（S2） | **只用測試結果比對**（目標分支通過的每個測試 ID，在 PR 上都必須被收集且通過），不保留參考專案的 pytest 語法掃描 | 與技術棧無關（G4）；專案需要語法掃描可以放在 C3 |
| D29 | `serial-resource` 的進行中資訊（S2） | 讀目標分支的 `docs/board.md`，狀態為 building、verifying、fixing 的 ticket，再讀它們的 `serial` | 參考專案沒有這項檢查，屬於範本的通用化；看板沒更新時會失準 |
| D30 | 停用的檢查與設定來源（S2） | 停用的檢查 job 照常執行，印出「已停用（D-xxx）」並通過；**ticket 與設定一律從目標分支讀取**，PR 無法停用自己的檢查或放寬自己的範圍 | 必要檢查的名稱清單不必隨停用而改 |
| D31 | 範本路徑唯讀與護欄教學（S2） | `readonly-paths` 包含 `.sop/managed.txt` 列出的所有範本路徑，ticket PR 不能修改評判自己的檢查程式；新增 `docs/sop/setup.md`，一步一步教 Owner 設定機器帳號、ruleset、必要檢查、標籤與通知 | 範本無法替使用者設定 GitHub；教學把 S0 實際踩過的問題（email 隱私、Evaluate 模式、bypass 合併方式）寫進去 |
| D32 | 範本的 README 與 LICENSE（S3，修正 S0 的設計錯誤） | `.sop/template-only.txt` 支援 `marker:<文字>` 條目：檔案可以是專案自己的版本，但不能仍是範本的版本 | 原本列為「必須不存在」，專案換上自己的 README 或授權後 `sop-ready` 永遠失敗 |
| D33 | 啟動的程式（S3） | `bootstrap-project` skill 與不用 Claude 時的備用腳本**共用** `scripts/sop/bootstrap`（`ask`、`write`、`apply`、`check`、`record`、`finalize`）；skill 負責對話與判斷，腳本負責確定性的步驟 | 會改檔案的邏輯只寫一份、只測一份 |
| D34 | 寫入設定的方式（S3） | **逐行替換 `null`，保留每個欄位旁的註解**，寫完重新解析確認一致 | 給新手的說明不會在寫入後消失 |
| D35 | 啟動腳本的範圍（S3） | 只改本機檔案並印出下一步，不推送、不開 PR；API 讀不到的查證以 Owner 的截圖記錄 | 腳本需要的權限最小 |
| D36 | `sop-sync` 的形式（S3） | **只有 skill 加腳本，不提供 workflow**（修改第 14.5 節） | 用 `GITHUB_TOKEN` 開的 PR 不會觸發其他 workflow，必要檢查永遠不會出現；改用 PAT 又多一個要管理的密鑰 |
| D37 | 啟動與 sync PR 的範圍（S3） | `path-scope` 限制：`sop/bootstrap` 不能修改範本擁有的路徑（只能刪除關閉的模組）；`sop/sync-*` 只能改範本擁有的路徑、`AGENTS.md`、`.sop/config.yml` | `ci-contract.md` 原本寫了這條規則，卻沒有東西執行 |
| D38 | `@claude` review 模組（S3） | **保留為可選模組**，預設由使用者在啟動時明確選擇（參考專案沒有這個功能，它來自 v1，D1、D5）。只在 PR 留言提及、且留言者是 collaborator 時觸發；使用 `anthropics/claude-code-action`，需要 secret `ANTHROPIC_API_KEY`（B6） | 只是參考：不取代 Verifier，也不是合併條件；多維護一個外部 action 的版本 |
| D39 | workflow 檔案的位置（S3，修正設計錯誤） | 模組的 workflow 是 `.github/workflows/module-*.yml`，專案額外的 CI（C3）是 `.github/workflows/project-*.yml`；`docs_lint` 模組用標準函式庫的 `scripts/sop/docs_lint.py` 檢查連結與錨點 | GitHub 只執行 `.github/workflows/` 第一層的檔案；原本設計的 `workflows/modules/`、`workflows/project/` 子目錄永遠不會被執行 |

**為什麼從 Copier 改成 template + agent 啟動（D2、D7）：** Copier 要求使用者在本機安裝 Python 與 Copier、在終端機一次回答十幾題，而且只能檢查**格式**，無法檢查**事實**（機器帳號是否存在、權限是否正確）。對不熟悉的使用者，這是最容易出錯、也最難排查的一步。本範本預設使用者使用 Claude Code，所以引導者可以直接是 agent：逐題詢問、即時查證、當場指出修正方法。設計早已把「範本擁有的檔案」與「專案的設定值」分開，幾乎不需要模板渲染，所以這個改變成本很低。

> **EN:** D1 replace v1; D2 (revised in v0.5) distribute as a GitHub template repository with an agent-guided bootstrap instead of Copier; D3 language is a required per-project choice; D4 the machine account is required and live-checked at bootstrap; D5 the learning module is optional and must be chosen; D6 P1 and P2; D7 (revised) template mode is on and "Use this template" is the only creation path, with P2 guaranteed by the gate rather than the creation tool; D8 Markdown docs; D9 MIT-0; D10 template-only development files are removed at bootstrap; D11 customization layers; D12 (S0) the config file is a restricted YAML subset parsed and written by our own stdlib code, keeping native null and comments while rejecting anything YAML versions read differently; D13 Python 3.11 minimum, CI on 3.11 and 3.13; D14 pytest as the only test dependency, pinned; D16 shipped template docs are Traditional Chinese with English summaries, like this document; D17 and D18 were superseded by D23 and D24; D19 the learning module writes to its own `docs/learning.md` rather than adding a column to the decision log; D20 the project section of `AGENTS.md` is delimited by `<!-- sop:project:begin -->` and `<!-- sop:project:end -->`; D21 the harness itself (roles, process, CI rules, skill steps, record formats) follows the reference project, with only its subject-specific parts generalized or dropped; D22 the Chief pushes its records directly to `milestone/Mx` and required CI checks are set only on `main` (replacing the old B4); D23 ticket lists may be one-line `[a, b]` or block lists; D24 the board follows the reference's per-milestone sections plus a `Ticket / Milestone / Title / State / PR / Fix rounds / Notes` table, and milestone reports are HTML; D25 a read-only path may be changed only when a ticket's `allowed_paths` names it exactly, and evidence is always required, with `screens: true / false` saying whether screenshots are needed; D26 one job per check, named after it; D27 a `detect` job skips every check in the template repo itself; D28 `no-weakened-tests` compares results only; D29 `serial-resource` reads in-progress tickets from the target branch's board; D30 disabled checks still run and pass with their reason, and tickets and config always come from the target branch; D31 template-managed paths are read-only, and `docs/sop/setup.md` teaches the Owner the GitHub-side setup; D32 `template-only.txt` marker entries let a project keep its own README and license (fixing an S0 bug); D33 the bootstrap skill and the no-Claude fallback share `scripts/sop/bootstrap`; D34 config values are written in place, keeping every comment; D35 the script changes local files only and never pushes; D36 `sop-sync` is a skill plus a script, with no workflow, because PRs opened with `GITHUB_TOKEN` don't trigger other workflows; D37 `path-scope` limits bootstrap and sync PRs to their own paths; D38 the `@claude` review stays an optional, advisory module (from v1, not in the reference), triggered only by collaborators' mentions; D39 module and project workflows are top-level `module-*.yml` and `project-*.yml` files, because GitHub ignores workflow subdirectories. D15 a merge commit already in the template's history carries the machine account's email: accepted, history not rewritten; prevented from recurring by the account's email-privacy settings and a ruleset that keeps the machine account from merging (projects created from the template don't inherit the history; merge commits are created after CI, so only settings can prevent them). Why drop Copier: it needs a local Python install, asks everything in one terminal pass, and can validate format but not facts. An agent can ask one question at a time, check answers against GitHub live, and explain the fix. Because template-owned files and project values were already separated, almost no templating is needed.

## 5. 角色與權限

| 角色 | 是誰 | 做什麼 | 不做什麼 | 生命週期 |
| --- | --- | --- | --- | --- |
| **Owner** | 人 | 核准 milestone 計畫、回答升級 issue、審查並合併 `milestone/* → main`、指定各角色的模型、核准啟動閘門與範本更新 | — | 永久 |
| **Chief of Staff** | 一個 Claude Code session | 切 ticket、排平行批次、開子 session、合併 ticket PR 進 milestone 分支、維護看板、寫 milestone 報告 | 不寫產品程式、不合併 `main` | 一個 milestone；中斷時由新 session 從 repo 接手 |
| **Builder** | 每張 ticket 一個全新 session | 先紅再綠、開 PR、附證據 | 不改唯讀路徑、不改範圍外檔案、不合併、不弱化測試 | 一張 ticket（含第一輪修正） |
| **Verifier** | 每個 PR 每一輪一個全新 session | 乾淨重跑、逐項檢查、變異抽查、寫 PASS / FAIL 留言 | 不修產品程式、不看 Builder 的對話、不合併 | 一輪驗證 |
| **Researcher**（可選） | Chief 內的 subagent | 規劃時的唯讀調查，回傳結論 | 不寫任何檔案 | 一次呼叫 |

啟動流程（`bootstrap-project`）與範本更新（`sop-sync`）不是常駐角色，而是由 Owner 開的單次 session 執行，產出的 PR 一律由 Owner 合併。

**每條限制都要有執行點**

| 限制 | 執行點 |
| --- | --- |
| 只有 Owner 合併 `main` | GitHub ruleset：機器帳號無法更新 `main`（啟動閘門查證） |
| Builder 不改範圍外檔案 | CI `path-scope` |
| Builder 不改規則、規格、看板 | CI `readonly-paths` |
| 不弱化測試 | CI `no-weakened-tests` |
| 只有機器帳號提交 | CI `commit-author` |
| Verifier 獨立 | dispatch 規則：全新 session，prompt 只給 PR 編號與 ticket 路徑 |
| 設定不完整時不能開工 | CI `sop-ready` 與 skill 開頭檢查（第 15 節） |
| Chief 只在 CI 全綠且 PASS 後合併 ticket PR | Chief 確認四項條件（CI 全綠、Verifier PASS、範圍內、唯讀路徑沒被改）；最後由 `main` 的必要檢查與 Owner 審查把關（D22） |

> **EN:** Five roles: Owner (human), Chief of Staff (one session per milestone), Builder (fresh session per ticket), Verifier (fresh session per PR per round, never sees the Builder's conversation), optional Researcher (read-only subagent). Bootstrap and template sync run as one-off Owner-started sessions whose PRs the Owner merges. Every "does not" maps to an enforcement point.

## 6. Milestone 與 ticket 的生命週期

**專案的第一天到一個 milestone 結束**（**粗體**是需要 Owner 的關卡）

```text
GitHub「Use this template」建立 repo
  → 開 Claude session，執行 bootstrap-project（逐題詢問、即時查證、移除僅範本檔案）
  → **Owner 合併啟動 PR**
  → plan-milestone
  → **Owner 核准計畫**
  → 分批開 Builder → 每個 PR 開 Verifier → PASS 則合併
  → milestone-report
  → **Owner 合併 main**
```

啟動 PR 只在專案開始時出現一次；之後每個 milestone 只有兩個關卡。

**Ticket 狀態機**

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

狀態只記在 `docs/board.md`，Chief 是唯一寫入者，因此新的 Chief 不需要舊對話就能接手。

> **EN:** A project starts from "Use this template", then the bootstrap skill (ask, live-check, remove template-only files) and an Owner-merged bootstrap PR; after that, each milestone has two Owner gates. Ticket states live only in `docs/board.md`, written only by the Chief.

## 7. 平行開發模式

### 7.1 可以同時進行的條件

兩張 ticket 可以同時進行，若且唯若：

1. **依賴：** 兩者的 `depends_on` 都已 merged。
2. **路徑不相交：** 兩者的 `allowed_paths` 沒有交集（例外見 7.3）。
3. **序列化資源不相交：** 兩者的 `serial` 沒有共同項目。
4. **容量：** 進行中（building、verifying、fixing）的 ticket 數小於專案設定的 `max_parallel`。

### 7.2 序列化資源

有些衝突不在檔案層級：兩張 ticket 改不同的 migration 檔，卻都改變 schema 的順序；兩張 ticket 都升級依賴，改的是同一份 lockfile。這類共用狀態用 `serial` 宣告，資源清單由專案在啟動時設定（例如 `db-schema`、`lockfile`、`ci-config`、`public-api`）。CI 檢查宣告的資源都在清單內，且沒有另一張進行中的 ticket 宣告同一項。

### 7.3 共用的只增檔案

有些檔案每張 ticket 都要加一行（例如「已實作的規則清單」）。若嚴格要求路徑不相交，這些 ticket 就無法平行。sop-v2 把這類檔案正式列為 `append_only`：

- 可以同時出現在多張平行 ticket 的 `allowed_paths`。
- CI 檢查 PR 對這些檔案的 diff **只有新增行**。
- 合併衝突由 Chief 依序合併時解決，保留雙方的新增行。

### 7.4 Chief 的排程演算法

Chief 在 `plan-milestone` 時算出批次並寫進計畫 issue；執行時每當一張 ticket merged 就重新評估。演算法是貪婪的拓撲排序：

```python
ready = {t in todo | all(depends_on merged)}
running = {t | state in (building, verifying, fixing)}
for t in sorted(ready, key=(critical_path_length desc, id)):
    if len(running) >= max_parallel: break
    if any(paths_overlap(t, r) or serial_overlap(t, r) for r in running): continue
    start(t); running.add(t)
```

**路徑重疊的判定是保守的。** 兩個 glob 是否有交集不易精確計算，所以比較「第一個萬用字元之前的路徑前綴」：其中一個是另一個的前綴就視為重疊。可能誤判為重疊（少平行一點），但不會漏判。PR 時的 `path-scope` 用實際變更的檔案檢查，這是精確的。

依關鍵路徑長度排序，是為了先啟動「後面還有一長串依賴它」的 ticket，縮短 milestone 的總時間。

### 7.5 平行度不宜過大

- 每個平行的 Builder 都需要一個 Verifier，token 成本約為 2×N。
- Chief 要追蹤的 PR 狀態線性增加，Chief 的 context 是瓶頸。
- 參考專案的實測上限是 2–3 張。啟動流程會告訴使用者這個經驗值，但不替使用者填入（P2）。

> **EN:** Two tickets may run together iff dependencies are merged, allowed paths don't overlap, serialized resources don't overlap, and the project's `max_parallel` isn't reached. Append-only shared files are an explicit exception guarded by a CI check that diffs only add lines. The Chief schedules with a greedy topological sort ordered by critical-path length, judging overlap conservatively by static glob prefixes; PR-time path-scope checks actual files exactly. A cap of 2–3 worked in practice and is offered as guidance, never pre-filled.

## 8. 角色的執行方式（dispatch）

角色定義與執行機制分開：第 5 節定義「誰做什麼」，`docs/sop/dispatch.md` 定義「怎麼跑起來」。工具改變時只改這份文件。

| 機制 | 隔離 | 成本 | 用於 |
| --- | --- | --- | --- |
| **獨立 cloud session**（建立 session 並傳送任務） | 最高：各自容器、context、資料庫 | 高 | Builder、Verifier |
| **同 session 的 subagent**（必要時用 worktree 隔離） | 中：共用容器 | 中 | Researcher |
| **Workflow 腳本** | 中 | 可能很高 | 預設不用；僅在 Owner 明確要求的固定批次 |

**為什麼 Verifier 一定是獨立 session：** Verifier 的價值在於「不知道 Builder 怎麼想」。若能看到 Builder 的推理，它會傾向確認 Builder 的說法（anchoring）。所以 Verifier 的 prompt 只包含 PR 編號、ticket 檔路徑與 `verify-ticket` skill 的指示；PR 說明裡的說法不算證據，Verifier 必須自己重跑。

**Dispatch prompt 的固定格式**

```text
角色：Builder
Ticket：docs/tickets/T-012.md
分支：從 milestone/M2 開 ticket/T-012
模型：（Owner 在本 milestone 指定的 Builder 模型）
步驟：使用 build-ticket skill。只讀 ticket「要讀的檔案」列出的內容。
完成時：PR 開好、CI 全綠、交付留言已寫，然後結束。
遇到 AGENTS.md「停下來」的情況：用 ask-owner skill，回報 issue 連結後結束。
```

**Chief 如何得知進度**

- Builder 訂閱自己 PR 的活動，CI 結果會叫醒它，直到全綠。一個 PR 同時只能被一個 session 訂閱，所以 Chief 不訂閱 ticket PR。
- Chief 在子 session 結束或失敗時收到通知，並以 session 狀態與 PR 的 CI 結果重建進度。
- Chief 只讀 PR 說明、Verifier 判定、CI 結果，不讀子 session 的完整對話，以保護自己的 context。

> **EN:** Role definitions are separate from mechanisms; `docs/sop/dispatch.md` maps roles to mechanisms. Builders and Verifiers run as separate cloud sessions; the Researcher as an in-session subagent; Workflow scripts are off by default. The Verifier gets only the PR number and ticket path. Builders subscribe to their own PR; the Chief tracks progress through session status, PR descriptions, verdicts and CI.

## 9. Ticket 契約

Ticket 檔是 Chief 與 Builder 之間唯一的契約，也是 CI 的輸入。每個欄位都有排程用途或機器檢查：

```yaml
---
id: T-012                    # 與分支 ticket/T-012 對應（CI branch-ticket）
title: 一句話
milestone: M2
depends_on: [T-010]          # 排程（D23）
allowed_paths:               # CI path-scope；排程時判斷重疊
  - "src/billing/**"
  - "tests/billing/**"
  - "docs/evidence/T-012/**"
append_only:                 # 選填；須同時列在 allowed_paths，且在專案的 append_only 清單內
  - tests/implemented.txt
serial: [db-schema]          # 選填；序列化資源
screens: false               # 是否需要截圖；沒有這個欄位時 CI evidence 判為失敗（D25）
done_when:                   # CI done-when：這些測試 ID 必須在 JUnit 結果中存在且通過
  - "tests/billing/test_invoice.py::test_rounding"
status: todo                 # 只由 Chief 修改（實際狀態以 board.md 為準）
---
```

本文的固定段落：`## 目標`、`## 要讀的檔案`（只讀這些，保護 Builder 的 context）、`## 完成條件`（人讀的版本，與 `done_when` 一一對應）、`## 不在範圍內`。

完成條件只寫在 ticket 檔，而且以 `done_when` 的形式可被機器判定。規格怎麼寫、測試用什麼框架，範本不管；範本只要求專案能把完成條件對應到 JUnit 結果中的測試 ID。

> **EN:** The ticket file is the only Chief–Builder contract and the input to CI. Each field has a scheduling use or a machine check. "Done" lives only in the ticket, as `done_when` test IDs.

## 10. CI 契約

### 10.1 兩層設計

| 檢查 | 層 | 內容 | 輸入 |
| --- | --- | --- | --- |
| `sop-ready` | 中立 | 啟動閘門：設定符合 schema、啟動已核准、僅範本檔案已移除（第 15 節） | `.sop/*`、檔案清單 |
| `branch-ticket` | 中立 | 目標是 `milestone/*` 的 PR，來源分支必須是 `ticket/T-xxx`，且目標分支上有對應的 ticket 檔 | 分支名、檔案 |
| `path-scope` | 中立 | 每個變更檔案都符合 `allowed_paths` | `git diff --name-only` |
| `readonly-paths` | 中立 | 不得修改 `AGENTS.md`、`.sop/**`、`docs/sop/**`、`.claude/**`、`.github/**`、`docs/board.md`、`docs/decisions.md` 與專案設定的規格路徑；例外是 ticket 的 `allowed_paths` 明確列出（不含萬用字元）的路徑（D25）；只檢查進入 `milestone/*` 的 PR（Chief 直接推送的紀錄不經過 PR，D22）；啟動 PR 與 `sop-sync` PR 只能改各自允許的路徑 | diff、ticket |
| `append-only` | 中立 | `append_only` 檔案的 diff 只有新增行 | `git diff` |
| `serial-resource` | 中立 | 宣告的資源在清單內，且沒有其他進行中的 ticket 宣告同一項 | ticket、`board.md` |
| `evidence` | 中立 | PR 說明的「證據」一節有 code block 或連到 `docs/evidence/T-xxx/`；ticket 為 `screens: true` 時至少一張圖；ticket 沒有 `screens` 欄位判為失敗（D25） | PR body、檔案 |
| `commit-author` | 中立 | 每個 commit 的 GitHub 作者都是專案設定的機器帳號 | GitHub API、`.sop/config.yml` |
| `tests` | 介面 | 執行 `scripts/sop/test`，必須產生 `build/sop/junit.xml` | 專案實作 |
| `no-weakened-tests` | 介面 | 目標分支上通過的每個測試 ID，在 PR 上都被收集且通過；沒有 XML 判為失敗 | 兩份 JUnit XML |
| `done-when` | 介面 | `done_when` 的每一項都在 PR 的 JUnit 中存在且通過 | ticket、JUnit XML |

### 10.2 JUnit XML 介面

pytest、Jest、Go、JUnit、cargo-nextest 等主流測試工具都能輸出 JUnit XML，是跨語言事實上的標準。專案只需實作一支可執行檔：

```text
scripts/sop/test  — 由專案實作
  退出碼：0 = 全部通過，非 0 = 有失敗
  輸出：build/sop/junit.xml
  測試 ID：classname + "::" + name，必須穩定（改名會被視為測試消失）
```

範本內附的 `scripts/sop/test` 預設直接失敗，訊息是「請實作測試介面」。這讓「接上測試」成為啟動閘門的一部分。測試改名時 CI 不提供例外，由 Chief 在 ticket 寫明新舊對應並記錄在決策紀錄。

### 10.3 檢查本身也要被測試

每一項檢查都至少有一個「會讓它失敗」的測試案例，證明檢查真的有效。這些測試屬於僅範本檔案，啟動時移除，不會留在產生的專案中。

> **EN:** Stack-neutral checks (sop-ready, branch-ticket, path-scope, readonly-paths, append-only, serial-resource, evidence, commit-author) need only git, the config files and the GitHub API; stack-specific ones (tests, no-weakened-tests, done-when) go through a single interface, `scripts/sop/test` writing JUnit XML. The shipped stub fails on purpose. Every guard has a test proving it can fail; those tests are template-only and removed at bootstrap.

## 11. 記憶與狀態

Context window 是短期記憶，用完即丟；要留下的事一律寫進 repo。

| 檔案 | 內容 | 寫入者 | 規則 | `sop-sync` 時 |
| --- | --- | --- | --- | --- |
| `AGENTS.md` | 永遠適用的規則摘要 | 範本；專案段落由 Chief 經 Owner 核准修改 | 只放規則與連結；專案段落以 `<!-- sop:project:begin -->` / `<!-- sop:project:end -->` 隔開（D20） | 只更新範本段落 |
| `.sop/config.yml` | 專案設定值 | 啟動流程；之後只能經 Owner 核准的 PR 修改 | 必須符合 `.sop/schema.json` | 不覆寫；新版若新增欄位，sync PR 會要求填寫 |
| `.sop/bootstrap.yml` | 啟動查證結果 | `bootstrap-project`；Owner 合併時核准 | 見第 15 節 | 不覆寫 |
| `.sop/schema.json`、`.sop/managed.txt`、`.sop/version` | 設定格式、範本擁有的路徑、範本版本 | 範本 | 專案不改 | 覆寫 |
| `docs/sop/**`、`.claude/skills/**`、`scripts/sop/**`（`scripts/sop/test` 除外） | 完整流程、skills、檢查程式 | 範本 | 專案不改；要改就回饋到 sop-v2 | 覆寫 |
| `scripts/sop/test` | 測試介面（第 10.2 節） | 專案（啟動時由 `bootstrap-project` 協助寫入） | 範本內附的版本故意失敗 | 不覆寫 |
| `docs/board.md` | ticket 狀態、各輪使用的模型 | Chief | 單一事實來源 | 不覆寫 |
| `docs/decisions.md` | Owner 的決定 | Chief | 只增不改；推翻時新增一列並註明取代哪列 | 不覆寫 |
| `docs/pitfalls.md` | 下一個 agent 不知道就會再犯的事 | Chief（milestone 結束時） | 上限 30 條 | 不覆寫 |
| `docs/learning.md` | 學習紀錄（僅在 `modules.learning` 開啟時存在，D19） | Chief | 只增不改 | 不覆寫 |
| `docs/tickets/*.md` | 任務契約 | Chief | 完成條件只在這裡 | 不覆寫 |
| `docs/milestones/Mx.md` | 給 Owner 的報告 | Chief | 數字可重算；每個「已驗證」都連到證據 | 不覆寫 |

> **EN:** Anything that must outlive a context window goes into the repo. Template-owned files (listed in `.sop/managed.txt`: `docs/sop/**`, skills, `scripts/sop/**` except the project-implemented `scripts/sop/test`, schema, version) are overwritten by `sop-sync`; project values live in `.sop/config.yml`, validated by `.sop/schema.json`; project-owned files are never overwritten.

## 12. 升級、修正輪與證據

**什麼時候停下來找 Owner**

1. 規格不清楚或互相矛盾。
2. 需要改資料模型或公開介面，而 ticket 沒有授權。
3. 第二輪修正後 Verifier 仍判定 FAIL。
4. 專案設定的敏感領域（例如權限、金額、加密）沒有測試涵蓋。

唯一的管道是 GitHub issue（`needs-owner` 標籤），由機器帳號開立，Owner 會收到通知。每個 issue 給兩到三個選項、各自的後果與反悔成本，並標出建議。不替 Owner 決定，也不先照建議實作。等待期間，不依賴該 ticket 的其他 ticket 繼續。

**修正輪**

| 輪次 | 誰修 | 為什麼 |
| --- | --- | --- |
| 第一輪 | 原 Builder session | 它有實作的 context，修小問題最快 |
| 第二輪 | 新的 Builder session，用 Owner 指定的較強模型 | 同一個 session 兩次都沒修好，通常是理解有偏差，換新 context 才能跳出 |
| 之後 | 停止，升級給 Owner | 避免子 session 空轉燒成本 |

**證據與署名**

- 任何「已驗證」「已通過」都附證據：CLI 指令與輸出；有畫面的附截圖，存在 `docs/evidence/T-xxx/`。
- 「先紅」的失敗輸出也是證據。
- Builder 與 Verifier 的留言寫明模型名稱與版本，從 session 的實際設定取得，取不到就寫「無法取得」。Chief 在看板記錄各輪使用的模型。

> **EN:** Escalate only via GitHub issues with options, consequences and a recommendation; never decide for the Owner. Fix round 1 is the original Builder; round 2 a fresh session on a stronger Owner-chosen model; then escalate. Every verification claim carries evidence; every handoff names the model from the session's actual configuration.

## 13. 可選模組

每個模組都是 `.sop/config.yml` 中一個必填的是／否欄位，沒有預設值。

| 模組 | 設定欄位 | 內容 | 開啟後的啟動查證 |
| --- | --- | --- | --- |
| 學習 | `modules.learning` | milestone 報告加「Q1–Q4」一節（Owner 先答，Chief 再比較差異）；Owner 的回答記在獨立的 `docs/learning.md`（D19）；附教學與追問用的 skills | 無 |
| `@claude` review | `modules.claude_review` | PR 上提及 `@claude` 觸發審查的 workflow | repo secret 已設定 |
| 文件檢查 | `modules.docs_lint` | Markdown 格式與連結檢查 | 無 |

**關閉的模組怎麼處理：** 每個模組的檔案集中在一個位置（例如 `.claude/skills/learning/`、`.github/workflows/module-*.yml`），並在 `.sop/managed.txt` 標註所屬模組。啟動流程會**刪除**關閉的模組檔案，`sop-sync` 也只同步已開啟的模組。之後要開啟某個模組，就修改設定並執行 `sop-sync`。

測試介面的語言範例不再是模組：啟動流程會依使用者描述的技術棧，協助寫出 `scripts/sop/test`，並實際執行確認能產生 JUnit XML（B5）。

> **EN:** Each optional module is a required yes/no field in `.sop/config.yml`. Module files are grouped and tagged in `.sop/managed.txt`; bootstrap deletes disabled modules and `sop-sync` only syncs enabled ones (enable later by editing config and running sync). The test-interface example is no longer a module: bootstrap helps write `scripts/sop/test` for the user's stack and runs it to confirm JUnit output.

## 14. 發布、設定與更新

### 14.1 常見做法與選擇

| 做法 | 例子 | 使用門檻 | 防設定錯誤 | 之後的更新 |
| --- | --- | --- | --- | --- |
| GitHub template + 手動改佔位符 | 多數 starter repo | 最低 | ❌ 容易漏改 | ❌ |
| 生成器 CLI（無更新） | Cookiecutter、`npm create`、`cargo generate` | 中：需安裝工具 | 只驗格式 | ❌（Cookiecutter 可加 `cruft`） |
| 生成器 CLI（有更新） | Copier | 中偏高：Python、終端機、Jinja | 只驗格式 | ✅ 三方合併 |
| 由程式管理設定檔 | projen | 高 | 型別 | ✅ 最強但最受限 |
| 組織內部範本平台 | Backstage Software Templates | 低：網頁表單 | 表單驗證 | 部分 |
| **Template + agent 啟動（本設計）** | — | **低：按鈕 + 對話** | **格式 + 即時查證事實** | ✅ `sop-sync`（覆寫範本擁有的路徑） |

### 14.2 設定欄位

所有值放在 `.sop/config.yml`，格式由 `.sop/schema.json`（JSON Schema 的子集）定義。範本中每個欄位都是 `null`，代表未填。**沒有預設值**；啟動流程可以提供建議與說明，但必須由使用者明確回答。

| 欄位 | 型別與驗證 | 啟動時的即時查證 | 用途 |
| --- | --- | --- | --- |
| `project.name` | 字串，非空 | — | 文件標題、報告 |
| `project.goal` | 字串，一句話，非空 | — | `AGENTS.md` 的專案段落 |
| `owner.display_name` | 字串，非空 | — | 文件中稱呼 Owner 的名字 |
| `owner.github` | GitHub login 格式 | 帳號存在；是 repo 擁有者或 Admin | 計畫 issue 與 milestone PR 的指派對象 |
| `bot.github` | GitHub login 格式，不可等於 `owner.github` | 帳號存在；是 Write collaborator（B2）；目前 session 以它登入（B1） | `commit-author`；身分檢查 |
| `bot.github_id` | 正整數 | 與 `bot.github` 的實際 ID 相符 | 機器帳號的 noreply email |
| `doc_language` | 列舉：`zh-TW` / `en` / … | — | 專案產出的語言 |
| `max_parallel` | 整數 1–5 | — | 平行上限 |
| `spec_paths` | glob 清單，可為空但不可為 `null` | 列出的路徑存在或已規劃 | 額外的唯讀路徑 |
| `serial_resources` | 名稱清單，可為空但不可為 `null` | — | 序列化資源 |
| `append_only_files` | 路徑清單，可為空但不可為 `null` | — | 只增檔案 |
| `sensitive_areas` | 字串清單，可為空但不可為 `null` | — | 升級條件第 4 條 |
| `modules.*` | 布林，不可為 `null` | 開啟 review 時 secret 已設定（B6） | 可選模組 |
| `template.source` | `owner/repo` | 由 GitHub API 的 `template_repository` 自動讀取並請使用者確認 | `sop-sync` 的來源 |
| `overrides.disabled_guards` | 物件清單（檢查名稱、原因、決策編號），可為空但不可為 `null` | 檢查名稱存在（`sop-ready` 本身不能停用）；決策編號（格式 `D-001`）存在於 `docs/decisions.md` | 停用範本檢查（第 14.6 節 C4） |

模型分配不是設定欄位：它由 Owner 在每個 milestone 的計畫核准時指定，記在看板上，因為模型會隨時間更換。

**驗證只寫一份：** `.sop/schema.json` 同時被三個地方使用：`bootstrap-project` skill、CI 的 `sop-ready`、給不使用 Claude 的人準備的備用腳本 `scripts/sop/bootstrap`（只用 Python 標準函式庫的互動腳本，做格式驗證與能用 `GITHUB_TOKEN` 完成的查證）。為了讓標準函式庫就能驗證，schema 只使用一個小子集，並由 `scripts/sop/config.py` 實作：`type`（單一型別，永遠不含 `null`）、`properties`、`required`、`additionalProperties`（只允許 `false`，用來抓欄位名稱的錯字）、`items`（可巢狀，用於物件清單）、`enum`、`pattern`、`minLength`、`minimum`、`maximum`，以及一個擴充關鍵字 `x-not-equal-to`（跨欄位不相等，可設定忽略大小寫，用於 `bot.github ≠ owner.github`）。驗證器遇到子集以外的關鍵字會直接報錯，不會默默略過規則。

### 14.3 為什麼不需要模板渲染

範本擁有的檔案在所有專案都相同；專案差異只在 `.sop/config.yml`。workflow、腳本、skill 在**執行時**讀取設定，而不是在建立時把值寫進檔案。少數需要給人看的地方（例如 `AGENTS.md` 的專案段落）由啟動流程直接寫入專案擁有的區段。這也避開了 GitHub Actions 的 `${{ }}` 與模板語法的衝突。

### 14.4 範本自身的開發檔案（D10）

GitHub template 會複製整個 repo，包括 sop-v2 自己的開發檔案。這些檔案列在 `.sop/template-only.txt`：

```text
docs/design/
tests/sop/
.github/workflows/self-ci.yml
README.md  marker:…   # 範本的使用說明；啟動時換成專案 README 骨架（D32）
LICENSE  marker:…     # 範本的授權；專案自行決定授權（D9、D32）
```

啟動流程刪除這些檔案，`sop-ready` 確認它們都不存在。帶 `marker:` 的條目（README、LICENSE）可以換成專案自己的版本，`sop-ready` 只確認它不再是範本的版本（D32）。

### 14.5 更新：`sop-sync`

1. sop-v2 合併改進後打 semver tag（例如 `v2.1.0`），並在 release notes 寫明是否新增設定欄位。
2. 專案中由 Owner 開一個 session 執行 `sop-sync` skill（不提供 workflow，D36）：
   - 從 `template.source` 抓指定 tag。
   - 用新版覆寫 `.sop/managed.txt` 列出的路徑（只包含已開啟的模組）。
   - 更新 `.sop/version`。
   - 新版 schema 若新增欄位，逐題詢問使用者，同樣沒有預設值（P2 在更新時也成立）。
   - 在 `sop/sync-v2.1.0` 分支開 PR。
3. PR 只能由 Owner 合併。回滾：用同一流程同步回前一個 tag。

因為範本擁有的路徑在專案中是唯讀的（`readonly-paths`），覆寫不會蓋掉專案的修改，不需要三方合併。

### 14.6 客製化層級

範本的目的是讓每個專案客製化使用，但客製化不能破壞兩件事：P2 的閘門，以及之後能用 `sop-sync` 取得更新。所以客製化分成五層，越往下越強、代價也越高：

| 層 | 能改什麼 | 放在哪裡 | 會不會被 `sop-sync` 覆寫 | 需要誰核准 |
| --- | --- | --- | --- | --- |
| **C1 設定值** | 第 14.2 節的所有欄位：帳號、語言、平行上限、唯讀路徑、序列化資源、模組開關 | `.sop/config.yml` | 不會 | 啟動時由 Owner；之後經 Owner 合併的 PR |
| **C2 專案規則** | 專案自己的規則、技術棧說明、指令、目錄約定、敏感領域的細節 | `AGENTS.md` 的專案段落、`docs/project/**` | 不會 | Owner |
| **C3 擴充** | 專案專屬的 skill、額外的 CI 檢查、額外的 issue / PR 樣板段落 | `.claude/skills/project/**`、`.github/workflows/project-*.yml`、`scripts/project/**` | 不會 | Owner；擴充本身也受 `readonly-paths` 保護，Builder 不能改 |
| **C4 停用範本規則** | 關掉某一項範本檢查（例如專案不需要 `evidence`） | `.sop/config.yml` 的 `overrides.disabled_guards`，每項附原因與 `docs/decisions.md` 的決策編號 | 不會 | Owner；`sop-ready` 檢查每項停用都有對應的決策紀錄 |
| **C5 修改範本本身** | 改流程、角色、skill 的內容 | fork sop-v2，改完後把 fork 當成 `template.source` | 會從 fork 同步 | fork 的維護者 |

原則：

- **先用低層：** 能用 C1–C3 解決的，不要用 C4、C5。專案特有的需求放在專案擁有的位置，就不會跟範本更新衝突。
- **停用要留下紀錄：** C4 不是偷偷關掉，而是一個寫進決策紀錄、有原因、可被審查的決定。`sop-ready` 會列出目前停用的檢查，讓每個 PR 的 reviewer 都看得到。
- **通用的改進回饋給範本：** 如果某個客製化對所有專案都有用，應該回饋到 sop-v2，而不是留在單一專案裡。
- **C5 是逃生口：** 想要完全不同的流程時，fork 範本並把 `template.source` 指向自己的 fork，仍然可以用 `sop-sync` 在自己的 fork 與專案之間同步。

`overrides.disabled_guards` 也是必填欄位（可以是空清單，但不可為 `null`），所以 P2 仍然成立：使用者必須明確回答「要不要停用任何檢查」。

> **EN:** Customization comes in five layers, from cheapest to strongest: C1 config values (`.sop/config.yml`); C2 project rules (the project section of `AGENTS.md`, `docs/project/**`); C3 extensions (project skills, extra CI workflows and scripts under `project/` paths); C4 disabling a template guard via `overrides.disabled_guards`, each with a reason and a decision-log reference that `sop-ready` checks; C5 forking sop-v2 and pointing `template.source` at the fork. C1–C4 live in project-owned locations, so `sop-sync` never overwrites them. Prefer the lowest layer that works; disabling must be recorded and visible; generally useful changes go back to sop-v2; C5 is the escape hatch. `overrides.disabled_guards` is itself required (may be empty, never null), so P2 still holds.

> **EN:** Distribution is a GitHub template repository plus an agent-guided bootstrap. All values live in `.sop/config.yml` (every field `null` in the template, no defaults), validated by one schema (`.sop/schema.json`, a small JSON Schema subset implemented in stdlib Python) shared by the bootstrap skill, CI `sop-ready`, and a stdlib fallback script for people without Claude. Bootstrap also checks facts live via the GitHub API. No templating is needed because template-owned files are identical across projects and read config at runtime. Template-only development files (design doc, guard tests, self CI, template README and LICENSE) are listed in `.sop/template-only.txt` and removed at bootstrap. Updates use `sop-sync`: fetch a tag from `template.source`, overwrite the managed paths (enabled modules only), ask any new schema questions, and open an Owner-merged PR; no three-way merge is needed because managed paths are read-only in projects.

## 15. 啟動閘門

P2 用三層來保證。每一層防的情況不同，缺一層就有漏洞：

| 層 | 機制 | 防的情況 | 擋不到的情況 |
| --- | --- | --- | --- |
| **L1 啟動流程** | `bootstrap-project` 逐題詢問，依 schema 驗證格式，並向 GitHub **即時查證**事實 | 漏填、格式錯、**帳號不存在、權限錯誤、ruleset 沒設** | 使用者不跑啟動流程，直接手改設定 |
| **L2 repo 層** | CI `sop-ready`，對所有目標為 `main` 或 `milestone/*` 的 PR 執行 | 手改後不符合 schema、`ready` 未核准、僅範本檔案沒刪 | agent 不開 PR、直接在本機開工 |
| **L3 agent 層** | 每個 skill 的第一步都是讀 `.sop/bootstrap.yml`，`ready` 不是 true 就停止並告訴 Owner | agent 在閘門通過前就開始規劃或實作 | 有人刻意繞過 skill（此時 L2 仍會擋住合併） |

**啟動流程的互動原則**

- 一次問一題，附上說明、為什麼需要、建議值（如果有），但**不得替使用者填入**。
- 每個答案立刻驗證；不通過時說明原因，並指出去哪個設定頁修正，再重問。
- 使用者說「不知道」時，解釋選項與後果，請使用者決定；仍無法決定就停在該題，不跳過。
- 全部答完後，列出完整設定讓使用者確認，再寫入檔案。

**Repo 設定的查證（B1–B7）**

這些是 GitHub repo 的設定，不是檔案。啟動流程逐項檢查，結果寫進 `.sop/bootstrap.yml`，每項附證據（API 回應或指令輸出）：

| # | 檢查 | 驗證方式 |
| --- | --- | --- |
| B1 | 目前 session 的 GitHub 身分等於 `bot.github` | 查詢目前登入的使用者 |
| B2 | 機器帳號是 collaborator，權限是 Write（不是 Admin） | repo collaborator API |
| B3 | `main` 有 ruleset：機器帳號無法直接更新 | branch rules API；無法讀取時由 Owner 提供設定畫面截圖 |
| B4 | `main` 的 ruleset 把 CI 的必要檢查設為必須通過（D22） | 同上 |
| B5 | `scripts/sop/test` 已實作，能產生 JUnit XML | 實際執行 |
| B6 | （啟用 review 模組時）repo secret 已設定 | secret 名稱清單 API（不讀值） |
| B7 | 僅範本檔案已移除；關閉的模組已移除 | 檔案清單比對 |

**閘門如何打開**

1. `bootstrap-project` 在 `sop/bootstrap` 分支寫入設定與查證結果，全部通過時把 `ready` 設為 `true`，並開 PR 到 `main`。`ready: true` 時，B1–B7 每項都必須是 `passed`（附證據）或 `not_applicable`，否則 `sop-ready` 失敗，這樣手改一行 `ready: true` 也開不了閘門。
2. 只有 Owner 能合併 `main`（B3 已查證），所以**閘門最後一定經過 Owner 核准**。agent 自己無法把閘門打開。
3. 合併後，`sop-ready` 在 `main` 上為綠，`plan-milestone` 才能開始 M0。

若之後任何設定被改壞（例如有人手改 `.sop/config.yml`），`sop-ready` 會在下一個 PR 失敗，閘門自動關上。

> **EN:** P2 in three layers: L1 the bootstrap skill asks one question at a time, validates against the schema, and live-checks facts with GitHub (catching missing accounts, wrong permissions, missing rulesets); L2 CI `sop-ready` on every PR into main or milestone branches; L3 every skill checks `.sop/bootstrap.yml` first. Bootstrap never fills an answer for the user, re-asks on failure with the fix, and confirms the full config before writing. B1–B7 are verified with evidence; `sop-ready` rejects `ready: true` while any check is pending or failed, or passed without evidence. The gate opens only when the Owner merges the bootstrap PR, and closes again if config is later broken.

## 16. 範本的個資衛生

P1 要求 sop-v2 這個 repo 本身沒有個人資訊。做法：

- **內容：** 範本中的人一律以角色稱呼（Owner、Chief、機器帳號），具體值全部是 `.sop/config.yml` 中未填的欄位。範例資料使用明顯虛構的值（例如 `example-owner`、`example-bot`）。
- **CI 掃描：** sop-v2 自己的 CI 掃描 email、GitHub 帳號連結、`@` 提及等樣式。採**允許清單**：只允許虛構範例值與公開的工具來源（例如 GitHub Actions 官方 action）。不用禁止清單，因為禁止清單本身就得寫出要隱藏的個資。
- **Git 歷史：** commit 作者使用 noreply 位址；PR 合併前檢查新 commit 的作者資訊。歷史一旦含有個資，只能靠改寫歷史清除，所以要在合併前擋住。sop-v2 本身已有一筆例外，處理方式見 D15。
- **合併產生的 commit：** Owner 在網頁上合併 PR 時，GitHub 會以 Owner 的身分（顯示名稱與 noreply email）建立 merge commit。在意這點的專案可以只允許 rebase 合併，或清空 GitHub 的顯示名稱。（sop-v2 本身目前接受這一點。）
- **使用紀錄不進範本：** 某個專案怎麼用這個範本、遇到什麼問題，留在那個專案的 repo；回饋到 sop-v2 時只寫成通用的規則。
- **Template 不帶歷史：** 用「Use this template」建立的 repo 從一個全新的 commit 開始，不包含 sop-v2 的 git 歷史，所以範本歷史中的合併紀錄不會進入使用者的專案。

注意：產生的專案中，`.sop/config.yml` 會存放 Owner 和機器帳號等資訊。這是使用者自己的專案，屬於預期行為；README 會說明這一點。

> **EN:** People are referred to by role; concrete values are unset config fields; examples are fictional. The template's CI scans against an allowlist. Commits use noreply addresses, checked before merge. Web merges create commits under the Owner's identity; projects that care can allow only rebase merges or clear their display name (sop-v2 currently accepts this). Repos created from a GitHub template start from a fresh commit without the template's history. Generated projects store owner and bot accounts in `.sop/config.yml`, which is expected and documented.

## 17. Repo 結構

範本 repo 的根目錄就是專案的樣子；只有 `.sop/template-only.txt` 列出的路徑會在啟動時移除。

```text
sop-v2/
  README.md                       # 範本使用說明（僅範本；啟動時換成專案 README 骨架）
  LICENSE                         # MIT-0（僅範本，D9）
  docs/design/sop-v2-design.md    # 本文件（僅範本）
  tests/sop/                      # 檢查本身的測試（僅範本）
  .github/workflows/self-ci.yml   # 範本自己的 CI（僅範本）
  CLAUDE.md                       # 一行：讀 AGENTS.md
  AGENTS.md                       # 規則摘要；專案段落以標記隔開，啟動時填入
  .sop/
    config.yml                    # 所有欄位為 null
    schema.json                   # 設定格式（JSON Schema 子集）
    bootstrap.yml                 # ready: false，B1–B7 待查證
    managed.txt                   # 範本擁有的路徑（含模組標註）
    template-only.txt             # 啟動時移除的路徑
    version                       # 範本版本
  docs/sop/
    workflow.md  parallel.md  dispatch.md  ci-contract.md  bootstrap.md  sync.md  setup.md
  docs/board.md  docs/decisions.md  docs/pitfalls.md
  docs/learning.md                # 學習模組開啟時才有（D19）
  docs/project/                   # 專案自己的規則與說明（C2，專案擁有）
  docs/tickets/_template.md
  docs/milestones/README.md  docs/milestones/report-template.html
  .claude/skills/project/         # 專案專屬 skill（C3，專案擁有）
  .github/workflows/project-*.yml # 專案額外的 CI（C3，專案擁有；GitHub 只執行 workflows/ 第一層的檔案）
  scripts/project/                # 專案的腳本（C3，專案擁有）
  .claude/skills/
    bootstrap-project/  sop-sync/  plan-milestone/  build-ticket/
    verify-ticket/  ask-owner/  milestone-report/
    learning/                     # 學習模組（關閉時啟動流程刪除）
  .github/
    ISSUE_TEMPLATE/plan-approval.md  ISSUE_TEMPLATE/needs-owner.md
    PULL_REQUEST_TEMPLATE.md
    workflows/sop-guards.yml
    workflows/module-*.yml        # 模組的 workflow（關閉時刪除）
  scripts/sop/
    config.py                     # 讀取設定、schema 子集驗證（標準函式庫）
    guards.py                     # 中立檢查（含 sop-ready）
    compare_junit.py              # no-weakened-tests、done-when
    bootstrap                     # 不使用 Claude 時的備用互動腳本
    test                          # 測試介面；預設失敗（專案擁有，不被 sop-sync 覆寫）
```

> **EN:** The template repo root looks like a project; only paths in `.sop/template-only.txt` (README, LICENSE, design doc, guard tests, self CI) are removed at bootstrap. Config, schema, bootstrap state, the managed-path list and the version live under `.sop/`.

## 18. 失效情境與最壞影響

| 情境 | 後果 | 對策 |
| --- | --- | --- |
| 規格本身是錯的 | 全綠但行為錯 | milestone 報告必須列出「agent 自行做的判斷」；Owner 對照實際需求審查 |
| 測試步驟造假（永遠通過） | 全綠但沒驗證到 | Verifier 變異抽查：故意改壞產品程式，確認對應測試會失敗 |
| 檢查本身有 bug | **所有下游專案**被擋或漏放 | 每項檢查都有會失敗的測試；semver 發布；下游可 `sop-sync` 回前一版 |
| 啟動流程的 agent 自行填值 | 違反 P2 | skill 規則禁止；全部答完後讓使用者確認；Owner 審查啟動 PR；`sop-ready` 再驗一次 schema |
| 啟動閘門過嚴（例如 API 讀不到 ruleset） | 新專案無法開工 | B3、B4 允許 Owner 以截圖證據核准；閘門的打開永遠需要 Owner 合併 |
| 使用者不跑啟動流程，直接手改設定 | 少了即時查證 | L2 仍驗 schema 與 `ready`；`ready` 只能由啟動 PR 經 Owner 合併設為 true |
| 不使用 Claude 的使用者 | 無法用 skill | 備用腳本 `scripts/sop/bootstrap` 做格式驗證與可用 token 完成的查證 |
| 僅範本檔案沒刪乾淨 | 專案裡留著範本的 README、LICENSE、測試 | B7 與 `sop-ready` 檢查 `.sop/template-only.txt` |
| 關閉的模組檔案殘留 | 多餘的 skill 或 workflow | B7 檢查；`sop-sync` 只同步已開啟的模組 |
| 專案改了範本擁有的檔案 | `sop-sync` 會覆寫掉 | `readonly-paths` 擋下；要改就回饋到 sop-v2 |
| 個資混進範本 | 違反 P1，分享時外洩 | 允許清單掃描；PR 檢查 commit 作者 |
| 路徑重疊判定太保守 | 平行度下降 | 可接受；Chief 可在計畫中列出「人工確認不重疊」由 Owner 核准 |
| Verifier PASS 只靠流程 | Chief 可能在沒有 PASS 時合併 | 候選改進：CI 檢查 PR 上有機器帳號留下、格式正確、對應目前 head SHA 的 PASS 留言 |
| Chief session 中斷 | 進度停住 | 狀態全在 repo；新 Chief 讀看板與 PR 狀態接手 |
| 平行開太多 | 成本 ×2N、Chief context 爆掉 | 上限由專案設定；修正輪上限 2 |

**最壞影響與回滾：** sop-v2 只是範本，建立它不影響任何現有專案。風險在之後：檢查的 bug 會擴散到所有下游專案，啟動閘門過嚴會讓新專案無法開工。回滾方式：下游以 `sop-sync` 同步回前一個 tag；sop-v2 以 revert 修正後發新的 patch 版。

> **EN:** Creating sop-v2 touches no existing project. Later risks are guard bugs propagating downstream and an overly strict gate blocking new projects. Roll back per project with `sop-sync` to the previous tag; fix sop-v2 with a revert and a new patch release.

## 19. 實作計畫

| 階段 | 內容 | 完成條件 |
| --- | --- | --- |
| S0 設定與閘門骨架 | `.sop/`（`config.yml` 全 `null`、`schema.json`、`bootstrap.yml`、`managed.txt`、`template-only.txt`、`version`）、`scripts/sop/config.py`（schema 子集驗證）、`guards.py` 中的 `sop-ready`、預設失敗的 `scripts/sop/test`、`self-ci.yml` | 測試：未填的範本 `sop-ready` 失敗；填好且 `ready: true`、僅範本檔案已移除的樣本通過；每條 schema 規則都有一個被拒絕與一個通過的案例；任一欄位為 `null` 即失敗 |
| S1 協作文件 | `AGENTS.md`、`docs/sop/*`、skills（不含 bootstrap / sync）、issue / PR 樣板、看板與 ticket 樣板、報告樣板 | 個資掃描通過；所有具體值都來自設定欄位 |
| S2 其餘檢查 | `guards.py` 其他檢查、`compare_junit.py`、`sop-guards.yml` | 每項檢查至少一個會失敗的測試；自我 CI 全綠 |
| S3 啟動與更新 | `bootstrap-project` skill（互動原則、B1–B7）、備用腳本 `scripts/sop/bootstrap`、`sop-sync` skill 與 workflow、模組的開關 | 備用腳本有測試；sync 的覆寫範圍有測試；模組開關各組合的 B7 結果正確 |
| S4 試用 | 開啟 template mode，用「Use this template」建立測試專案，走完啟動閘門，讓一張假 ticket 走完 Builder → Verifier → 合併，再做一次 `sop-sync` | 流程走得通；發 `v2.0.0` |

> **EN:** S0 config and gate skeleton (`.sop/` files, a stdlib schema-subset validator, `sop-ready`, the failing test stub, self CI) with tests proving an unfilled template fails and a completed sample passes; S1 de-projectized docs and skills; S2 remaining guards; S3 bootstrap skill, fallback script and `sop-sync`; S4 enable template mode and run a trial project end to end, then tag v2.0.0.

## 20. 待決問題

1. **Ruleset 的可讀性：** 以機器帳號（非 Admin）能否透過 API 讀到 branch rules，決定 B3、B4 能否全自動查證。
2. **Verifier PASS 的機器檢查** 放進 v2.0 還是 v2.1。
3. **`template_repository` 的可用性：** 用 template 建立的 repo，GitHub API 會回傳來源範本；需確認機器帳號能讀到，否則 `template.source` 改由使用者輸入。
4. ~~**Schema 子集的範圍**~~ **已解決（S0）：** 原本列出的子集不夠，缺三項：跨欄位規則（`bot.github ≠ owner.github`）、物件清單的元素結構（`overrides.disabled_guards`）、拒絕未知欄位。補上 `x-not-equal-to`、可巢狀的 `items` 與 `additionalProperties: false` 後足夠（第 14.2 節）。證據：`tests/sop/test_schema_rules.py` 從 schema 自動列出每一條規則，若有規則沒有「拒絕」與「通過」案例，測試就失敗。
5. ~~**設定檔格式**~~ **已解決（S0）：** 限制版 YAML 子集（D12）。TOML 沒有 `null`，無法表達「欄位存在但未填」；JSON 不能寫註解；外部依賴違反「只用標準函式庫」。證據：`tests/sop/test_yaml_subset.py` 的接受與拒絕案例，以及在有 PyYAML 時比對解析結果一致的測試。

> **EN:** Open: (1) whether a non-admin machine account can read branch rules (decides if B3/B4 are fully automatic); (2) Verifier-PASS machine check in v2.0 or v2.1; (3) whether the machine account can read `template_repository` from the API, else the user types `template.source`; (4) resolved in S0: the original subset was not enough (no cross-field rule, no object-list items, no unknown-field rejection); adding `x-not-equal-to`, nestable `items` and `additionalProperties: false` covers every rule, and a test enumerates the schema's rules and fails if any lacks a rejected and an accepted case; (5) resolved in S0: a restricted YAML subset (D12), because TOML has no null, JSON has no comments, and a dependency breaks stdlib-only.
