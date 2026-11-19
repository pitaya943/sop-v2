# Verifier checklist

You're the verifier. You can't see the builder's conversation, on purpose. Judge only from the ticket, the spec, the diff and what you run yourself. The PR description's claims are not evidence: redo anything you rely on.

Mark every item pass or fail, with evidence: the command and its output, or the file and line. No evidence means fail.

1. **Clean re-run.** In a clean checkout of the head commit, install what the project needs and run the full test command from `docs/agents/harness.md`. The result matches CI, if CI ran.
2. **Completion conditions.** Each condition in the ticket has a test, or a re-runnable command, that you ran and saw pass. The count matches the ticket.
3. **Tests weren't weakened.**
   - Run the suite on the base branch too, and compare: every test that passed on the base still exists and passes on the head.
   - The diff adds no skip or expected-failure markers.
   - The diff deletes no test or parametrized case, and loosens no assertion.
4. **Tests are real.** Read each new or changed test: it calls the product code through its public interface, and it checks the result. A test that would pass with the feature removed fails this item.
5. **Mutation spot-check.** Pick up to three conditions, preferring sensitive areas from the harness file, money, permissions and state changes. For each, break the implementation locally (invert a condition, drop a line, return early) and confirm the matching test fails. Revert. Never push these changes.
6. **Error paths.** For at least one error path, the test asserts the outcome or its type, the exact message, and that nothing else changed.
7. **Bad input through the interface.** Send the public interface one invalid input that no test covers (a missing field, out of range, wrong permissions). Confirm it's rejected.
8. **Edge cases from the spec.** Read the spec text, think of two edge cases the tests don't cover, and try them.
   - Behaviour that contradicts the spec is a fail.
   - Behaviour the spec doesn't decide isn't a fail: list it under "Spec questions".
9. **Scope.** Run `git diff --stat <base>...<head>`. If the ticket lists a scope, every changed file is inside it. In every case, the diff doesn't touch specs, `docs/agents/harness.md`, `AGENTS.md`/`CLAUDE.md` or CI config unless the ticket names that exact file.
10. **Evidence and hygiene.**
    - The PR's evidence section covers every condition, including the red output.
    - Nothing in the diff, PR or logs exposes a secret.
    - No test talks to a shared or production system.

**Verdict:** PASS only if every item passes. Otherwise FAIL. Fill in [verdict-template.md](verdict-template.md).
