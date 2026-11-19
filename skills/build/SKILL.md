---
name: build
description: Build one ticket red-then-green and open a pull request with evidence. Takes a ticket reference (an issue number, URL or docs/tickets path). One ticket per session.
disable-model-invocation: true
argument-hint: "<ticket: issue number, URL or path>"
---

# Build a ticket

## Before you start

1. Read `docs/agents/harness.md`. If it's missing, suggest `/setup` once, then continue: tickets are GitHub Issues in this repo, and the test command is whatever the repo's config files say.
2. Fetch the ticket and state its title. If the reference is ambiguous, ask. List its completion conditions back to the user as a numbered list.
3. If any condition is unclear, two conditions contradict each other, or the work needs a change the ticket doesn't authorize (a data model, a public interface, a sensitive area from the harness file with no covering test): stop. Ask the Owner with the `ask-owner` skill when installed, otherwise in the conversation. Don't guess.
4. **Identity.** If the harness file names a machine account, confirm the GitHub login you act as is that account. If it isn't, stop and tell the user. Set the commit author to that account and its GitHub noreply email: `<id>+<login>` at the domain `users.noreply.github.com`, where `<id>` comes from `gh api users/<login> --jq .id`.
5. Branch `ticket/<id>-<short-slug>` from the ticket's base branch (`main` unless the ticket says otherwise).

## Build

1. For each completion condition, in order, use the `tdd` skill: red for the right reason, then green, then refactor. Keep each red output.
2. Run the full test suite. Nothing that passed before may now fail or disappear.
3. Check scope: `git diff --stat <base>...HEAD`. If the ticket lists a scope, every changed file must be inside it. If it doesn't, still touch only what the ticket needs. Never edit specs, the harness file, `AGENTS.md`/`CLAUDE.md`, or CI config unless the ticket names that exact file.
4. Commit in small steps, with English commit messages.

## Hand over

1. Push, then open a PR into the base branch, with [pr-template.md](pr-template.md) as the description, in the document language. Use the `evidence` skill for the "Evidence" section: one entry per condition, plus the red output.
2. If CI runs on the PR, wait for it. Fix and push until it's green. A red CI isn't a hand-off.
3. Post one hand-off comment: each condition with its evidence, the head commit, and the model that did the work (`evidence` skill).

## Fix rounds

- Verifier says FAIL, round 1: fix each listed problem in this same session, push, wait for green CI, and comment on what changed and where.
- Round 2 goes to a fresh session, which reads only the ticket, the diff and the verdicts.
- Still FAIL after round 2: stop and escalate to the Owner with the open problems and two or three options.

## Don't

- Don't skip, delete or loosen tests, or write tests that pass no matter what (`tdd` skill).
- Don't connect to shared or production systems. Use local, throwaway resources only.
- Don't print secrets in code, logs, commits or PRs.
- Don't merge your own PR, and don't push to `main`.
