---
name: verify
description: Verify one pull request cold. A fresh subagent that never saw the builder's conversation re-runs everything from a clean checkout, works through a checklist, and posts PASS or FAIL as a PR comment. Takes a PR number or URL.
disable-model-invocation: true
argument-hint: "<PR number or URL>"
---

# Verify a pull request

Verification is only worth something if it's independent. The verifier judges from the ticket, the spec, the diff and what it runs itself: never from the builder's conversation, and never from claims in the PR description.

## 1. Prepare (you, the coordinator)

1. Read `docs/agents/harness.md`. If it's missing, suggest `/setup` once, then continue with defaults: the document language is the conversation's, and there are no sensitive areas.
2. Fetch the PR: its number, base branch, head commit and linked ticket. If there's no ticket, ask the user for the completion conditions. Don't infer them from the diff.
3. Count earlier verdicts on the PR to get this round's number.

## 2. Dispatch a fresh verifier

Start **one new subagent** with a fresh context. If this session wrote the code, this step isn't optional: you can't verify your own work.

Give it only pointers, not your opinions:

- the PR number, the base branch and the head commit;
- the ticket reference and the path to the harness file;
- the round number;
- the path to [checklist.md](checklist.md) and [verdict-template.md](verdict-template.md) in this skill's directory.

Tell it to:

- work in a clean checkout of the head commit (a new worktree or a fresh clone), never in this session's working tree;
- follow the checklist, and return the filled-in verdict;
- not modify product code or tests, and not push anything except its own screenshots under `docs/evidence/<ticket>/verify/`.

## 3. Post the verdict

1. Read the returned verdict. Check that every checklist row has evidence. A row without evidence counts as fail, and you send it back to the same verifier once to fill the gap.
2. Post the verdict as one PR comment, acting as the machine account from the harness file when there is one.
3. Tell the user the result in one line, with the PR link.

## After the verdict

- PASS: the Owner (or whoever the harness file says merges) decides. Don't merge.
- FAIL: the builder fixes it (`/build` explains the fix rounds). Each new round is verified by a new subagent.
- FAIL in round 2: recommend escalating to the Owner.

## Don't

- Don't give PASS just because CI is green. CI is one row of the checklist.
- Don't propose fix code in the verdict. Describe the problem, how to reproduce it, and what was expected.
- Don't write the model name from memory (`evidence` skill).
