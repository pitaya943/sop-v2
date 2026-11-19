<!-- pitaya template 3.0.0-dev.0 · AGENTS.md -->
# AGENTS.md

A short map for coding agents. Details live in the files it points to; read them when you need them.

## Start here

- Read `docs/agents/harness.md` first: the level, who the Owner is, who may merge, where tickets live, how work is verified.
- Work on a branch, never on `main`.

## Commands

- Test: `<TEST_COMMAND>`. Run it after every change and before saying anything is done.

## Done means

1. The completion conditions of the ticket each have a test that went red first, then green.
2. The full test command passes locally and in CI.
3. The pull request shows evidence: the commands you ran and their real output.
4. A fresh verifier, not the session that wrote the code, judged it PASS.
5. Whoever `docs/agents/harness.md` names under Autonomy merges it.

## Never

- Push to `main`, force-push, or delete remote branches. A hook blocks these; open a pull request instead.
- Skip, delete or loosen a test to get green.
- Read, print or commit secrets (`.env`, keys, credentials).
- Change this file, `docs/agents/harness.md`, `.claude/` or CI workflows unless the user asked. A hook asks the user first.
- Connect to shared or production systems. Use local, throwaway resources.

## When unsure

Stop and ask the Owner, with two or three options, their consequences and your recommendation. Don't guess.

## Where things are

- `docs/agents/harness.md`: this project's harness settings.
- `docs/decisions.md`: the Owner's decisions, append only.
- Skills (the `pitaya` plugin): `/pitaya:setup`, `/pitaya:build`, `/pitaya:verify` and the rest.
