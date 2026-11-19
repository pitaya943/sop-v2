<!-- PR description for /build. Write it in the document language from docs/agents/harness.md. Keep the headings; write "None" for an empty section. -->

## What was done

Ticket: <link or path>. Completion conditions: <n>, all met.

<two or three sentences on the change>

## How to verify

```bash
<command to run the tests>
```

Expected: <what passes, how many tests>.

## Evidence

<!-- One entry per completion condition, in the ticket's order: the command and its output, or a screenshot path under docs/evidence/<ticket>/. Then the red output from before the fix. -->

1. <condition> — <command and output>

Red before green:

```text
<failing output>
```

## Assertions stricter than the spec

<!-- Each assertion that checks more than the spec asks for, or "None". -->

## Scope

<!-- git diff --stat <base>...HEAD -->

## Open questions

<!-- Spec questions, follow-up work, or proposals for docs/pitfalls.md. "None" if there are none. -->
