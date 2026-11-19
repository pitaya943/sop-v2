# 通用 harness 模板 scratchbook / General harness template scratchbook

從零開始，每一輪用選擇題做決定，答案逐輪寫進這裡。依據：研究頁面「Agent Harness 藍圖」（八層：L1 Context 地圖、L2 流程、L3 回饋迴路、L4 機制化、L5 權限與沙箱、L6 記憶與進度、L7 審查與驗證、L8 評估與維護）。

> **EN:** Built from scratch, one round of multiple-choice decisions at a time, with each round's answers recorded here. Basis: the Agent Harness blueprint and its eight layers.

## 決策 / Decisions

| # | 輪 | 問題 | 選擇 | 層 |
| --- | --- | --- | --- | --- |
| T1 | 1 | 服務誰 | 分級：同一套模板 Level 0–3，個人停在 Level 1，多 agent 升到 Level 2–3 | 全部 |
| T2 | 1 | 支援的工具 | Claude Code 優先 + 可攜：AGENTS.md 為入口，skill 用開放標準；hooks 只在 Claude Code 生效，其他工具得到文字版 | L1、L4 |
| T3 | 1 | 自主程度 | 設定欄位，預設「只有 Owner 合併 `main`」；專案可改成「CI 綠 + 驗證 PASS 後 agent 合併」 | L4、L7 |
| T4 | 1 | 發佈方式 | Plugin 發佈 skill（自動更新）+ `/setup` 把 Level 1 檔案複製進專案，之後歸專案所有 | L2 |
| T5 | 2 | 測試契約 | 分級：Level 1 只要一個真的跑得通的指令；Level 2 才要求輸出 JUnit XML（為了「不弱化測試」的結果比對） | L3 |
| T6 | 2 | Level 1 hooks | 擋推送到 `main` 與 force push；擋危險指令；編輯規則檔（AGENTS.md、harness.md、CI、hooks）時改成詢問。不做「結束前要跑測試」的 Stop hook | L4 |
| T7 | 2 | Level 1 CI | 一個 workflow、一個 job，跑 harness.md 的測試指令，設為 `main` 的必要檢查 | L4 |
| T8 | 2 | Level 1 權限 | `.claude/settings.json`：deny 讀取 `.env`、金鑰、雲端憑證；allow 測試指令與常用 git；其他維持詢問；不含沙箱 | L5 |
| T9 | 3 | Ticket 位置 | `/setup` 選：有 GitHub remote 時預設 Issues（標籤 `ticket`），否則 `docs/tickets/<id>.md`；skill 兩種都支援 | L6 |
| T10 | 3 | Ticket 欄位 | Level 1 四個：目標、完成條件、依賴、範圍。Level 2 加：完成條件對應的測試 ID、序列化資源、只增檔案、是否截圖 | L6 |
| T11 | 3 | 進度與交接 | 平常靠 issue、PR、git log；加 `handoff` skill 寫交接文件。Level 3 再加進度檔與固定開場流程 | L6 |
| T12 | 3 | 紀錄檔 | `/setup` 詢問：`docs/decisions.md`（只增不改）預設建立；`docs/pitfalls.md` 預設不建 | L6 |
| T13 | 4 | 驗證者 | `/verify` 預設派全新 subagent；多 agent 時可改成另開 session、指定不同模型 | L7 |
| T14 | 4 | 第二模型審查 | 食譜，選配；建議用在敏感領域或高風險 PR | L7 |
| T15 | 4 | 證據 | 指令與輸出寫在 PR 說明與留言；只有畫面截圖存到 `docs/evidence/<ticket>/` | L7 |
| T16 | 4 | 修正輪 | 預設兩輪（第一輪原 session、第二輪全新 session），仍 FAIL 就升級；輪數可在 harness.md 設定 | L7 |
| T17 | 5 | 測 harness | 範本 repo 放 `evals/` 任務集（小 repo 狀態 + ticket + 評分方式），改 skill 前後手動各跑一次；第一個任務取自 sop-trial #3 | L8 |
| T18 | 5 | 淘汰元件 | 每篇食譜、每個 hook 與 skill 寫「什麼證據顯示可以拿掉它」，retro 時檢查 | L8 |
| T19 | 5 | 自我改進 | `retro` skill 把重複出現的錯誤整理成「規則 → 由誰保證（測試 / lint / hook / CI / 文件）」的提議，Owner 核准後才改 | L8 |
| T20 | 5 | 版本 | plugin 用 semver；CHANGELOG 標出 skill 與食譜的改動；複製進專案的檔案開頭寫來源版本，`/setup` 重跑時比對是否過時 | L8 |
| T21 | 6 | 角色 | 保留 Owner / Chief / Builder / Verifier 作為概念（`docs/concepts/`），對應到 skill：plan=Chief、build=Builder、verify=Verifier；個人使用時一個 session 輪流扮演 | L7 |
| T22 | 6 | learning | 保留為選配 skill：使用者呼叫或 harness.md 開啟時才用 | L2 |
| T23 | 6 | 名稱 | repo 維持 sop-v2；plugin 另取一個不帶版本號的名稱 | — |
| T24 | 6 | 實作位置 | 繼續 PR #12 分支；設計文件改寫成這份 scratchbook 的結果，重排 V3 之後的步驟 | — |
| T25 | 7 | Plugin 名稱 | `pitaya`（skill 顯示為 `/pitaya:build` 等）。Owner 確認放寬 P1：品牌名稱是刻意選擇的例外；帳號、email 等其他個資仍然禁止 | — |
| T26 | 7 | v2 的 CI 檢查 | 改寫成 Level 2 食譜（範圍、唯讀路徑、不弱化測試、完成條件、commit 作者、只增檔案、序列化資源、證據），附可複製檔與失敗案例測試；啟動閘門與 branch-ticket 不再需要 | L4 |

## 逐漸成形的模板 / The template so far

```text
plugin `pitaya`（自動更新）         專案 repo（/setup 複製，歸專案所有）
├─ skills/                  ├─ AGENTS.md            地圖，入口（T2）
                            ├─ CLAUDE.md            匯入 AGENTS.md
                            ├─ docs/agents/harness.md
                            │    等級（T1）、自主程度（T3，預設人類合併）
                            │    測試指令（T5：Level 1 只要跑得通）
                            │    ticket 位置（T9：預設 Issues）
                            │    驗證方式（T13）、修正輪數（T16，預設 2）
                            ├─ docs/decisions.md    只增不改，setup 預設建立（T12）
                            ├─ .claude/settings.json  deny 機密、allow 常用指令（T8）
                            ├─ .claude/hooks/
                            │    no-push-main          擋 main 與 force push（T6）
                            │    no-destructive        擋危險指令（T6）
                            │    ask-on-rule-files     改規則檔要詢問（T6）
                            └─ .github/workflows/tests.yml  一個 job，必要檢查（T7）
├─ templates/   /setup 複製的檔案，檔頭寫來源版本（T20）
├─ docs/guardrails/   Level 2–3 食譜，含「何時拿掉」（T18）、第二模型審查（T14）
├─ evals/       任務集，手動跑（T17）
└─ CHANGELOG.md （T20）

skills（目前）：setup · plan · build · verify · report · handoff（T11）· retro（T19）
                tdd · evidence · ask-owner · learning（選配，T22）
```

## 待問 / Still to ask

（全部問完。下一步：把這份結果改寫成設計文件，重排實作步驟。/ All asked. Next: turn this into the design doc and re-plan the steps.）
