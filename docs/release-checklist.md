# v1.0 Release Checklist

Use this before tagging a public release.

## Product

- README has a clear one-line value proposition.
- Install instructions work for Codex and Claude Code.
- Demo app can be launched locally in under 2 minutes.
- Example reports show JSON, Markdown, and CSV aggregate output.
- Safety model and limitations are visible before usage instructions get deep.

## Skill Quality

- `beta-test-app/SKILL.md` validates against the local skill checker.
- `SKILL.md` stays concise and links to focused references.
- Report schema examples validate with `validate_report.py`.
- Aggregation output is stable between repeated test runs.
- Evals cover happy path, missing credentials, mobile layout, logged-in app, and safety boundaries.

## Repo Hygiene

- No generated files, caches, local reports, or `node_modules/` are committed.
- CI passes on a fresh clone.
- License and contribution guide are present.
- GitHub description and topics are set.
- Release notes include breaking schema changes.

## Suggested GitHub Topics

`agent-skills`, `claude-code`, `codex`, `playwright`, `ux-testing`, `ai-agents`, `beta-testing`, `indie-hackers`

