# SOP v2 設計文件

Chief of Staff 與 subagent 協作、平行開發的通用專案範本。草稿 v0.4，2026-11-19。

> **一句話：** 一個任何人都能拿來開新專案的範本。它定義「Chief 分派、Builder 實作、Verifier 獨立驗收、Owner 只做決策」的協作模式與平行開發規則，並用 CI 把角色之間的契約變成機器檢查。範本本身不含任何個人或專案資訊；所有需要注入的資訊都必須在建立專案時選定，並通過啟動閘門，才能開始開發。
>
> **EN:** A template anyone can use to start a project. It defines a collaboration model (the Chief dispatches, Builders build, Verifiers check independently, the Owner only decides) and parallel-development rules, with CI turning the contract between roles into machine checks. The template carries no personal or project data; every value that must be injected is chosen when the project is created, and development can't start until a bootstrap gate passes.

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
14. [注入點與 Copier](#14-注入點與-copier)
15. [啟動閘門](#15-啟動閘門)
16. [範本的個資衛生](#16-範本的個資衛生)
17. [Repo 結構](#17-repo-結構)
18. [失效情境與最壞影響](#18-失效情境與最壞影響)
19. [實作計畫](#19-實作計畫)
20. [待決問題](#20-待決問題)

---

## 1. 範本定義

sop-v2 必須同時滿足兩個性質。之後的每個設計都要能回答「它怎麼維持這兩個性質」。

| 性質 | 定義 | 怎麼保證 |
| --- | --- | --- |
| **P1 可分享** | 範本 repo 內不含任何個人資訊：姓名、帳號、email、私人 repo、個人偏好、特定專案的內容。任何人拿到都能直接使用，不會看到或沿用別人的設定。 | 所有人和專案相關的值都是注入點（第 14 節）；範本 repo 的 CI 掃描個資樣式（第 16 節） |
| **P2 先完整，才開工** | 建立專案時，每一個注入點都必須被明確選定，**不提供預設值**。只要還有任何一項沒填、沒驗證，就不能開始開發。 | 三層啟動閘門：Copier 必答問題、repo 的 `sop-ready` CI 檢查、每個 skill 開頭的檢查（第 15 節） |

P2 的理由：協作模式的安全性依賴這些值（例如機器帳號決定誰能 commit、誰不能推 `main`）。一個「先用預設值、之後再改」的值，最常見的結局是從來沒被改，而錯的身分設定會讓所有防護失效。

> **EN:** Two properties. **P1 Shareable:** the template repo contains no personal data (names, accounts, emails, private repos, personal preferences, project content); every person- or project-specific value is an injection point, and the template's own CI scans for personal-data patterns. **P2 Complete before start:** every injection point must be chosen explicitly, with no defaults; development is blocked until all are filled and verified, via a three-layer bootstrap gate. Rationale: the model's safety depends on these values, and "use the default, change it later" usually means never changed.

## 2. 目標與非目標

**目標**

- **G1 協作模式可重用：** 角色、交接格式、狀態機、升級管道，在任何專案都一樣。
- **G2 平行開發安全：** 多個 Builder 同時工作時不互相覆寫；衝突在計畫階段排除，CI 是最後防線。
- **G3 契約可被機器檢查：** 「Builder 只能改自己的範圍」「不能弱化測試」「沒有證據不算完成」由 CI 判定，不靠 agent 自律。
- **G4 與技術棧無關：** 範本不假設語言、框架、資料庫；專案只需實作一個測試介面。
- **G5 可演進：** 範本改進後，既有專案能同步更新。
- **G6 = P1、G7 = P2**（第 1 節）。

**非目標**

- 不含規格、產品程式、測試內容、資料庫 migration 的任何具體做法。
- 不取代 GitHub 的 repo 設定（ruleset、collaborator、secret）；範本只引導設定並驗證。
- 不做常駐的 orchestrator 服務：Chief 本身就是一個 Claude Code session。

> **EN:** Goals: reusable collaboration model; safe parallel development; machine-checkable contracts; stack-neutral; evolvable; plus P1 and P2. Non-goals: any product content; replacing GitHub repo settings (the template guides and verifies them); a standalone orchestrator service.

## 3. 來源

sop-v2 由兩個前身整理而來：一份以文件規範為主的單 session 範本（v1），以及一個在實戰中跑過多個 milestone 的參考專案。參考專案把 v1 發展成多 session、由 CI 強制執行的流程，平行上限 2–3 張 ticket，修正輪與升級都有紀錄。sop-v2 把參考專案拆成三層：

| 層 | 參考專案中的內容 | sop-v2 的處理 |
| --- | --- | --- |
| **A 協作模式** | Owner / Chief / Builder / Verifier 四角色、ticket 狀態機、兩輪修正後升級、用 issue 找 Owner、Chief 中斷後從 repo 接手 | 完整保留；人名、帳號、模型全部改成注入點 |
| **B 平行與防護** | `depends_on`、`allowed_paths`、migration 一次一張、同時上限、看板 / 決策 / 坑的紀錄、證據與模型署名、CI 檢查 | 保留並通用化：migration → **序列化資源**；CI 拆成與技術棧無關的檢查加一個 **JUnit XML 介面** |
| **C 專案內容** | 規格、產品程式、特定資料庫與測試框架、專案專屬的檢查與 skill | 全部刪除 |

> **EN:** sop-v2 consolidates two predecessors: a documentation-driven single-session template (v1) and a reference project that evolved it into a multi-session, CI-enforced process. Layer A (collaboration model) is kept, with every name, account and model turned into an injection point; layer B (parallelism and guards) is generalized; layer C (project content) is dropped.

## 4. 已定案的決策

| # | 問題 | 決定 | 後果 |
| --- | --- | --- | --- |
| D1 | 與 v1 的關係 | sop-v2 取代 v1；v1 的學習、`@claude` review、文件檢查收為可選模組 | 只維護一套範本 |
| D2 | 發布機制 | **Copier** | 參數化、可 `copier update`；多一個工具依賴（第 14 節） |
| D3 | 文件語言 | 專案選定（必答，無預設） | 範本自身文件只維護一份；語言設定決定專案產出（PR、issue、報告）的語言 |
| D4 | 機器帳號 | 注入點，必答，啟動時驗證 | 見第 15 節 |
| D5 | 學習模組 | 可選模組，必須明確選開或關 | 見第 13 節 |
| D6 | 範本定義 | **P1 可分享、P2 先完整才開工** | 所有注入點無預設值；新增啟動閘門與範本個資掃描 |
| D7 | GitHub 的 template repository 設定 | **不開啟** | 「Use this template」會繞過 Copier（L1），使用者會拿到未渲染的 `.jinja` 檔；只提供 Copier 一種建立方式 |
| D8 | 設計文件格式 | Markdown | 在 GitHub 上直接閱讀、diff 易讀 |
| D9 | 授權 | **MIT-0**，著作權人「sop-v2 contributors」 | 範本內容會被複製進每個下游專案，MIT-0 不要求保留聲明，下游沒有負擔；授權檔不含個人名字，符合 P1；仍保留免責條款。`LICENSE` 只放在 repo 根目錄，不在 `template/` 內，所以產生的專案不會繼承它；第三方檔案的授權檔隨所屬模組一起產生 |

> **EN:** D1 replace v1, keeping its useful parts as optional modules; D2 distribute with Copier; D3 language is a required per-project choice; D4 the machine account is a required injection point verified at bootstrap; D5 the learning module is optional and must be explicitly chosen; D6 the template definition (P1, P2); D7 don't enable GitHub's "template repository" setting, because "Use this template" bypasses Copier and yields unrendered `.jinja` files; D8 the design doc is Markdown; D9 license MIT-0 held by "sop-v2 contributors": template content is copied into every downstream project, MIT-0 requires no notice there, names no person (P1), and keeps the warranty disclaimer. `LICENSE` sits at the repo root, outside `template/`, so generated projects don't inherit it; third-party license files ship with their modules.

## 5. 角色與權限

| 角色 | 是誰 | 做什麼 | 不做什麼 | 生命週期 |
| --- | --- | --- | --- | --- |
| **Owner** | 人 | 核准 milestone 計畫、回答升級 issue、審查並合併 `milestone/* → main`、指定各角色的模型、核准啟動閘門 | — | 永久 |
| **Chief of Staff** | 一個 Claude Code session | 切 ticket、排平行批次、開子 session、合併 ticket PR 進 milestone 分支、維護看板、寫 milestone 報告 | 不寫產品程式、不合併 `main` | 一個 milestone；中斷時由新 session 從 repo 接手 |
| **Builder** | 每張 ticket 一個全新 session | 先紅再綠、開 PR、附證據 | 不改唯讀路徑、不改範圍外檔案、不合併、不弱化測試 | 一張 ticket（含第一輪修正） |
| **Verifier** | 每個 PR 每一輪一個全新 session | 乾淨重跑、逐項檢查、變異抽查、寫 PASS / FAIL 留言 | 不修產品程式、不看 Builder 的對話、不合併 | 一輪驗證 |
| **Researcher**（可選） | Chief 內的 subagent | 規劃時的唯讀調查，回傳結論 | 不寫任何檔案 | 一次呼叫 |

**每條限制都要有執行點**

| 限制 | 執行點 |
| --- | --- |
| 只有 Owner 合併 `main` | GitHub ruleset：機器帳號無法更新 `main`（啟動閘門驗證） |
| Builder 不改範圍外檔案 | CI `path-scope` |
| Builder 不改規則、規格、看板 | CI `readonly-paths` |
| 不弱化測試 | CI `no-weakened-tests` |
| 只有機器帳號提交 | CI `commit-author` |
| Verifier 獨立 | dispatch 規則：全新 session，prompt 只給 PR 編號與 ticket 路徑 |
| 設定不完整時不能開工 | CI `sop-ready` 與 skill 開頭檢查（第 15 節） |
| Chief 只在 PASS 後合併 ticket PR | milestone 分支的 ruleset 要求 CI 全綠；PASS 目前由流程保證（第 18 節） |

> **EN:** Five roles: Owner (human), Chief of Staff (one session per milestone), Builder (fresh session per ticket), Verifier (fresh session per PR per round, never sees the Builder's conversation), optional Researcher (read-only subagent). Every "does not" maps to an enforcement point: a GitHub ruleset, a CI check, or a dispatch rule.

## 6. Milestone 與 ticket 的生命週期

**專案的第一天到一個 milestone 結束**（**粗體**是需要 Owner 的關卡）

```
copier copy（回答全部問題）
  → bootstrap-project
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

> **EN:** A project starts with Copier (all questions answered), the bootstrap skill, and an Owner-merged bootstrap PR; after that, each milestone has two Owner gates (plan approval, merge to main). Ticket states live only in `docs/board.md`, written only by the Chief.

## 7. 平行開發模式

### 7.1 可以同時進行的條件

兩張 ticket 可以同時進行，若且唯若：

1. **依賴：** 兩者的 `depends_on` 都已 merged。
2. **路徑不相交：** 兩者的 `allowed_paths` 沒有交集（例外見 7.3）。
3. **序列化資源不相交：** 兩者的 `serial` 沒有共同項目。
4. **容量：** 進行中（building、verifying、fixing）的 ticket 數小於專案選定的 `max_parallel`。

### 7.2 序列化資源

有些衝突不在檔案層級：兩張 ticket 改不同的 migration 檔，卻都改變 schema 的順序；兩張 ticket 都升級依賴，改的是同一份 lockfile。這類共用狀態用 `serial` 宣告，資源清單由專案在建立時選定（例如 `db-schema`、`lockfile`、`ci-config`、`public-api`）。CI 檢查宣告的資源都在清單內，且沒有另一張進行中的 ticket 宣告同一項。

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
- 參考專案的實測上限是 2–3 張。Copier 問題的說明文字會列出這個經驗值，但不提供預設值（P2）。

> **EN:** Two tickets may run together iff dependencies are merged, allowed paths don't overlap, serialized resources don't overlap, and the project's chosen `max_parallel` isn't reached. Append-only shared files are an explicit exception guarded by a CI check that diffs only add lines. The Chief schedules with a greedy topological sort ordered by critical-path length, judging overlap conservatively by static glob prefixes; PR-time path-scope checks actual files exactly. A cap of 2–3 worked in practice and is shown as guidance, not as a default.

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

> **EN:** Role definitions are separate from mechanisms; `docs/sop/dispatch.md` maps roles to mechanisms. Builders and Verifiers run as separate cloud sessions; the Researcher as an in-session subagent; Workflow scripts are off by default. The Verifier gets only the PR number and ticket path, so it isn't anchored on the Builder's reasoning. Builders subscribe to their own PR; the Chief tracks progress through session status, PR descriptions, verdicts and CI, never full transcripts.

## 9. Ticket 契約

Ticket 檔是 Chief 與 Builder 之間唯一的契約，也是 CI 的輸入。每個欄位都有排程用途或機器檢查：

```yaml
---
id: T-012                    # 與分支 ticket/T-012 對應（CI branch-ticket）
title: 一句話
milestone: M2
depends_on: [T-010]          # 排程
allowed_paths:               # CI path-scope；排程時判斷重疊
  - src/billing/**
  - tests/billing/**
  - docs/evidence/T-012/**
append_only:                 # 選填；須同時列在 allowed_paths，且在專案的 append_only 清單內
  - tests/implemented.txt
readonly_override:           # 選填；允許改動預設唯讀路徑，須 Owner 在計畫中核准
  - .github/workflows/ci.yml
serial: [db-schema]          # 選填；序列化資源
evidence: cli                # cli | screens | none；CI evidence 依此判定
done_when:                   # CI done-when：這些測試 ID 必須在 JUnit 結果中存在且通過
  - tests/billing/test_invoice.py::test_rounding
status: todo                 # 只由 Chief 修改（實際狀態以 board.md 為準）
---
```

本文的固定段落：`## 目標`、`## 要讀的檔案`（只讀這些，保護 Builder 的 context）、`## 完成條件`（人讀的版本，與 `done_when` 一一對應）、`## 不在範圍內`。

完成條件只寫在 ticket 檔，而且以 `done_when` 的形式可被機器判定。規格怎麼寫、測試用什麼框架，範本不管；範本只要求專案能把完成條件對應到 JUnit 結果中的測試 ID。

> **EN:** The ticket file is the only Chief–Builder contract and the input to CI. Each field has a scheduling use or a machine check. "Done" lives only in the ticket, as `done_when` test IDs the template can check regardless of how the project writes specs or tests.

## 10. CI 契約

### 10.1 兩層設計

| 檢查 | 層 | 內容 | 輸入 |
| --- | --- | --- | --- |
| `sop-ready` | 中立 | 啟動閘門：設定完整、沒有未渲染的佔位符、啟動驗證已核准（第 15 節） | `.sop/*.yml`、全 repo 文字 |
| `branch-ticket` | 中立 | 目標是 `milestone/*` 的 PR，來源分支必須是 `ticket/T-xxx`，且目標分支上有對應的 ticket 檔 | 分支名、檔案 |
| `path-scope` | 中立 | 每個變更檔案都符合 `allowed_paths` | `git diff --name-only` |
| `readonly-paths` | 中立 | 不得修改 `AGENTS.md`、`.sop/**`、`docs/sop/**`、`.claude/**`、`.github/**`、`docs/board.md`、`docs/decisions.md` 與專案選定的規格路徑；`readonly_override` 例外 | diff、ticket |
| `append-only` | 中立 | `append_only` 檔案的 diff 只有新增行 | `git diff` |
| `serial-resource` | 中立 | 宣告的資源在清單內，且沒有其他進行中的 ticket 宣告同一項 | ticket、`board.md` |
| `evidence` | 中立 | PR 說明的「證據」一節有 code block 或連到 `docs/evidence/T-xxx/`；`evidence: screens` 時至少一張圖 | PR body、檔案 |
| `commit-author` | 中立 | 每個 commit 的 GitHub 作者都是專案選定的機器帳號 | GitHub API、`.sop/config.yml` |
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

每一項檢查都至少有一個「會讓它失敗」的測試案例，證明檢查真的有效。這些測試只在 sop-v2 自己的 CI 執行，不會進入產生的專案。

> **EN:** Stack-neutral checks (sop-ready, branch-ticket, path-scope, readonly-paths, append-only, serial-resource, evidence, commit-author) need only git, YAML and the GitHub API; stack-specific ones (tests, no-weakened-tests, done-when) go through a single interface, `scripts/sop/test` writing JUnit XML. The shipped stub fails on purpose, making "wire up tests" part of the bootstrap gate. Every guard has a test proving it can fail.

## 11. 記憶與狀態

Context window 是短期記憶，用完即丟；要留下的事一律寫進 repo。

| 檔案 | 內容 | 寫入者 | 規則 | Copier update 時 |
| --- | --- | --- | --- | --- |
| `AGENTS.md` | 永遠適用的規則摘要 | 範本；專案段落由 Chief 經 Owner 核准修改 | 只放規則與連結；專案段落以標記隔開 | 範本段落更新 |
| `.sop/config.yml` | 注入值 | Copier | 只能透過 `copier update` 重新回答來改 | 重新渲染 |
| `.sop/bootstrap.yml` | 啟動驗證結果 | `bootstrap-project` skill；Owner 合併時核准 | 見第 15 節 | 不覆寫 |
| `docs/sop/**` | 完整流程 | 範本 | 專案不改；要改就回饋到 sop-v2 | 更新 |
| `docs/board.md` | ticket 狀態、各輪使用的模型 | Chief | 單一事實來源 | 不覆寫 |
| `docs/decisions.md` | Owner 的決定 | Chief | 只增不改；推翻時新增一列並註明取代哪列 | 不覆寫 |
| `docs/pitfalls.md` | 下一個 agent 不知道就會再犯的事 | Chief（milestone 結束時） | 上限 30 條 | 不覆寫 |
| `docs/tickets/*.md` | 任務契約 | Chief | 完成條件只在這裡 | 不覆寫 |
| `docs/milestones/Mx.md` | 給 Owner 的報告 | Chief | 數字可重算；每個「已驗證」都連到證據 | 不覆寫 |

> **EN:** Anything that must outlive a context window goes into the repo. Template-owned files (AGENTS.md template sections, `docs/sop/**`) update via Copier; injected values live in `.sop/config.yml` and change only by re-answering through Copier; project-owned files (board, decisions, pitfalls, tickets, reports, bootstrap results) are never overwritten.

## 12. 升級、修正輪與證據

**什麼時候停下來找 Owner**

1. 規格不清楚或互相矛盾。
2. 需要改資料模型或公開介面，而 ticket 沒有授權。
3. 第二輪修正後 Verifier 仍判定 FAIL。
4. 專案選定的敏感領域（例如權限、金額、加密）沒有測試涵蓋。

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

每個模組都是一個必答的是／否問題，沒有預設值。關閉的模組不會產生任何檔案（Copier 的條件檔名）。

| 模組 | Copier 問題 | 內容 | 開啟後的啟動驗證 |
| --- | --- | --- | --- |
| 學習 | `enable_learning` | milestone 報告加「Q1–Q4」一節（Owner 先答，Chief 再比較差異）；決策紀錄加 Owner 的回答欄；附教學與追問用的 skills | 無 |
| `@claude` review | `enable_claude_review` | PR 上提及 `@claude` 觸發審查的 workflow | repo secret 已設定 |
| 文件檢查 | `enable_docs_lint` | Markdown 格式與連結檢查 | 無 |
| 測試介面範例 | `test_interface_example` | `none` 或某個語言的 `scripts/sop/test` 範例 | 仍須實際能產生 JUnit XML |

> **EN:** Each optional module is a required yes/no question with no default: learning (Q1–Q4 in milestone reports, teaching skills), @claude review (needs a repo secret, verified at bootstrap), docs lint, and a language-specific example of the test interface. Disabled modules produce no files.

## 14. 注入點與 Copier

### 14.1 為什麼是 Copier

| | GitHub template | Copier |
| --- | --- | --- |
| 參數化 | 無；手動改佔位符，容易漏 | 有；問題答案渲染進檔案，可設必答與格式驗證 |
| 之後的範本改進 | 拿不到 | `copier update` 以三方合併套用 |
| 代價 | 無 | 需安裝 copier；範本檔要注意 Jinja 語法衝突 |

P2 是選 Copier 的另一個理由：GitHub template 無法強制「先填完」，Copier 可以。也因此本 repo **不開啟** GitHub 的 template repository 設定（D7）：「Use this template」會複製出未渲染的 `.jinja` 檔，完全繞過 L1。

### 14.2 注入點清單

全部必答，**沒有預設值**。說明文字可以列出建議值，但使用者必須自己輸入或選擇。

| 問題 | 型別與驗證 | 用途 |
| --- | --- | --- |
| `project_name` | 字串，非空 | 文件標題、報告 |
| `project_goal` | 字串，一句話，非空 | `AGENTS.md` 的專案段落 |
| `owner_display_name` | 字串，非空 | 文件中稱呼 Owner 的名字 |
| `owner_github` | GitHub login 格式 | 計畫 issue 與 milestone PR 的指派對象 |
| `bot_github` | GitHub login 格式，且不可等於 `owner_github` | `commit-author`；身分檢查 |
| `bot_github_id` | 正整數 | 機器帳號的 noreply email |
| `doc_language` | 選項：`zh-TW` / `en` / … | 專案產出的語言 |
| `max_parallel` | 整數 1–5 | 平行上限 |
| `spec_paths` | glob 清單，可為空但必須明確回答 | 額外的唯讀路徑 |
| `serial_resources` | 名稱清單，可為空但必須明確回答 | 序列化資源 |
| `append_only_files` | 路徑清單，可為空但必須明確回答 | 只增檔案 |
| `sensitive_areas` | 字串清單，可為空但必須明確回答 | 升級條件第 4 條 |
| `enable_*`、`test_interface_example` | 是／否、選項 | 可選模組 |

模型分配不在注入點中：它由 Owner 在每個 milestone 的計畫核准時指定，記在看板上，因為模型會隨時間更換。

### 14.3 注入值存放的位置

值集中在一個由 Copier 渲染的 `.sop/config.yml`，其他檔案在執行時讀取它，而不是把值散布到各處。理由：

- GitHub Actions 的 `${{ }}` 與 Jinja 語法衝突，workflow 檔不適合用模板渲染。
- 只有一處需要驗證完整性，`sop-ready` 檢查最簡單。
- 文件（例如 `AGENTS.md`）中需要顯示的值仍可渲染，但只渲染少數幾個欄位。

### 14.4 更新流程

1. sop-v2 合併改進後打 semver tag（例如 `v2.1.0`）。
2. 專案中執行 `copier update`，在 `sop/update-v2.1.0` 分支產生 PR。新版本若新增注入點，Copier 會要求回答，同樣沒有預設值，所以 P2 在更新時也成立。
3. 這個 PR 會改到唯讀路徑，只能由 Owner 審查合併，不經 ticket 流程。

> **EN:** Copier over GitHub templates because it parameterizes files, can enforce required answers and formats (GitHub templates can't enforce P2), and `copier update` three-way-merges later improvements. For the same reason this repo does not enable GitHub's template-repository setting. Every injection point is required with no default; help text may suggest values. Model assignment is deliberately not an injection point. Values live in one rendered `.sop/config.yml` read at runtime. Updates are semver tags applied via an Owner-reviewed PR; any new question in an update is also required, so P2 holds over time.

## 15. 啟動閘門

P2 用三層來保證。每一層防的情況不同，缺一層就有漏洞：

| 層 | 機制 | 防的情況 | 擋不到的情況 |
| --- | --- | --- | --- |
| **L1 建立時** | Copier 必答問題 + 格式驗證 | 漏填、格式錯（例如帳號不合法、機器帳號與 Owner 相同） | 值格式正確但事實錯誤；不用 Copier、直接複製檔案 |
| **L2 repo 層** | CI `sop-ready`，對所有目標為 `main` 或 `milestone/*` 的 PR 執行 | 直接複製檔案而留下的佔位符；設定被刪改；啟動驗證未核准 | agent 不開 PR、直接在本機開工 |
| **L3 agent 層** | 每個 skill 的第一步都是讀 `.sop/bootstrap.yml`，`ready` 不是 true 就停止並告訴 Owner | agent 在閘門通過前就開始規劃或實作 | 有人刻意繞過 skill（此時 L2 仍會擋住合併） |

**Copier 無法設定、必須驗證的事**

這些是 GitHub repo 的設定，不是檔案。`bootstrap-project` skill 逐項檢查，結果寫進 `.sop/bootstrap.yml`，每項附證據（API 回應或指令輸出）：

| # | 檢查 | 驗證方式 |
| --- | --- | --- |
| B1 | 目前 session 的 GitHub 身分等於 `bot_github` | 查詢目前登入的使用者 |
| B2 | 機器帳號是 collaborator，權限是 Write（不是 Admin） | repo collaborator API |
| B3 | `main` 有 ruleset：機器帳號無法直接更新 | branch rules API；無法讀取時由 Owner 提供設定畫面截圖 |
| B4 | `milestone/*` 有 ruleset：必須 PR、必須 CI 全綠 | 同上 |
| B5 | `scripts/sop/test` 已實作，能產生 JUnit XML | 實際執行 |
| B6 | （啟用 review 模組時）repo secret 已設定 | secret 名稱清單 API（不讀值） |
| B7 | repo 中沒有未渲染的佔位符 | 與 `sop-ready` 相同的掃描 |

**閘門如何打開**

1. `bootstrap-project` 在 `sop/bootstrap` 分支寫入檢查結果，全部通過時把 `ready` 設為 `true`，並開 PR 到 `main`。
2. 只有 Owner 能合併 `main`（B3 已驗證），所以**閘門最後一定經過 Owner 核准**。agent 自己無法把閘門打開。
3. 合併後，`sop-ready` 在 `main` 上為綠，`plan-milestone` 才能開始 M0。

若之後任何設定被改壞（例如有人改了 `.sop/config.yml`），`sop-ready` 會在下一個 PR 失敗，閘門自動關上。

> **EN:** P2 is enforced in three layers: L1 Copier required questions with validators; L2 the `sop-ready` CI check on every PR into main or milestone branches; L3 every skill first checks `.sop/bootstrap.yml` and stops if not ready. Repo settings Copier can't set (B1–B7) are verified by the bootstrap skill with evidence. The gate opens only when the Owner merges the bootstrap PR into main, which agents can't do, and it closes again automatically if config is later broken.

## 16. 範本的個資衛生

P1 要求 sop-v2 這個 repo 本身沒有個人資訊。做法：

- **內容：** 範本中的人一律以角色稱呼（Owner、Chief、機器帳號），具體值全部來自注入點。範例資料使用明顯虛構的值（例如 `example-owner`、`example-bot`）。
- **CI 掃描：** sop-v2 自己的 CI 掃描範本檔案中的 email、GitHub 帳號連結、`@` 提及等樣式。採**允許清單**：只允許虛構範例值與公開的工具來源（例如 GitHub Actions 官方 action）。不用禁止清單，因為禁止清單本身就得寫出要隱藏的個資。
- **Git 歷史：** commit 作者使用 noreply 位址；PR 合併前檢查新 commit 的作者資訊。歷史一旦含有個資，只能靠改寫歷史清除，所以要在合併前擋住。
- **使用紀錄不進範本：** 某個專案怎麼用這個範本、遇到什麼問題，留在那個專案的 repo；回饋到 sop-v2 時只寫成通用的規則。

注意：產生的專案中，`.copier-answers.yml` 與 `.sop/config.yml` 會存放 Owner 和機器帳號等資訊。這是使用者自己的專案，屬於預期行為；README 會說明這一點，讓公開專案的使用者知道哪些值會出現在 repo 中。

> **EN:** P1 for the template repo itself: people are referred to by role, concrete values come only from injection points, and examples use obviously fictional values. The template's CI scans for emails, account links and @-mentions against an allowlist (a denylist would itself have to contain the data it hides). Commits use noreply addresses, checked before merge, because history can only be cleaned by rewriting it. Generated projects do store owner and bot accounts in `.copier-answers.yml` and `.sop/config.yml`; that's expected, and the README says so.

## 17. Repo 結構

```text
sop-v2/
  copier.yml                      # 注入點（全部必答）、模組、_skip_if_exists、_subdirectory: template
  README.md                       # 使用方式、會寫進專案的資訊、版本紀錄
  LICENSE                         # MIT-0（不進專案，D9）
  docs/design/sop-v2-design.md    # 本文件（不進專案）
  tests/sop/                      # 檢查本身的測試（不進專案）
  .github/workflows/self-ci.yml   # 範本自己的 CI：guards 測試、個資掃描、渲染測試
  template/                       # 以下會被產生到專案
    CLAUDE.md                     # 一行：讀 AGENTS.md
    AGENTS.md.jinja               # 規則摘要；專案段落以標記隔開
    .sop/config.yml.jinja         # 注入值
    .sop/bootstrap.yml            # ready: false，B1–B7 待檢查
    docs/sop/
      workflow.md  parallel.md  dispatch.md  ci-contract.md  bootstrap.md
    docs/board.md  docs/decisions.md  docs/pitfalls.md
    docs/tickets/_template.md
    docs/milestones/README.md  docs/milestones/report-template.md
    .claude/skills/
      bootstrap-project/  plan-milestone/  build-ticket/
      verify-ticket/  ask-owner/  milestone-report/
      （學習模組開啟時另有教學與追問用的 skills）
    .github/
      ISSUE_TEMPLATE/plan-approval.md  ISSUE_TEMPLATE/needs-owner.md
      PULL_REQUEST_TEMPLATE.md
      workflows/sop-guards.yml
    scripts/sop/
      guards.py                   # 中立檢查，僅用標準函式庫
      compare_junit.py            # no-weakened-tests、done-when
      test                        # 介面；預設失敗
```

> **EN:** The template lives under `template/` (Copier's `_subdirectory`), keeping the design doc, the guards' tests and the template's own CI (guard tests, personal-data scan, render tests) out of generated projects.

## 18. 失效情境與最壞影響

| 情境 | 後果 | 對策 |
| --- | --- | --- |
| 規格本身是錯的 | 全綠但行為錯 | milestone 報告必須列出「agent 自行做的判斷」；Owner 對照實際需求審查 |
| 測試步驟造假（永遠通過） | 全綠但沒驗證到 | Verifier 變異抽查：故意改壞產品程式，確認對應測試會失敗 |
| 檢查本身有 bug | **所有下游專案**被擋或漏放 | 每項檢查都有會失敗的測試；semver 發布；下游可用 `copier update --vcs-ref` 回到前一版 |
| 啟動閘門過嚴（例如 API 讀不到 ruleset） | 新專案無法開工 | B3、B4 允許 Owner 以截圖證據核准；閘門的打開永遠需要 Owner 合併 |
| 值格式正確但事實錯誤（例如填錯機器帳號） | 身分檢查失敗或防護失效 | B1、B2 用 API 驗證實際狀態，不只驗格式 |
| 不經 Copier、直接複製檔案 | 佔位符殘留 | L2 `sop-ready` 掃描未渲染的佔位符 |
| 個資混進範本 | 違反 P1，分享時外洩 | 允許清單掃描；PR 檢查 commit 作者 |
| 路徑重疊判定太保守 | 平行度下降 | 可接受；Chief 可在計畫中列出「人工確認不重疊」由 Owner 核准 |
| Verifier PASS 只靠流程 | Chief 可能在沒有 PASS 時合併 | 候選改進：CI 檢查 PR 上有機器帳號留下、格式正確、對應目前 head SHA 的 PASS 留言 |
| Chief session 中斷 | 進度停住 | 狀態全在 repo；新 Chief 讀看板與 PR 狀態接手 |
| 平行開太多 | 成本 ×2N、Chief context 爆掉 | 上限由專案選定並寫進設定；修正輪上限 2 |

**最壞影響與回滾：** sop-v2 只是範本，建立它不影響任何現有專案。風險在之後：檢查的 bug 會擴散到所有下游專案，啟動閘門過嚴會讓新專案無法開工。回滾方式：下游以 `copier update --vcs-ref` 回到前一個 tag；sop-v2 以 revert 修正後發新的 patch 版。

> **EN:** Creating sop-v2 touches no existing project. Later risks are guard bugs propagating downstream and an overly strict gate blocking new projects. Roll back per project with `copier update --vcs-ref`; fix sop-v2 with a revert and a new patch release.

## 19. 實作計畫

| 階段 | 內容 | 完成條件 |
| --- | --- | --- |
| S0 骨架 | `copier.yml`（全部注入點、驗證）、`template/`、自我 CI 的框架 | 渲染測試：缺任何一個答案都無法產生專案；給齊答案能產生預期檔案 |
| S1 協作文件 | 去專案化的 `AGENTS.md`、`docs/sop/*`、6 個 skills、issue / PR 樣板、看板與 ticket 樣板、報告樣板 | 個資掃描通過；所有具體值都來自注入點 |
| S2 檢查 | `guards.py`（含 `sop-ready`）、`compare_junit.py`、`sop-guards.yml`、`tests/sop/` | 每項檢查至少一個會失敗的測試；自我 CI 全綠 |
| S3 啟動閘門與模組 | `bootstrap-project` skill、B1–B7、可選模組 | 各模組開關組合都能產生；未完成啟動時 `sop-ready` 失敗，完成後通過 |
| S4 試用 | 用 sop-v2 產生一個測試專案，走完啟動閘門，再讓一張假 ticket 走完 Builder → Verifier → 合併 | 流程走得通；發 `v2.0.0` |

> **EN:** S0 skeleton and Copier config (a render test proves any missing answer blocks generation); S1 de-projectized docs and skills passing the personal-data scan; S2 guards with failing-case tests; S3 bootstrap gate and modules; S4 a trial project through the gate and one dummy ticket through the full loop, then tag v2.0.0.

## 20. 待決問題

1. **Copier 必答行為：** 需要在 S0 用測試確認「沒有預設值的問題」在互動模式與非互動模式（`--data`、`--defaults`）下都無法略過；若某種模式會略過，改由 `validator` 拒絕空值。
2. **Ruleset 的可讀性：** 以機器帳號（非 Admin）能否透過 API 讀到 branch rules，決定 B3、B4 能否全自動驗證。
3. **Verifier PASS 的機器檢查** 放進 v2.0 還是 v2.1。
4. ~~**授權條款**~~：已決定，見 D9。

> **EN:** Open: (1) verify in S0 that Copier can't skip default-less questions in any mode, else reject empty values via validators; (2) whether a non-admin machine account can read branch rules via the API (decides if B3/B4 are fully automatic); (3) whether the Verifier-PASS machine check ships in v2.0 or v2.1. (4) License: resolved, see D9.
