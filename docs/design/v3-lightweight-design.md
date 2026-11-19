# sop-v2 輕量化重新設計 / Lightweight redesign (v3 draft)

- 版本：草稿 0.1（2026-11-19）
- 狀態：**待 Owner 審閱**，還沒有任何實作
- 前一版：[`sop-v2-design.md`](sop-v2-design.md)（v0.12，重量版，凍結在 `v2.0.0-rc.1`）

> **EN:** Draft 0.1, awaiting Owner review; nothing is implemented yet. The previous heavyweight design is frozen at `v2.0.0-rc.1`.

## 目錄 / Contents

1. [為什麼重做](#1-為什麼重做--why-redo-it)
2. [設計原則](#2-設計原則--principles)
3. [保留、刪除、搬移](#3-保留刪除搬移--keep-drop-move)
4. [Repo 結構](#4-repo-結構--repo-layout)
5. [Skill 清單](#5-skill-清單--the-skills)
6. [每個專案的設定](#6-每個專案的設定--per-project-config)
7. [Ticket 格式](#7-ticket-格式--ticket-format)
8. [護欄食譜](#8-護欄食譜--guardrail-recipes)
9. [發佈與更新](#9-發佈與更新--distribution-and-updates)
10. [已定案的決策](#10-已定案的決策--decisions)
11. [失效情境與最壞影響](#11-失效情境與最壞影響--failure-modes)
12. [從 v2 搬移](#12-從-v2-搬移--migrating-from-v2)
13. [實作計畫](#13-實作計畫--implementation-plan)
14. [待決問題](#14-待決問題--open-questions)

## 1. 為什麼重做 / Why redo it

S4 試用（一個從 `v2.0.0-rc.1` 建立的私人試用 repo）顯示，v2 在**開始寫第一行產品程式之前**就要求：

- 回答 16 個設定題目，沒有任何預設值（P2）；
- 通過 B1–B7 七項 repo 查證，其中 B3、B4 需要 Owner 手動設定 ruleset 與 11 個必要檢查；
- 理解 11 項 CI 檢查、唯讀路徑、`managed.txt`、`sop-sync` 與四個角色。

試用中，啟動 PR 第一次跑 CI 就碰到兩個範本自己的 bug，ruleset 也設錯（Target branches 為空）。重量主要來自**強制機制**，而不是流程本身：v2 的 8 個 skill 一共不到 400 行，但檢查、閘門、同步程式加上測試超過 5,000 行。

Owner 的結論：流程太繁瑣，限制了開發。方向改為公開的 skill 合集 `mattpocock/skills` 那一類：**小、可組合、使用者保有控制權**；但留下足夠的文件，讓使用者需要時自己加上 CI gate 等防護。

> **EN:** The S4 trial showed that v2 demands 16 default-less config answers, seven repo checks (two needing hand-built rulesets and 11 required checks), and an understanding of 11 CI checks, read-only paths, managed paths, sync and four roles before the first line of product code. The first bootstrap PR hit two template bugs and a misconfigured ruleset. The weight is enforcement, not process: under 400 lines of skills versus over 5,000 lines of gate, guard and sync code plus tests. The Owner's call: go lightweight, like the composable `mattpocock/skills` pack, while documenting enough that users can add CI gates and other guardrails themselves.

## 2. 設計原則 / Principles

| # | 原則 | 意思 |
| --- | --- | --- |
| R1 | **流程在 skill，保證在使用者手上** | skill 教 agent 怎麼做（先紅後綠、冷讀驗證、附證據）；能不能被 CI 擋下，由使用者照食譜自己決定要不要加 |
| R2 | **每個 skill 都能單獨用** | 不需要先跑完整套流程；只用 `/verify` 或只用 `tdd` 都可以 |
| R3 | **兩種 skill** | **使用者呼叫**（編排一段工作，`disable-model-invocation: true`）與**模型呼叫**（可重用的紀律）。編排型可以呼叫紀律型，編排型之間不互相呼叫 |
| R4 | **沒有閘門** | 缺設定時 skill 提示使用者去跑 `/setup`，然後照常工作或停在那一步；不擋整個 repo |
| R5 | **慢慢加煞車** | 防護從最便宜的開始（CI 跑測試 → 保護 `main` → …），每加一項都說明防什麼、代價是什麼 |
| R6 | **P1 不變** | 範本與 plugin 不含任何個人資訊；所有人和專案的值都在使用者自己的 repo |
| R7 | **短** | 每個 `SKILL.md` 目標 ≤ 80 行；細節放在同目錄的參考檔，需要時才讀 |

P2（先完整才開工）**取消**，理由見 D44。

> **EN:** R1 skills carry the process; whether CI enforces anything is the user's choice, guided by recipes. R2 every skill stands alone. R3 two kinds: user-invoked orchestrators and model-invoked disciplines; orchestrators may call disciplines, never each other. R4 no gate: missing config points to `/setup`. R5 add brakes gradually, cheapest first, each with its purpose and cost. R6 P1 unchanged. R7 short skills (≤ 80 lines), details in sibling reference files. P2 is dropped (D44).

## 3. 保留、刪除、搬移 / Keep, drop, move

| v2 的部分 | v3 | 理由 |
| --- | --- | --- |
| 四個角色（Owner / Chief / Builder / Verifier） | **保留為概念**，寫在 `docs/concepts/roles.md`；一個人一個 session 也能用 | 角色分工是參考專案驗證過的核心價值；但不強迫 |
| 先紅後綠、Verifier 冷讀、兩輪後升級、證據與模型署名 | **保留**，寫進對應的 skill | 這是流程，不是強制 |
| 「agent 以機器帳號留下紀錄」 | **保留**為 skill 規則 + 食譜 G4 | Owner 的長期要求：之後多個 agent 可依 GitHub 帳號區分 |
| 看板、決策紀錄、pitfalls | **保留為可選檔案**，`/setup` 時選擇要不要建立 | 對多 session 有用，對單人小專案是負擔 |
| `.sop/config.yml` + schema + YAML 子集 parser | **刪除**，改成一份 Markdown 設定（第 6 節） | agent 讀 Markdown 就夠；不需要機器驗證 |
| 啟動閘門（L1–L3、B1–B7、`sop-ready`） | **刪除**；B1–B7 的內容搬進食譜 | R4 |
| 11 項 CI 檢查（`guards.py` 等） | **搬移**成食譜的可複製檔（第 8 節） | R1；程式碼與測試可以重用 |
| `managed.txt`、`template-only.txt`、`sop-sync` | **刪除**；改用 plugin 自動更新（第 9 節） | 食譜複製後歸使用者所有，不需要同步 |
| 可選模組（learning、claude_review、docs_lint） | learning → 可選 skill；claude_review、docs_lint → 食譜 | 模組開關的機制隨設定檔一起刪除 |
| milestone 分支與 HTML 報告 | **可選**：`/plan` 可以用 milestone 分支，也可以直接對 `main` 開 PR | 小專案不需要兩層分支 |

> **EN:** Kept as concepts or skill rules: the four roles (documented, not enforced), red-green, the cold-reading Verifier, two-round escalation, evidence and model attribution, and agents acting as the machine account. Optional: board, decision log, pitfalls, milestone branches and HTML reports. Dropped: the YAML config and schema, the bootstrap gate, managed/template-only lists and sync. Moved into recipes: the 11 CI checks, B1–B7 setup steps, claude_review and docs_lint.

## 4. Repo 結構 / Repo layout

```text
.claude-plugin/
  plugin.json          # plugin 清單：明列每個 skill 的路徑
  marketplace.json     # 讓 repo 本身可以當單一 plugin 的 marketplace
skills/
  <name>/SKILL.md      # 每個 skill 一個目錄；細節放同目錄的 *.md
docs/
  concepts/            # 角色、ticket、證據、升級：給人讀的說明
  guardrails/          # 護欄食譜：每項一篇 + files/ 可複製檔
  design/              # 設計文件（v2 凍結版、本文件）
tests/                 # 範本自己的測試：frontmatter、連結、個資掃描、食譜
.github/workflows/
  self-ci.yml          # 範本自己的 CI（不是給使用者的）
README.md              # 安裝、30 秒上手、skill 一覽
```

範本 repo **不再是**「Use this template」的來源：使用者的 repo 不需要長得像它，只要裝 plugin 或複製 skill。

> **EN:** Plugin manifests, one directory per skill, human-facing concept docs, guardrail recipes with copyable files, design docs, the template's own tests and CI, and a README. The repo stops being a "Use this template" source: users install the plugin or copy skills, and their repo needn't resemble this one.

## 5. Skill 清單 / The skills

### 使用者呼叫（編排）/ User-invoked

| Skill | 做什麼 | 對應 v2 |
| --- | --- | --- |
| `/setup` | 探索 repo，問 2–4 題，寫 `docs/agents/harness.md`；最後**推薦**第一個值得加的護欄，但不強迫 | `bootstrap-project`（大幅縮小） |
| `/plan` | 把一段需求切成 tracer-bullet ticket（每張是可驗證的垂直切片），標出依賴，請 Owner 確認後寫到設定的 ticket 位置 | `plan-milestone` |
| `/build <ticket>` | 讀一張 ticket，用 `tdd` 先紅後綠，用 `evidence` 整理證據，開 PR | `build-ticket` |
| `/verify <PR>` | 用**全新的 subagent**（不帶 Builder 的對話）從乾淨 checkout 重跑，依 ticket 與 diff 判 PASS / FAIL，寫成 PR 留言 | `verify-ticket` |
| `/report` | 把一批合併的 ticket 整理成給 Owner 的報告（Markdown 或 HTML） | `milestone-report` |

### 模型呼叫（紀律）/ Model-invoked

| Skill | 做什麼 |
| --- | --- |
| `tdd` | 先寫會失敗的測試、確認它真的失敗、再實作；不弱化測試的規則 |
| `evidence` | 「已驗證」必須附什麼：指令與輸出、截圖位置、模型名稱（從 session 設定取得） |
| `ask-owner` | 規格不清、需要未授權的變更、兩輪修正失敗時，開 issue：兩三個選項、各自後果、建議 |
| `learning`（可選） | 報告後請 Owner 先回答四個問題，再比較與記錄 |

所有 skill 第一步讀 `docs/agents/harness.md`；檔案不存在時說一句「建議先跑 `/setup`」，然後用合理的預設繼續（例如 issue tracker 用目前 repo 的 GitHub Issues）。

> **EN:** User-invoked: `/setup` (explore, ask 2–4 questions, write `docs/agents/harness.md`, recommend a first guardrail), `/plan` (tracer-bullet tickets with dependencies), `/build` (red-green via `tdd`, evidence, PR), `/verify` (a fresh subagent re-runs from a clean checkout and posts PASS/FAIL), `/report`. Model-invoked: `tdd`, `evidence`, `ask-owner`, optional `learning`. Every skill reads `docs/agents/harness.md` first; if it's missing, it suggests `/setup` and continues with sensible defaults.

## 6. 每個專案的設定 / Per-project config

`/setup` 寫一份給 agent 讀的 Markdown，不做 schema 驗證：

```markdown
# Harness

- Owner：example-owner（只有 Owner 合併 main）
- 機器帳號：example-bot（agent 的 push、PR、留言都用這個帳號；沒有就寫「無」）
- Issue tracker：GitHub Issues（本 repo）
- Ticket 位置：GitHub Issues，標籤 `ticket`   # 或 docs/tickets/*.md
- 測試指令：`pytest`
- 文件語言：zh-TW
- 紀錄檔：board 否、decisions 是、pitfalls 是
- 已啟用的護欄：G1、G2              # 由食譜的「完成後」步驟更新
```

這份檔案**屬於使用者的 repo**，可能含真實帳號，所以不在範本中出現；範本只有虛構範例（R6）。

> **EN:** `/setup` writes a plain Markdown file for agents, with no schema: Owner, machine account (or none), tracker, ticket location, test command, doc language, which record files to keep, and which guardrails are enabled. It lives in the user's repo and may hold real accounts; the template ships only fictional examples.

## 7. Ticket 格式 / Ticket format

最小格式，四個欄位：

| 欄位 | 必填 | 用途 |
| --- | --- | --- |
| 標題與目標 | 是 | 一兩句話：完成後能做到什麼 |
| 完成條件 | 是 | 每條對應一個測試（或一個可重跑的指令） |
| 依賴 | 否 | 哪些 ticket 必須先完成 |
| 範圍 | 否 | 預期會改的路徑；加了食譜 G5 之後由 CI 檢查 |

v2 的其他欄位（`append_only`、`serial`、`screens`、`done_when` 的測試 ID）在對應食譜裡說明：**加那個護欄時才需要加那個欄位**。

> **EN:** Four fields: title and goal, done-when conditions (each tied to a test or re-runnable command), optional dependencies, optional scope. v2's other fields are introduced by the recipes that need them, only when the user adds that guardrail.

## 8. 護欄食譜 / Guardrail recipes

### 8.1 每篇食譜的固定格式 / Recipe format

每篇 `docs/guardrails/Gx-<name>.md` 都有六節：

1. **防什麼**：沒有它時會發生的具體事故。
2. **什麼時候值得加**：訊號（例如「開始有第二個 agent 同時工作」）。
3. **怎麼加**：步驟，加上 `docs/guardrails/files/Gx/` 的可複製檔（腳本、workflow 片段、ruleset 設定）。複製之後檔案歸使用者所有。
4. **怎麼證明有效**：一個會讓它失敗的操作，以及預期看到的輸出。
5. **代價與誤擋**：多花多少 CI 時間、哪些正常情況會被擋、怎麼處理。
6. **完成後**：在 `docs/agents/harness.md` 的「已啟用的護欄」記一筆；需要時更新 ticket 格式。

> **EN:** Each recipe has six sections: what it guards against, when it's worth adding, how to add it (steps plus copyable files that the user then owns), how to prove it works (a failing case and expected output), cost and false positives, and what to record afterwards.

### 8.2 食譜清單（依建議順序）/ Catalogue, in suggested order

| # | 食譜 | 來源（v2） | 需要 |
| --- | --- | --- | --- |
| G1 | CI 跑測試，產生 JUnit XML | `tests`、`scripts/sop/test` 契約 | 測試指令 |
| G2 | 保護 `main`：ruleset、只有 Owner 能合併、必要檢查 | `setup.md`、B3、B4 | repo 管理員 |
| G3 | 機器帳號：建立、權限 Write、token、commit 作者設定 | B1、B2、`--git-identity` | 一個 GitHub 帳號 |
| G4 | Commit 作者檢查 | `commit-author` | G3 |
| G5 | 範圍檢查：PR 只改 ticket 列出的路徑 | `path-scope`、`branch-ticket` | ticket 的「範圍」欄位 |
| G6 | 唯讀路徑：規則、規格、CI 設定不能被 agent 的 PR 改動 | `readonly-paths` | G5 |
| G7 | 不弱化測試：目標分支通過的測試，PR 上也必須存在且通過 | `no-weakened-tests`、`compare_junit.py` | G1 |
| G8 | 完成條件對應測試 | `done-when` | G1、ticket 完成條件寫測試 ID |
| G9 | 證據檢查：PR 說明一定要有證據一節 | `evidence` | PR 範本 |
| G10 | 只增檔案（例如 CHANGELOG） | `append-only` | — |
| G11 | 序列化資源（例如 migration、lockfile 一次一張 ticket） | `serial-resource` | 看板或 ticket 標籤 |
| G12 | AI 審查（`@claude` 在 PR 上提供意見） | `claude_review` 模組 | API key secret |
| G13 | 文件檢查（連結、雙語段落） | `docs_lint` 模組 | — |

`docs/guardrails/README.md` 另外放一張「症狀 → 食譜」表，例如「agent 改了不該改的檔案 → G5、G6」「測試被刪了還是綠的 → G7」。

> **EN:** Thirteen recipes in suggested order: G1 CI tests with JUnit, G2 protect `main`, G3 machine account, G4 commit author, G5 scope, G6 read-only paths, G7 no weakened tests, G8 done-when, G9 evidence, G10 append-only files, G11 serial resources, G12 AI review, G13 docs lint. Each is sourced from a v2 check or setup step. The guardrails README adds a symptom-to-recipe table.

### 8.3 可複製檔的原則 / Copyable files

- 只用 Python 標準函式庫與 `git`，不需要安裝套件。
- 每個檢查一個獨立檔案（不再是一個 `guards.py` 包全部），複製一個不需要其他檔案。
- 設定寫在檔案開頭的常數或 workflow 的 `env:`，不讀 YAML 設定檔。
- 範本的 `tests/` 為每個可複製檔保留 v2 的「會讓它失敗」測試，保證食譜的程式真的有效。

> **EN:** Copyable files use only the Python standard library and git, one standalone file per check, configured by constants or workflow `env:` rather than a config file. The template's own tests keep v2's failing cases for each file.

## 9. 發佈與更新 / Distribution and updates

| 方式 | 指令 | 更新 | 適合 |
| --- | --- | --- | --- |
| **Plugin** | 在 Claude Code 加入本 repo 為 marketplace 後安裝 | plugin 版本號改變時自動更新 | 想直接用、不想改 skill 的人 |
| **複製** | 把 `skills/<name>/` 複製到專案的 `.claude/skills/` | 自己比對 diff | 想改 skill 內容的人 |

- 食譜的可複製檔**不透過 plugin 發佈**（plugin 只放 skill）；使用者照食譜複製，之後自己維護。
- 版本號：`plugin.json` 的 `version` 與 git tag 一致；重大改變寫在 `CHANGELOG.md`，食譜改動也記在這裡，讓使用者知道要不要重新複製。

> **EN:** Two routes: install as a plugin (auto-updates on version bumps) or copy skill directories and maintain them yourself. Recipe files are never distributed by the plugin; users copy and own them. The plugin version matches the git tag, and `CHANGELOG.md` records skill and recipe changes so users know when to re-copy.

## 10. 已定案的決策 / Decisions

編號接續 v2 設計文件（D1–D43）。

| # | 決策 | 選擇 | 影響 |
| --- | --- | --- | --- |
| D44 | 整體方向（2026-11-19） | **改成輕量、可組合的 skill 包**，強制機制改成文件化的食譜；取消 P2 與啟動閘門 | 取代 D1–D43 中關於閘門、設定 schema、同步的決策；v2 凍結 |
| D45 | 護欄程式怎麼交付（2026-11-19） | **食譜：文件 + 可複製檔**，使用者複製後自己擁有 | 不提供 reusable workflow；範本不需要維護使用者端的 workflow 版本 |
| D46 | skill 怎麼發佈（2026-11-19） | **Plugin 與直接複製兩種** | 取代 template repo 與 `sop-sync` |
| D47 | 既有 v2 工作（2026-11-19） | **凍結 v2，在新分支重做**：`v2.0.0-rc.1` 保留為重量版參考；PR #11 關閉不合併；試用 repo 之後改用來試輕量版 | 任何時候都能回到 rc.1；v2 的程式與測試在 git 歷史中完整保留 |

> **EN:** D44: go lightweight and composable, enforcement becomes documented recipes, P2 and the gate are dropped, v2 is frozen. D45: recipes are docs plus copyable files the user owns. D46: distribute as a plugin and by copying. D47: freeze v2 at `v2.0.0-rc.1`, close PR #11 unmerged, reuse the trial repo for the lightweight version later.

## 11. 失效情境與最壞影響 / Failure modes

| 情境 | 最壞影響 | 緩解 |
| --- | --- | --- |
| 使用者只裝 skill，沒加任何護欄 | agent 改了範圍外的檔案、或刪測試讓 CI 變綠，只能靠人工審查發現 | `/setup` 最後推薦 G1、G2；`/verify` 的檢查表包含「範圍」與「測試數量有沒有變少」，至少在審查層抓到 |
| agent 自己合併 `main` | 未審查的程式進入主線 | 沒加 G2 時無法阻止；README 的第一段與 `/setup` 都明確提醒 |
| 複製的食譜檔過時 | 檢查有 bug 卻沒更新 | CHANGELOG 標出食譜修正；食譜檔頭部寫來源版本 |
| plugin 自動更新改變 skill 行為 | 進行中的工作流程突然不同 | 語意化版本；破壞性變更只在 major 版本，並寫進 CHANGELOG |
| 沒有 `docs/agents/harness.md` | skill 用預設值，例如用錯 issue tracker | 每個 skill 開頭提示一次 `/setup`；預設值只用「目前 repo」這類安全的選擇 |

v2 的保證（agent 無法自己打開閘門、無法弱化測試）**只有在使用者加了對應食譜後才成立**。這是 D44 有意接受的取捨。

> **EN:** Without guardrails, out-of-scope edits and deleted tests are caught only by review; `/setup` recommends G1 and G2 and `/verify` checks scope and test counts. Without G2, nothing stops an agent merging `main`. Stale copied recipes, plugin behaviour changes and a missing config file are mitigated by the changelog, semver and a one-line `/setup` hint. v2's guarantees hold only once the matching recipe is added; D44 accepts that trade-off on purpose.

## 12. 從 v2 搬移 / Migrating from v2

| v2 檔案 | v3 去處 |
| --- | --- |
| `.claude/skills/{plan-milestone,build-ticket,verify-ticket,milestone-report,ask-owner,learning}` | `skills/{plan,build,verify,report,ask-owner,learning}`，刪掉閘門與設定檔的部分，縮短 |
| `.claude/skills/{bootstrap-project,sop-sync}` | `bootstrap-project` → `skills/setup`；`sop-sync` 刪除 |
| `scripts/sop/guards.py`、`compare_junit.py` | 拆成 `docs/guardrails/files/G4…G11/` 的獨立檔 |
| `scripts/sop/config.py`、`bootstrap`、`sync`、`.sop/**` | 刪除（`--git-identity` 的邏輯搬到 G3） |
| `docs/sop/setup.md` | 拆成 G2、G3 |
| `docs/sop/ci-contract.md` | 拆進 G1、G5–G11 |
| `docs/sop/{workflow,parallel,dispatch}.md` | 濃縮成 `docs/concepts/` |
| `docs/tickets/_template.md`、看板、決策、pitfalls、報告樣板 | 搬到對應 skill 的同目錄參考檔 |
| `tests/sop/*` | 保留：個資掃描、文件連結、frontmatter；檢查的測試跟著可複製檔走；閘門與同步的測試刪除 |
| `AGENTS.md`、`CLAUDE.md` | 範本本身的開發規則；不再發給使用者 |

> **EN:** Skills move to `skills/` and shrink; bootstrap becomes `setup` and sync is removed; `guards.py` and `compare_junit.py` split into standalone recipe files; config, bootstrap, sync and `.sop/` are deleted (the git-identity logic moves to G3); the SOP docs are split into recipes and condensed concept docs; templates move next to the skills that use them; tests for the PII scan, links and frontmatter stay, guard tests follow their files, and gate and sync tests go.

## 13. 實作計畫 / Implementation plan

每一步在本分支上做，完成後請 Owner 看過再進下一步。

| 步驟 | 內容 | 完成條件 |
| --- | --- | --- |
| V0 | 本文件定稿 | Owner 核准 |
| V1 | 骨架：`.claude-plugin/`、`skills/` 空目錄、README、self-ci、frontmatter 檢查、個資掃描 | self-ci 綠；`plugin.json` 列出的每個 skill 目錄都存在 |
| V2 | 核心 skill：`setup`、`tdd`、`evidence`、`build`、`verify` | 每個 ≤ 80 行；在試用 repo 用一張 ticket 跑完 `/build` → `/verify` |
| V3 | 其餘 skill：`plan`、`report`、`ask-owner`、`learning`；`docs/concepts/` | 試用 repo 跑一次 `/plan` |
| V4 | 食譜 G1–G7 與可複製檔、失敗案例測試 | 每篇六節齊全；每個可複製檔有會失敗的測試 |
| V5 | 食譜 G8–G13；症狀表；CHANGELOG；刪除 v2 檔案 | 試用 repo 照食譜加上 G1、G2、G5、G7，並證明它們會擋 |
| V6 | 發佈 `v3.0.0` | Owner 建立 release |

> **EN:** V0 approve this doc; V1 skeleton (plugin manifests, README, self-CI, frontmatter and PII checks); V2 core skills, exercised end to end on the trial repo; V3 remaining skills and concept docs; V4 recipes G1–G7 with failing-case tests; V5 G8–G13, symptom table, changelog, removal of v2 files, and adding G1, G2, G5, G7 to the trial repo with proof they block; V6 `v3.0.0` released by the Owner. The Owner reviews after each step.

## 14. 待決問題 / Open questions

| # | 問題 | 建議 |
| --- | --- | --- |
| O1 | `SKILL.md` 用什麼語言？雙語會讓每個 skill 長一倍，也多花 token | **skill 本文用英文**（給 agent 讀），`docs/` 與 README 維持中文優先的雙語（給人讀）；skill 產出的文件仍依 `docs/agents/harness.md` 的文件語言 |
| O2 | plugin 名稱 | 先用 repo 名稱；正式發佈前再定 |
| O3 | Chief 開多個子 session 的平行做法（v2 的 `dispatch.md`、`parallel.md`）要不要做成 skill | 先寫成 `docs/concepts/parallel.md` 的說明；有實際需求再做 skill |
| O4 | 範本 repo 自己的 commit 是否也改用機器帳號 | 沿用 v2 的未決狀態，等 Owner 決定 |

> **EN:** O1: write skill bodies in English for agents, keep human docs bilingual, and have skills produce documents in the configured language (recommended). O2: plugin name, decided before release. O3: document parallel multi-session dispatch first and turn it into a skill only on demand. O4: whether the template's own commits use the machine account is still open.
