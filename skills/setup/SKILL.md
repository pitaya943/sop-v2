---
name: setup
description: Configure this repo for the sop-v2 skills. Explore it, ask two to four questions, and write docs/agents/harness.md, the file every other skill reads first. Run once per repo, and again whenever the answers change.
disable-model-invocation: true
---

# Setup

Write `docs/agents/harness.md`: the short config every sop-v2 skill reads first. There is no gate. Other skills work without it, using safe defaults, so keep this quick.

## 1. Explore before asking

Read what exists. Don't assume.

- `git remote -v`: is this a GitHub repo, and which one?
- `docs/agents/harness.md`: if it exists, you're updating it. Show the current values and ask only about what changes.
- The test command: look at `package.json` scripts, `pyproject.toml`, `pytest.ini`, `Makefile`, `go.mod`, `Cargo.toml` and CI workflows. Run the best candidate once, and note whether it passes.
- `docs/tickets/` or issues labelled `ticket`: where does planned work already live?
- `AGENTS.md` and `CLAUDE.md`: is there already a pointer to the harness file?
- Who you are on GitHub: `gh api user --jq .login`, or the GitHub tool's "get me" call. Don't guess.

## 2. Ask, one question at a time

Lead each question with your recommendation, so the user can accept it in a word. Skip any question that exploring already settled.

1. **Owner and machine account.** Who merges `main`? Is there a separate machine account the agents act as? Recommend one if several agents will work in parallel: then every push, PR and comment can be traced to an agent by its GitHub account. "None" is a valid answer.
2. **Where tickets live.** GitHub Issues labelled `ticket` (recommended when there's a GitHub remote) or `docs/tickets/<id>.md` files.
3. **Test command.** Confirm the one you found, or ask for it. If nothing runs yet, record "none yet" and say that `/build` needs one.
4. **Language, records and sensitive areas.** Which language documents are written in (PRs, issues, reports); whether to keep `docs/decisions.md` (recommended) and `docs/pitfalls.md`; which areas need a covering test before anyone changes them (money, permissions, migrations). "None" is fine.

If an answer contradicts something you found (an account that doesn't exist, a failing test command), say what you found and ask again. Never fill in an answer yourself.

## 3. Write

1. Copy [harness-template.md](harness-template.md) to `docs/agents/harness.md` and fill it in. Delete lines that don't apply rather than leaving placeholders.
2. Create `docs/decisions.md` and `docs/pitfalls.md` if the user chose them, each with only a title and one line saying what goes there.
3. Add this section to `AGENTS.md`, or to `CLAUDE.md` if there's no `AGENTS.md`. Create `AGENTS.md` if neither exists.

   ```markdown
   ## Agent harness

   Read `docs/agents/harness.md` before planning, building or verifying work.
   ```

4. Show the user the diff, then commit with the message `Configure sop-v2 skills`. Open a PR only if the user asks.

## 4. Recommend one guardrail

End by recommending the cheapest missing guardrail. It's a recommendation, not a requirement.

- No CI runs the tests: recommend "CI runs the tests".
- CI exists, but anyone (or any agent) can push to `main`: recommend "protect `main`".

The recipes live in `docs/guardrails/` of the sop-v2 repo. Installed as a plugin, that's `../../docs/guardrails/README.md` relative to this file; if it isn't there, point the user to the sop-v2 repo instead. Once a guardrail is added, list it under "Guardrails" in `docs/agents/harness.md`.

## Don't

- Don't write secrets, tokens or passwords anywhere. Name the secret, never its value.
- Don't change repo settings (rulesets, collaborators, secrets). Explain the steps; the Owner makes the change.
