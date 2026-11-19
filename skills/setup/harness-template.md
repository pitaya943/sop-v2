# Harness

Read by every pitaya skill before it plans, builds, verifies or reports. Written by `/setup`; edit it by hand or re-run `/setup`.

## Level

- Level: 1. What it includes: `docs/suggestion.md` in the pitaya repo. Raise it by adding guardrail recipes; record each under "Guardrails" below.
- Templates: pitaya 3.0.0-dev.0. The version `/setup` installed; re-run `/setup` to find stale copies.

## People and accounts

- Owner: example-owner.
- Machine account: example-bot. Agents push, open PRs and comment as this account. If it's "none", agents use the current session's account.
- Autonomy: Only the Owner merges `main`. (Alternative, Level 3 only: "Agents merge after CI is green and the verdict is PASS".)

## Work

- Issue tracker: GitHub Issues in this repo.
- Tickets: GitHub Issues labelled `ticket`. (Without a GitHub remote: `docs/tickets/<id>.md`.)
- Test command: `pytest -q`. Recorded exactly as it runs here. From Level 2 it must also write JUnit XML.
- Document language: en. Used for PRs, issues, comments and reports. Code, identifiers and commit messages stay in English.

## Review

- Verification: a fresh subagent, started by `/verify`. (Alternative: "a separate session", optionally with a named model.)
- Fix rounds: 2. Round 1 in the builder's session, the rest in fresh sessions; still failing after the last round means escalating to the Owner.
- Learning: off. When on, `/report` ends by offering the `learning` review.

## Records

- Decisions: `docs/decisions.md`. Append only: add new entries, never rewrite old ones.

## Sensitive areas

Areas where a change needs a covering test before it starts, otherwise escalate to the Owner. Examples: money calculations, permissions, data migrations.

- (none yet)

## Guardrails

Guardrails in place. Skills rely on these being enforced by hooks or CI rather than re-checking them by hand.

- (none yet)
