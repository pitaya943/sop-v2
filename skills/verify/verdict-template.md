<!-- Verdict comment for /verify. Write it in the document language from docs/agents/harness.md. -->

## Verification: PASS | FAIL

- Model: <name and version from the session's configuration, or "unavailable: <reason>">
- Round: <n>
- Head commit: <sha>
- Ticket: <link or path>

| # | Check | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Clean re-run | pass / fail | <command, summary line> |
| 2 | Completion conditions | | |
| 3 | Tests not weakened | | |
| 4 | Tests are real | | |
| 5 | Mutation spot-check | | |
| 6 | Error paths | | |
| 7 | Bad input | | |
| 8 | Spec edge cases | | |
| 9 | Scope | | |
| 10 | Evidence and hygiene | | |

## Problems

<!-- FAIL only. For each problem: where (file:line), how to reproduce, what was expected, what happened. No fix code. -->

## Spec questions

<!-- Behaviour the spec doesn't decide. "None" if none. -->

## Pitfall proposals

<!-- Something the next agent should know, for docs/pitfalls.md. "None" if none. -->
