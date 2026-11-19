---
name: setup
description: Configure this repo for the pitaya skills. Explore it, ask a few questions, install the Level 1 defaults (AGENTS.md, permissions, hooks, a tests workflow) without overwriting anything, and write docs/agents/harness.md, the file every other skill reads first. Run once per repo, and again to update stale copies.
disable-model-invocation: true
---

# Setup

Install the defaults for the chosen level and write `docs/agents/harness.md`, the short config every pitaya skill reads first. There is no gate: other skills work without it, using safe defaults, so keep this quick. Re-running is safe; it reports stale copies instead of overwriting them.

## 1. Explore before asking

Read what exists. Don't assume.

- `git remote -v`: is this a GitHub repo, and which one?
- `docs/agents/harness.md`: if it exists, you're updating it. Show the current values and ask only about what changes.
- The test command: look at `package.json` scripts, `pyproject.toml`, `pytest.ini`, `Makefile`, `go.mod`, `Cargo.toml` and CI workflows. Run the best candidate once, exactly as you'll record it, and note whether it passes.
- `docs/tickets/` or issues labelled `ticket`: where does planned work already live?
- `AGENTS.md`, `CLAUDE.md`, `.claude/settings.json`, `.github/workflows/`: what the project already has that the install must not overwrite.
- Who you are on GitHub: `gh api user --jq .login`, or the GitHub tool's "get me" call. Don't guess.
- If the skills were copied into `.claude/skills/`, run `git check-ignore -v .claude/skills/*/SKILL.md`. A broad rule such as `build/` hides the `build` skill from git; anchor it (`/build/`) and tell the user.

## 2. Ask, one question at a time

Lead each question with your recommendation, so the user can accept it in a word. Skip any question that exploring already settled.

1. **Owner and machine account.** Who merges `main`? Is there a separate machine account the agents act as? Recommend one if several agents will work in parallel: then every push, PR and comment can be traced to an agent by its GitHub account. "None" is a valid answer.
2. **Where tickets live.** GitHub Issues labelled `ticket` (recommended when there's a GitHub remote) or `docs/tickets/<id>.md` files.
3. **Test command.** Confirm one that actually runs here, as typed: if the test tool lives in a virtualenv, record that path (for example `.venv/bin/python -m pytest -q`). Otherwise ask for it. If nothing runs yet, record "none yet" and say that `/build` needs one.
4. **Language, records and sensitive areas.** Which language documents are written in (PRs, issues, reports); whether to keep `docs/decisions.md` (recommended; add a `Pitfalls:` line only if they also want `docs/pitfalls.md`); which areas need a covering test before anyone changes them (money, permissions, migrations). "None" is fine.

If an answer contradicts something you found (an account that doesn't exist, a failing test command), say what you found and ask again. Never fill in an answer yourself.

## 3. Install and write

1. **Level.** Recommend Level 1 (the default) unless the user only wants the skills (Level 0). Levels 2 and 3 come later from recipes; `docs/suggestion.md` in the plugin's repo says what each level achieves.
2. **Preview, then install.** From the repo root, run [scripts/install_templates.py](scripts/install_templates.py) with `--level`, `--test-command "<the confirmed command>"`, `--no-decisions` if the user declined the decision log, and `--check`. Show the user the output, then run it again without `--check`.
   - `created` and `merged` are done. `merged` means `.claude/settings.json` gained rules and hooks; nothing of theirs was removed.
   - `differs` and `stale` files were left alone. Show the diff against `../../templates/<path>` (relative to this file) and let the user choose. Never overwrite one yourself.
   - If `AGENTS.md` differs, add a short "Agent harness" section to theirs instead, pointing to `docs/agents/harness.md`.
3. **Harness file.** Copy [harness-template.md](harness-template.md) to `docs/agents/harness.md` and fill it in: the answers, the level, and under "Guardrails" the Level 1 parts that are now installed. Delete lines that don't apply rather than leaving placeholders.
4. **CI.** Add to `.github/workflows/tests.yml` the setup steps the test command needs (a language runtime, installing dependencies). The first pull request must show the `tests` check passing.
5. Show the user the diff, then commit with the message `Configure pitaya skills`. Open a PR only if the user asks.

## 4. Hand the Owner the repo settings

The machine account can't change repo settings, so list these steps for the Owner, and check them afterwards where you can read them:

- A ruleset on `main`: require a pull request, block force pushes and deletions, require the `tests` check, and let only the Owner bypass.
- If there's a machine account: it's a collaborator with Write, not Admin.

Then name the next step up, from `docs/suggestion.md`: usually nothing until a second agent works in the repo (Level 2).

## Don't

- Don't write secrets, tokens or passwords anywhere. Name the secret, never its value.
- Don't change repo settings (rulesets, collaborators, secrets). Explain the steps; the Owner makes the change.
