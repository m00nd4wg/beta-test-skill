# Contributing

Thanks for helping make agent beta testing more useful for builders.

## Good First Contributions

- Add realistic eval prompts in `evals/evals.json`.
- Improve the flawed demo app with obvious but believable UX defects.
- Add example reports from real app categories.
- Improve clustering or CSV output in `beta-test-app/scripts/aggregate_reports.py`.
- Tighten validation and error messages in `beta-test-app/scripts/validate_report.py`.

## Quality Bar

- Keep the core skill portable across Codex, Claude Code, and other Agent Skills clients.
- Keep `beta-test-app/SKILL.md` concise; move detail into `references/`.
- Prefer Python standard-library scripts inside the skill.
- Keep Playwright in `runner/` optional.
- Add or update tests for script behavior.

## Local Checks

```bash
python tools/check_skill.py beta-test-app
python -m unittest discover -s tests
python beta-test-app/scripts/validate_report.py examples/reports/run-001.json
python beta-test-app/scripts/aggregate_reports.py examples/reports --output /tmp/beta-test-summary
node runner/evidence-runner.js --help
```

## Pull Request Notes

Include:

- what changed
- why it improves beta-test quality or repo usability
- what checks you ran
- any limitations or follow-up work

