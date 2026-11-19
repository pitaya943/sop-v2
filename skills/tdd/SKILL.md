---
name: tdd
description: Red-green-refactor, one behaviour at a time. Write a test that fails for the right reason, make it pass with the smallest change, then tidy. Use whenever you add or change behaviour or fix a bug, and never weaken a test to get green.
---

# TDD

Before starting, read `docs/agents/harness.md` for the test command. If it's missing, find the command from the repo's config files, and suggest the user run `/setup` once.

## The loop

Repeat for one behaviour at a time: one completion condition, one bug, one edge case. Never batch.

1. **Red.** Write one test for the behaviour, through the public interface the caller uses. Run it on its own.
   - It must fail, and for the right reason: the behaviour is missing or wrong. An import error, a typo or a broken fixture isn't red. Fix the test, then run it again.
   - For a brand-new module or function, first add a minimal stub (the real signature, returning a placeholder), so the red is a failed assertion rather than an import error.
   - If earlier work already makes the test pass, don't undo work to manufacture a red. Keep the test, and say in the PR which condition had no red and why; the verifier backs it with a mutation.
   - Keep the failing output. It's evidence (see the `evidence` skill).
2. **Green.** Make the smallest change in product code that passes the test. Run that test, then the test file.
3. **Refactor.** With everything green, remove duplication and improve names. Run the tests after each step. No behaviour changes here.

Run the full suite once at the end, and before any commit you hand over.

## What a good test checks

- **Behaviour, not implementation:** it calls what a caller would call and checks what a caller would see. A test that mocks the code under test proves nothing.
- **The whole outcome:** the returned value or its type, the exact error message, and that nothing else changed. For error paths, assert all three.
- **One reason to fail:** when it goes red, the name and message say what broke.
- **Stable names.** A test ID is how reviewers and CI track it, so renaming one looks like deleting it.

For a bug, the first test reproduces the bug, and it must be red before the fix.

## Never weaken a test to get green

None of these, even temporarily:

- skipping, or marking as expected to fail (`skip`, `xfail`, `.only`, `t.Skip`, `#[ignore]`);
- deleting a test, or a case from a parametrized test;
- loosening an assertion: a smaller expected set, a range instead of a value, `in` instead of `==`, catching broader errors;
- editing the expected value to match what the code now returns, without a spec saying the new value is right.

If a test seems wrong, the spec is unclear, or making it pass needs a change outside your scope, stop. Ask the Owner (the `ask-owner` skill, when installed) with two or three options and a recommendation.

## Stricter than the spec

When a test asserts more than the spec asks (an exact message where the spec only says "an error"), list it in the PR under "Assertions stricter than the spec", so the Owner knows it's a choice, not a requirement.
