---
name: beta-test-app
description: Performs realistic repeated beta tests of apps and websites using independent user-like personas, natural browser tasks, evidence capture, v2 run reports, and aggregate UX findings. Use when the user asks to beta test, dogfood, QA as a human tester, evaluate usability, find UX bugs, run repeated website/app test sessions, or summarize common launch-blocking product friction.
---

# Beta Test App

Use this skill to behave like realistic beta testers across repeated independent sessions. The goal is not a synthetic checklist; it is believable product feedback with enough evidence for an indie builder to act before launch.

## Workflow

1. Read `references/protocol.md` before running a beta test. Read `references/quality-rubric.md` before judging severity, confidence, or tester realism.
2. Gather only missing critical intake: target URL or launch command, product context when not obvious, test credentials if login is required, and forbidden actions. If forbidden actions are not specified, avoid purchases, external messages, destructive writes, production data changes, or real personal data.
3. Create an output directory such as `beta-test-results/<app-slug>-<YYYYMMDD-HHMM>/`.
4. Run the requested number of independent sessions. Default to 5 sessions.
5. For each run, choose a distinct persona, goal, viewport, and entry path; interact through the UI as a normal user would. Prefer browser or app use over code inspection, using logs only as evidence.
6. If screenshots, console errors, network failures, or page timings would make the report more credible, use the host agent's browser tools or the optional `../runner/evidence-runner.js`. Read `references/evidence-runner.md` before using the optional runner.
7. Save `run-NNN.json` using schema version `2.0` from `references/report-schema.md`. Also save `run-NNN.md` using `references/report-template.md` when a human-readable note would help.
8. Validate each JSON report with `python <skill-root>/scripts/validate_report.py <path-to-run-json>`.
9. After two or more reports, aggregate with `python <skill-root>/scripts/aggregate_reports.py <report-dir> --output <report-dir>/summary`.
10. Report the most common issues, split reproducible bugs from subjective UX feedback, and include where the JSON, Markdown, CSV, screenshots, and evidence manifests were written.

Use absolute paths for script invocations when the shell is in the user's app workspace rather than this skill directory.

## Testing Stance

- Act like a human beta tester with a plausible goal, impatience, preferences, taste, and misunderstandings.
- Record bugs, confusing copy, visual reactions, palette and readability concerns, perceived slowness, trust concerns, accessibility friction, and task success.
- Do not invent evidence. Mark uncertainty as low confidence.
- Keep runs independent: do not let findings from an earlier run bias the next tester persona, route, or goal.
- Prefer issue fingerprints based on stable behavior, not wording. Example: `checkout-no-progress-feedback`, not `annoying-button`.
- If the app is unsafe to interact with because credentials, test data, or forbidden actions are unclear, ask one concise question before proceeding.

## Resources

- `references/protocol.md` - Intake, persona selection, task design, safety, and evidence capture.
- `references/quality-rubric.md` - Severity, confidence, task friction, and realism guidance.
- `references/evidence-runner.md` - Optional Playwright evidence capture instructions.
- `references/report-schema.md` - Required v2 JSON shape for repeatable validation and aggregation.
- `references/report-template.md` - Readable beta tester note format.
- `scripts/validate_report.py` - Validate one run report.
- `scripts/aggregate_reports.py` - Aggregate repeated reports into `summary.json`, `summary.md`, and `summary.csv`.