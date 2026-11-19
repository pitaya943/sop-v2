# 平行開發 / Parallel development

多個 Builder 同時工作時，如何保證彼此不互相覆寫。原則：**衝突在計畫階段排除，CI 是最後防線。**

> **EN:** How several Builders work at once without overwriting each other. Conflicts are ruled out at planning time; CI is the last line of defence.

## 1. 可以同時進行的條件 / When two tickets may run together

兩張 ticket 可以同時進行，若且唯若：

1. **依賴：** 兩者的 `depends_on` 都已 merged。
2. **路徑不相交：** 兩者的 `allowed_paths` 沒有交集（例外見第 3 節）。
3. **序列化資源不相交：** 兩者的 `serial` 沒有共同項目。
4. **容量：** 進行中（building、verifying、fixing）的 ticket 數小於 `max_parallel`。

> **EN:** Two tickets may run together iff their dependencies are merged, their `allowed_paths` don't overlap (except append-only files), their `serial` resources don't overlap, and fewer than `max_parallel` tickets are in progress.

## 2. 序列化資源 / Serialized resources

有些衝突不在檔案層級：兩張 ticket 改不同的 migration 檔，卻都改變 schema 的順序；兩張 ticket 都升級依賴，改的是同一份 lockfile。這類共用狀態用 ticket 的 `serial` 宣告。

- 可用的資源名稱由專案在 `serial_resources` 設定（例如 `db-schema`、`lockfile`、`ci-config`、`public-api`）。
- CI `serial-resource` 檢查：宣告的資源都在清單內，且看板上沒有另一張進行中的 ticket 宣告同一項。

> **EN:** Some conflicts aren't file-level (migration ordering, a shared lockfile). Tickets declare these in `serial`, using names from `serial_resources`; CI checks the names are known and that no other in-progress ticket holds the same one.

## 3. 共用的只增檔案 / Shared append-only files

有些檔案每張 ticket 都要加一行（例如「已實作的規則清單」）。若嚴格要求路徑不相交，這些 ticket 就無法平行。這類檔案列在 `append_only_files`：

- 可以同時出現在多張平行 ticket 的 `allowed_paths`，但 ticket 必須同時在 `append_only` 宣告。
- CI `append-only` 檢查 PR 對這些檔案的 diff **只有新增行**。
- 後合併的 ticket 在開 Verifier 前，先 merge 最新的 milestone 分支（`git merge origin/milestone/Mx`，不 rebase），解決衝突時保留雙方的新增行。

> **EN:** Files listed in `append_only_files` may appear in several parallel tickets if each declares them in `append_only`. CI checks that the diff only adds lines. The ticket merged later first merges the latest milestone branch (no rebase) before its Verifier starts, keeping both sides' additions.

## 4. Chief 的排程演算法 / The Chief's scheduling algorithm

Chief 在 `plan-milestone` 時算出批次並寫進計畫 issue；執行時每當一張 ticket merged 就重新評估。演算法是貪婪的拓撲排序：

```python
ready = {t in todo | all(depends_on merged)}
running = {t | state in (building, verifying, fixing)}
for t in sorted(ready, key=(critical_path_length desc, id)):
    if len(running) >= max_parallel: break
    if any(paths_overlap(t, r) or serial_overlap(t, r) for r in running): continue
    start(t); running.add(t)
```

- **依關鍵路徑長度排序：** 先啟動「後面還有一長串依賴它」的 ticket，縮短 milestone 的總時間。
- **路徑重疊的判定是保守的：** 比較兩個 glob「第一個萬用字元之前的路徑前綴」，其中一個是另一個的前綴就視為重疊。可能誤判為重疊（少平行一點），但不會漏判。
- **PR 時的 `path-scope` 是精確的：** 它用實際變更的檔案檢查。
- 若 Chief 確認兩張被判為重疊的 ticket 其實不衝突，可以在計畫中列出「人工確認不重疊」，由 Owner 核准。

> **EN:** A greedy topological sort ordered by critical-path length, re-evaluated whenever a ticket merges. Overlap is judged conservatively by the static prefix before each glob's first wildcard (may under-parallelize, never misses); PR-time `path-scope` checks actual files exactly. The Chief may list "manually confirmed non-overlapping" pairs in the plan for Owner approval.

## 5. 平行度不宜過大 / Keep parallelism modest

- 每個平行的 Builder 都需要一個 Verifier，token 成本約為 2×N。
- Chief 要追蹤的 PR 狀態線性增加，Chief 的 context 是瓶頸。
- 實務經驗：同時 2–3 張最穩定。`max_parallel` 的上限是 5。

> **EN:** Each Builder needs a Verifier (about 2×N cost), and the Chief's context is the bottleneck. Two or three at once worked best in practice; `max_parallel` is capped at 5.
