---
name: evidence
description: What counts as proof that work is done or verified, and how to present it. Commands with their real output, screenshots for anything visual, and the model that did the work, never from memory. Use before writing "done", "passes" or "verified" in a PR, comment or report.
---

# Evidence

A claim without evidence counts as unverified. Read `docs/agents/harness.md` for the document language and the ticket location. If it's missing, write in the language of the conversation, and suggest `/setup` once.

## What counts

| Claim | Evidence |
| --- | --- |
| A test passes or fails | The exact command, and its output in a code block. Keep the first lines, the last lines and the summary line; mark any cut with `...`. |
| Red before green | The failing output from before the fix, with the reason visible (an assertion, not an import error). If a condition passed on its first run because earlier work covered it, a note saying so instead. |
| A screen or UI works | Screenshots you took yourself, saved under `docs/evidence/<ticket>/`, named for what they show, and linked from the PR. |
| A file is unchanged or in scope | A `git diff --stat <base>...HEAD` listing. |
| Behaviour on bad input | The command or request, with the rejection it produced. |

Not evidence:

- "I ran it locally" without the output;
- someone else's output copied in, including the Builder's when you're verifying;
- a green CI badge on its own;
- a summary of the output instead of the output.

## Who did the work

Every hand-off comment and every verdict names the model that did the work.

- Take it from the session's actual configuration: the model ID stated in your system context, or a session-info tool if you have one. In a Claude Code cloud session, the `get_session` tool reports it.
- Never write a model name from memory or from what seems likely.
- If you can't get it, write "unavailable" and the reason, for example "no session-info tool in this environment".
- Working as a subagent, a session tool describes the parent session. Report that model and say it came from the parent session.

## Where it goes

- **PR description:** under an "Evidence" heading, one entry per completion condition, in the ticket's order.
- **Hand-off or verdict comment:** a table with one row per condition or check: what was checked, the result, and a link or code block. The model goes at the top.

## Don't

- Don't paste secrets, tokens, passwords, cookies or personal data, even inside command output. Redact them as `***` and say that you did.
- Don't commit large logs. Put the relevant lines in the PR, not files in the repo.
- Don't take screenshots from shared or production systems. Use local, throwaway resources only.
