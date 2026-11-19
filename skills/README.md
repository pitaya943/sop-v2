# Skills

One directory per skill: `skills/<name>/SKILL.md`, plus any reference files the skill reads on demand. Skill bodies are written in English for agents (design decision O1); the documents a skill produces follow the project's configured language.

Every directory here must be listed in `.claude-plugin/plugin.json`, and every listed path must exist. `python3 scripts/check_skills.py` enforces both, along with these rules:

- **Frontmatter:** `name` (equal to the directory name) and `description` (at most 1024 characters) are required. Optional keys: `disable-model-invocation`, `argument-hint`, `allowed-tools`. Quote any value that contains `: ` or starts with a YAML indicator character.
- **Two kinds:**
  - **User-invoked** skills orchestrate a piece of work and set `disable-model-invocation: true`.
  - **Model-invoked** skills hold reusable discipline the agent reaches for on its own.

  A user-invoked skill may call model-invoked ones, but never another user-invoked skill.
- **Short:** each `SKILL.md` is at most 80 lines. Put details in a sibling file and point to it.
- **No personal data:** use fictional examples such as `example-owner` and `example-bot`.

See [design doc section 5](../docs/design/v3-lightweight-design.md#5-skill-清單--the-skills) for the planned skills.
