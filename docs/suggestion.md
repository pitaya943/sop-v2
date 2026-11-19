# 各等級建議的元件 / What each level should have

這份文件說明一個用 agent 開發的專案，在每個等級**建議具備哪些元件**，以及每個元件**具體可以達成什麼結果、做不到什麼**。依據是前沿公司公開的 harness 文章，以及三個公開的 harness 實作（見[第 6 節](#6-來源--sources)）。等級與元件會隨研究更新，這份文件會跟著維護。

> **EN:** Which components a project developed with agents should have at each level, and exactly what each one achieves and can't achieve. Based on the frontier labs' published harness guidance and three public harnesses (section 6). This document is maintained as the research and levels evolve.

## 怎麼讀 / How to read this

每個元件都標出它靠哪一種**強制力**生效。這決定了它的保證有多可靠：

| 強制力 | 生效時機 | 可靠程度 | 代價 |
| --- | --- | --- | --- |
| **文字** | agent 讀到並遵守時 | 最低：agent 可能忽略或忘記 | 最低：寫文件 |
| **Session 機制** | agent 動手的當下（Claude Code 的 hook、權限設定） | 中：在 Claude Code 裡每次都會擋；換工具就沒有 | 低：一個提交進 repo 的設定檔 |
| **Merge 機制** | 合併 PR 時（CI、分支保護） | 最高：任何工具、任何人都繞不過（除了有 bypass 權限的人） | 中：要設 CI 與 ruleset，每個 PR 多等幾分鐘 |

原則：**沒有例外的規則，用最便宜而且夠用的機制保證**；只有需要判斷的事才留給文字。

> **EN:** Each component is tagged with how it's enforced, which sets how reliable its guarantee is:
> - **Prose** applies only when the agent reads and follows it, so it's the least reliable and the cheapest.
> - **Session mechanisms** (Claude Code hooks and permissions) act the moment the agent acts. They're reliable inside Claude Code but absent in other tools, and cheap: one committed settings file.
> - **Merge mechanisms** (CI and branch protection) apply when a PR merges. Nobody can get around them except someone with bypass rights, and they cost CI setup plus minutes per PR.
>
> Rule of thumb: enforce zero-exception rules with the cheapest mechanism that suffices, and leave only judgment calls to prose.

## 總覽 / Overview

| 等級 | 適合 | 一句話 |
| --- | --- | --- |
| [Level 0](#level-0只有-skill--skills-only) | 試用、不想改 repo | agent 有好的工作方法，但沒有任何東西擋得住它 |
| [Level 1](#level-1預設--the-default) | 一個人配一個或少數 agent（**建議所有專案至少到這裡**） | `main` 不會被 agent 直接改壞，測試一定被執行，機密讀不到，完成有獨立驗證 |
| [Level 2](#level-2多-agent-平行--parallel-agents) | 多個 agent 同時工作 | 每個 PR 只改自己的範圍，測試不能被偷偷刪掉，每個動作都能追到是哪個 agent |
| [Level 3](#level-3長時間自主--long-running-autonomy) | agent 長時間或在無人看管下工作 | 工作能跨 session 接續，品質可以量測，必要時能讓 agent 自己合併 |

**什麼時候升級：**

- **升到 Level 2：** 同時有第二個 agent 在改同一個 repo；或曾經發生 agent 改了範圍外的檔案、測試被刪了 CI 還是綠的。
- **升到 Level 3：** 一件工作要跨好幾個 session；或希望 agent 在沒人看的時候繼續做（例如夜間）。

> **EN:** Level 0 gives agents good habits but nothing stops them. Level 1, recommended as every project's minimum, keeps `main` safe from direct agent changes, always runs the tests, keeps secrets unreadable, and verifies "done" independently. Level 2 keeps each PR in scope, stops tests from being quietly removed, and traces every action to an agent. Level 3 lets work continue across sessions, makes quality measurable, and allows agent merges when the policy says so. Move to Level 2 when a second agent works in the same repo or an out-of-scope edit or deleted test slipped through; move to Level 3 when work spans several sessions or should continue unattended.

---

## Level 0：只有 skill / Skills only

安裝 plugin 即可，不改 repo 的任何設定。

| 元件 | 強制力 | 可達成的結果 | 做不到 |
| --- | --- | --- | --- |
| **`tdd` skill**（先紅後綠） | 文字 | agent 每個行為先寫會失敗的測試，確認失敗原因正確才實作；新功能都有測試，而且測試確實會在功能壞掉時失敗 | agent 不照做時沒有東西擋；不能防止 agent 事後刪測試 |
| **`evidence` skill**（證據規則） | 文字 | 每個「完成」都附指令與真實輸出，以及做這件事的模型名稱；審查者不用相信口頭說法 | 不能證明輸出不是捏造的；只有重跑才能確認 |
| **`build` skill** | 文字 | 一張 ticket 一個分支、一個 PR；PR 說明有固定格式，列出比規格更嚴格的斷言 | 不能保證 agent 只改範圍內的檔案 |
| **`verify` skill**（全新 subagent 冷讀） | 文字 | 由沒看過實作過程的 subagent 重跑測試、做突變抽查、找規格邊界情況，產出 PASS / FAIL 與證據；能抓到「測試其實沒在測」與規格漏洞（sop-trial 試跑時提出 3 個規格問題） | 驗證者和實作者是同一個模型，盲點可能相同；不能阻止沒驗證就合併 |

**這一級的風險：** agent 可以直接推送到 `main`、讀到 `.env`、刪掉失敗的測試讓結果變綠。所有保證都只靠 agent 自律。

> **EN:** Install the plugin; nothing in the repo changes.
> - **`tdd`:** each behaviour gets a failing test before the code, so new features have tests that actually fail when the feature breaks. Nothing enforces it, and it can't stop tests being deleted later.
> - **`evidence`:** every "done" comes with the command, its real output and the model that did the work. It can't prove the output wasn't made up; only a re-run can.
> - **`build`:** one ticket, one branch, one PR with a fixed description, listing assertions stricter than the spec. It can't keep edits in scope.
> - **`verify`:** a fresh subagent that never saw the work re-runs the tests, mutates the code and probes spec edge cases, then gives PASS or FAIL with evidence. It catches tests that test nothing, and spec gaps (3 in the sop-trial run). The verifier shares the builder's model and blind spots, and nothing stops an unverified merge.
>
> **Risk at this level:** an agent can push to `main`, read `.env` and delete failing tests. Every guarantee rests on the agent's discipline.

---

## Level 1：預設 / The default

`/setup` 會複製這些檔案。這一級的元件都很便宜，而且是所有來源一致同意的最低限度。

| 元件 | 強制力 | 可達成的結果 | 做不到 |
| --- | --- | --- | --- |
| **AGENTS.md 地圖**（≤ 100 行，CLAUDE.md 匯入它） | 文字 | 任何 agent 工具（Claude Code、Codex、Gemini CLI、Cursor）開工時都讀到同一份入口：測試指令、完成的定義、文件在哪；不用每次重新解釋專案 | 檔案太長時 agent 會略讀；不能強制遵守 |
| **`docs/agents/harness.md`** | 文字 | 所有 skill 讀同一份設定（Owner、機器帳號、測試指令、ticket 位置、自主程度、修正輪數），行為一致；換人或換 session 不會走樣 | 設定寫錯時 skill 會照著錯 |
| **一行跑完的測試指令** | 工具 | agent 每次改動後都能自己跑測試、看到結果、自己修，不用等人；這是 agent 能自我修正的前提 | 測試寫得不好時，綠燈不代表正確 |
| **CI 跑測試，設為 `main` 的必要檢查** | Merge 機制 | 測試沒通過的 PR **合併不了**，不管是哪個工具或哪個人開的；「我在本地跑過了」不再算數 | 不能防止測試被刪或被放寬（那是 Level 2 的「不弱化測試」） |
| **`main` 保護**（ruleset：必須經過 PR、只有 Owner 合併） | Merge 機制 | agent 無法直接改 `main`，所有變更都經過 PR 與 Owner；出錯時最多壞在分支上 | 有 bypass 權限的人仍然可以繞過 |
| **Hook：擋推送到 `main` 與 force push** | Session 機制 | 在 agent 打出指令的當下就擋，並說明「開 PR，由 Owner 合併」；不用等推送失敗，也不會改寫歷史 | 只在 Claude Code 生效；其他工具靠上面的 ruleset |
| **Hook：擋危險指令**（刪除根目錄或家目錄、`git reset --hard`、`git clean -fdx`） | Session 機制 | 本機的工作與未提交的改動不會被一個指令清掉 | 擋不了所有危險的寫法；只列出最常見、最難回復的 |
| **Hook：改規則檔要詢問**（AGENTS.md、harness.md、`.claude/`、CI 設定） | Session 機制 | agent 不能悄悄放寬自己的規則來通過檢查；每次修改規則都有人看到並同意 | 合理的維護也會多一次確認；其他工具沒有這一層 |
| **`.claude/settings.json` 權限**（deny 機密，allow 常用指令） | Session 機制 | agent 讀不到 `.env`、金鑰與雲端憑證，機密不會出現在對話或 PR 裡；常用的測試與 git 指令不用每次確認，少很多中斷 | 不是沙箱：agent 仍然能連網、執行其他指令（會詢問） |
| **全新驗證者**（`/verify`） | 文字 | 每個 PR 合併前都有一份獨立的判定與證據，Owner 審查時從判定開始，而不是從頭讀 diff | 同 Level 0：同模型的盲點；不能強制合併前一定要驗證 |
| **`docs/decisions.md`**（只增不改） | 文字 | Owner 的決定有一個固定的地方，新 session 不會重複問同一件事，也不會推翻已定的事 | 只增不改要到 Level 2 才有機器檢查 |

**這一級擋得住的事故：** agent 直接改壞 `main`；沒跑測試就合併；機密外洩到對話；一個指令清掉工作目錄；agent 改規則讓自己過關。

**仍然擋不住的：** agent 改範圍外的檔案；刪測試或放寬斷言（CI 會是綠的）；分不出是哪個 agent 做的。這些是 Level 2 的事。

> **EN:** `/setup` copies these files. Every component here is cheap and on every source's minimum list.
> - **AGENTS.md map:** every agent tool starts from the same entry point, with test commands, the definition of done and where docs live.
> - **harness.md:** all skills read one config, so behaviour stays consistent across people and sessions.
> - **One test command:** lets agents run, read and fix on their own, the precondition for self-correction.
> - **CI as a required check:** a PR with failing tests can't merge, whoever opened it, so "it passed locally" stops counting. It can't stop tests being deleted.
> - **`main` protection:** agents can't change `main` directly, so damage stays on branches. People with bypass rights can still get around it.
> - **The three hooks** act the moment a command is typed:
>   - the push hook blocks pushes to `main` and force pushes, and explains to open a PR instead;
>   - the destructive-command hook protects local work from a single wipe;
>   - the rule-file hook makes every rule change visible and approved, so an agent can't relax its own rules.
>
>   All three work only in Claude Code.
> - **Permissions:** keep `.env`, keys and cloud credentials out of reach, and spare constant prompts for routine commands. This isn't a sandbox.
> - **Fresh verifier:** gives the Owner an independent verdict and evidence to start from.
> - **Decision log:** gives decisions a fixed home, so sessions don't re-ask or overturn them.
>
> **Stopped at this level:** agents breaking `main`, unmerged-test merges, secrets leaking into chat, wiped working trees, agents loosening their own rules.
>
> **Not stopped yet:** out-of-scope edits, deleted or loosened tests (CI stays green), and not knowing which agent did what. Those are Level 2.

---

## Level 2：多 agent 平行 / Parallel agents

照食譜加（`docs/guardrails/`）。這一級把 v2 的 CI 檢查改寫成可以單獨挑選的元件；多數需要 ticket 寫明範圍與完成條件的測試 ID。

| 元件 | 強制力 | 可達成的結果 | 做不到 |
| --- | --- | --- | --- |
| **機器帳號**（每個 agent 一個 GitHub 帳號，只有 Write 權限） | Merge 機制 | 每個 push、PR、留言都能追到是哪個 agent；agent 帳號在 GitHub 層級就無法合併 `main` | 要多管理帳號與 token |
| **Commit 作者檢查** | Merge 機制 | PR 裡每個 commit 的作者都是指定的機器帳號（依 GitHub 帳號判斷，不比對 email）；冒用或設錯身分的 commit 合併不了 | 不能分辨同一個帳號底下的不同 session |
| **範圍檢查**（ticket 的「範圍」） | Merge 機制 | PR 只能改 ticket 列出的路徑；兩個 agent 平行工作不會互相覆寫，範圍外的「順手修改」合併不了 | 範圍寫太寬就沒有效果；需要 ticket 寫明範圍 |
| **唯讀路徑** | Merge 機制 | 規則、規格、CI 設定、決策紀錄在 ticket PR 中不能被修改，除非 ticket 明確列出該檔案；agent 無法改規格來配合程式 | 只擋 ticket PR；Owner 自己的修改不受影響 |
| **不弱化測試**（JUnit 結果比對） | Merge 機制 | base 上通過的每個測試，在 PR 上都必須存在而且通過；刪測試、改名、標記跳過，都會讓 PR 合併不了，即使其他測試全綠 | 測試真的需要改名時要由 Owner 記錄對應；不能抓到「斷言被放寬但測試還在」（由驗證者的突變抽查補上） |
| **完成條件對應測試** | Merge 機制 | ticket 的每個完成條件都有一個存在而且通過的測試 ID；「說做完但沒測」的條件合併不了 | 不能判斷測試是否真的測到條件的意思 |
| **只增檔案**（例如 CHANGELOG、決策紀錄） | Merge 機制 | 指定檔案在 PR 中只能新增行；歷史紀錄不會被改寫 | 不能檢查新增的內容是否正確 |
| **序列化資源**（例如 migration、lockfile） | Merge 機制 | 同一個資源同一時間只有一張 ticket 在改；避免兩個 PR 各自都對、合在一起卻衝突 | 需要維護「進行中」的清單（看板或 issue 標籤） |
| **證據檢查** | Merge 機制 | PR 說明沒有證據一節、或有畫面卻沒有截圖時合併不了；Owner 審查時一定看得到證據 | 只檢查證據存在，不檢查內容真假 |

**這一級擋得住的事故：** 平行的 agent 互相覆寫；刪掉失敗的測試讓 CI 變綠；改規格配合程式；分不出是誰做的；兩個 migration 同時合併造成衝突。

> **EN:** Added from recipes in `docs/guardrails/`. These are v2's CI checks as separately selectable components; most need tickets to state a scope and test IDs.
> - **Machine accounts:** trace every push, PR and comment to an agent, and can't merge `main`.
> - **Commit-author check:** blocks commits from the wrong identity, checked by GitHub account rather than email.
> - **Scope check:** keeps each PR to its ticket's paths, so parallel agents can't overwrite each other.
> - **Read-only paths:** stop ticket PRs from editing rules, specs, CI or the decision log, unless the ticket names the file.
> - **No weakened tests:** blocks any PR where a test that passed on the base is missing or failing. That catches deletions, renames and skips; loosened assertions are left to the verifier's mutation checks.
> - **Done-when:** requires every completion condition's test to exist and pass.
> - **Append-only files:** keep history from being rewritten.
> - **Serial resources:** let only one ticket touch a migration or lockfile at a time.
> - **Evidence check:** blocks PRs without an evidence section, or without screenshots when there's a UI.
>
> **Stopped at this level:** parallel overwrites, deleted tests passing CI, specs bent to fit code, untraceable work, conflicting migrations.

---

## Level 3：長時間自主 / Long-running autonomy

照食譜加。這一級讓工作能跨 session 接續，並讓 harness 本身可以被量測與改進。

| 元件 | 強制力 | 可達成的結果 | 做不到 |
| --- | --- | --- | --- |
| **進度檔與固定開場流程**（讀進度、讀 git log、跑一次測試，再挑下一項） | 文字 | 新的 session 幾分鐘內就能接手，不會重做已完成的事，也不會在壞掉的狀態上繼續疊；Anthropic 的長時間 harness 就是靠這個連續工作 | 進度檔寫錯時會誤導下一個 session |
| **`handoff` skill**（Level 1 起就能用） | 文字 | 中斷時留下「目標、已完成、進行中、下一步、證據位置」；換人或換 session 都能接 | 依賴中斷前有機會寫 |
| **JSON 功能清單**（只准改「是否通過」欄位） | 文字 + 可加檢查 | agent 不能刪掉或改寫還沒做完的需求，只能把它標成通過；長時間工作不會「範圍悄悄縮小」 | 要另外加檢查才能機器保證只改了那個欄位 |
| **第二模型審查**（不同廠商或不同模型） | 文字 | 同模型的盲點被另一個模型抓到；敏感領域或高風險 PR 多一層把關 | 增加費用與時間；兩個模型也可能一起錯 |
| **自主合併政策**（CI 綠 + 驗證 PASS 後由 agent 合併） | Merge 機制 | 不用等人就能持續交付；前提是 Level 2 的檢查都開著 | 未經人看的程式會進入 `main`；人只能事後審查 |
| **專案的 evals**（從真實失敗挑 20–50 個任務） | 工具 | 改 skill、改提示、換模型之前後各跑一次，用數字判斷變好還是變壞，而不是憑感覺 | 建立與維護任務集要時間；任務太少時數字不穩 |
| **`retro` skill** | 文字 | 重複出現的錯誤被整理成「規則 → 由誰保證」的提議（測試、lint、hook、CI 或文件），Owner 核准後才改；同樣的錯不會一直靠人提醒 | 只提議，不自動修改 |
| **「何時拿掉」檢查** | 文字 | 每個元件都寫了什麼證據顯示它不再需要；模型進步後能有根據地拿掉負擔，harness 不會只增不減 | 需要定期做 retro 才有作用 |

> **EN:** Added from recipes. This level lets work span sessions and makes the harness itself measurable.
> - **Progress file plus start-up routine:** a new session takes over in minutes without redoing work or building on a broken state, as in Anthropic's long-running harness.
> - **`handoff`** (usable from Level 1): leaves the goal, what's done and in progress, the next step and where the evidence is.
> - **JSON feature list:** stops scope from silently shrinking.
> - **Second-model review:** catches the first model's blind spots on sensitive or risky PRs.
> - **Agent-merge policy:** delivers continuously without waiting for a person, provided Level 2 is on. Unreviewed code then reaches `main`.
> - **Project evals:** 20–50 real-failure tasks turn "better or worse" into numbers before and after any change.
> - **`retro`:** turns repeated mistakes into rule-to-enforcer proposals for the Owner to approve.
> - **When-to-remove checks:** give evidence for retiring components as models improve, so the harness doesn't only grow.

---

## 5. 不建議一開始就做的事 / Not recommended up front

| 做法 | 為什麼不建議 |
| --- | --- |
| 一開始就把 Level 2–3 全部打開 | v2 的經驗：開工前就要設定 16 題、11 項檢查，流程變得繁瑣，限制開發。先到 Level 1，遇到對應的事故訊號再升級 |
| 用很長的 AGENTS.md 取代機制 | agent 會略讀長文件；沒有例外的規則寫成 hook 或 CI 才可靠 |
| 讓 agent 自己評自己的工作 | 所有來源都指出 agent 會高估自己的成果；驗證者一定要是全新的 context |
| 只看 CI 是否綠燈 | CI 綠只代表現有測試通過；測試被刪、被放寬時一樣是綠的 |

> **EN:**
> - **Turning on Levels 2–3 from day one:** v2 showed that 16 setup questions and 11 checks before any work make the process heavy. Start at Level 1 and upgrade on the matching incident signal.
> - **A long AGENTS.md instead of mechanisms:** agents skim long files, so zero-exception rules belong in hooks or CI.
> - **Agents grading their own work:** every source warns they overrate it, so the verifier must have a fresh context.
> - **Trusting a green CI alone:** green only means the existing tests passed, and it stays green when tests are deleted or loosened.

## 6. 來源 / Sources

- Anthropic：[Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)（2024-12）、[Writing effective tools for AI agents](https://www.anthropic.com/engineering/writing-tools-for-agents)（2025-09）、[Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)（2025-09）、[Building agents with the Claude Agent SDK](https://claude.com/blog/building-agents-with-the-claude-agent-sdk)（2025-09）、[Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)（2025-10）、[Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)（2025-11）、[Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)（2026-01）、[Harness design for long-running apps](https://www.anthropic.com/engineering/harness-design-long-running-apps)（2026-03）、[Best practices for Claude Code](https://code.claude.com/docs/en/best-practices)
- OpenAI：[Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/)（2026-02，研究時無法直接開啟，依摘要整理）；[OpenAI Agents SDK](https://github.com/openai/openai-agents-python)（guardrails）
- Google：[Gemini CLI](https://github.com/google-gemini/gemini-cli)（context 檔、hooks、沙箱、Agent Skills 支援）
- 開放標準：[AGENTS.md](https://github.com/agentsmd/agents.md)、[Agent Skills](https://github.com/agentskills/agentskills)
- 公開實作：[mattpocock/skills](https://github.com/mattpocock/skills)、[pstack](https://github.com/cursor/plugins/tree/main/pstack)、[gstack](https://github.com/garrytan/gstack)
- 本專案的試跑：sop-trial 的 `/build` → `/verify`（帳單分攤 ticket，PASS，提出 3 個規格問題與 9 項 skill 修正）

> **EN:** Anthropic engineering posts and Claude Code docs (2024-12 to 2026-03); OpenAI's harness-engineering post (summarized from snippets because the page couldn't be opened) and Agents SDK guardrails; Gemini CLI docs; the AGENTS.md and Agent Skills standards; mattpocock/skills, pstack and gstack; and this project's own sop-trial run.
