# Harness

Read by every sop-v2 skill before it plans, builds, verifies or reports. Written by `/setup`; edit it by hand or re-run `/setup`.

## People and accounts

- Owner: example-owner. Only the Owner merges `main`.
- Machine account: example-bot. Agents push, open PRs and comment as this account. If it's "none", agents use the current session's account.

## Work

- Issue tracker: GitHub Issues in this repo.
- Tickets: GitHub Issues labelled `ticket`. (Or: `docs/tickets/<id>.md`.)
- Test command: `pytest -q`
- Document language: en. Used for PRs, issues, comments and reports. Code, identifiers and commit messages stay in English.

## Records

- Decisions: `docs/decisions.md`. Append only: add new entries, never rewrite old ones.
- Pitfalls: `docs/pitfalls.md`. Things the next agent should know.

## Sensitive areas

Areas where a change needs a covering test before it starts, otherwise escalate to the Owner. Examples: money calculations, permissions, data migrations.

- (none yet)

## Guardrails

Guardrails in place, from the sop-v2 recipes. Skills rely on these being enforced by CI rather than re-checking them by hand.

- (none yet)
