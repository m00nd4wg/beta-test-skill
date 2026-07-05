# Beta-Test Protocol

Use this protocol to run realistic, repeated beta-test sessions for an app or website. Favor normal user behavior over exhaustive QA unless the user asks for strict test coverage.

## Intake

Collect only what is needed to test safely:

- Target: public URL, local URL, or launch command.
- Product context: what the app is for, target audience, and primary success action, if not obvious from the app.
- Access: test credentials, invite links, test tenant, or demo data when login is required.
- Boundaries: actions to avoid, especially purchases, subscriptions, messages to real people, destructive edits, admin actions, production data, and real personal information.
- Run count: default to 5 independent sessions.
- Evidence preference: whether screenshots, console/network errors, or page timing manifests are useful.

If the target is missing, ask for it. If context is missing but the app can be explored safely, infer it and label assumptions in the report.

## Session Design

For each run, choose a different realistic tester. Use a named persona, not a generic segment:

- Persona: role, motivation, technical comfort, domain familiarity, and patience level.
- Device: mix desktop, tablet, and mobile viewports where possible.
- Entry path: direct link, homepage, invitation link, search result, returning-user path, or deep link if available.
- Goal: one primary task and one or two secondary tasks that fit the product context.
- Bias: one realistic preference or anxiety, such as "hates salesy copy", "worries about accidental charges", "skims visual hierarchy first", or "expects keyboard-friendly forms".

Keep runs independent. Do not tell later personas what earlier testers found. Repeated issues should emerge through aggregation, not through biased retesting.

## Task Selection

Generate tasks from the app context. Prefer tasks a real beta tester would attempt:

- Understand what the product does.
- Sign up, sign in, or recover from authentication friction using test credentials.
- Complete the main value workflow.
- Search, filter, compare, configure, save, share, export, or return to previous work when relevant.
- Explore pricing, trust, help, empty states, settings, errors, and mobile layout.
- Try one slightly messy behavior per run, such as using the back button, refreshing, typoing a search, pausing on a loader, resizing, or abandoning a confusing flow.
- Include one "is this worth trusting?" moment when appropriate: pricing, security, data handling, cancellation, support, testimonials, or account settings.

Do not use a rigid checklist for every session. Realism matters: a tester can get distracted, misunderstand copy, dislike a palette, or decide a flow feels too slow.

## Evidence Capture

For every issue, capture enough detail to make the report useful:

- Where it happened: page, route, modal, form, or visible UI label.
- Steps to reproduce: concise actions from a realistic starting point.
- Expected versus actual behavior.
- Evidence: screenshot paths, console errors, network errors, visible text, approximate wait time, or direct observation.
- Tester reaction: what a normal user would say or feel.
- Confidence: high for directly observed/repeated behavior, medium for a strong single observation, low for subjective or uncertain impressions.
- Confidence rationale: one short reason for the confidence rating.
- Task friction score: 0 means effortless; 5 means blocked or likely to abandon.
- Fingerprint: a stable issue key that clusters repeated behavior across runs.

Separate perceived performance from measured performance. A report like "felt slow because the button showed no progress for about 4 seconds" is valid even without lab metrics.

## Safety Boundaries

Never complete purchases, send messages to real users, publish public content, delete or overwrite meaningful data, scrape private data, bypass access controls, or use real personal information unless the user explicitly authorized that action for the test environment.

Use harmless test data. Mask secrets in reports. If a risky action is necessary to continue, stop and ask.

## End Of Each Run

Write a JSON report that follows `references/report-schema.md`. Add a short Markdown note from `references/report-template.md` when the run has narrative feedback that would help a product owner.

After multiple runs, aggregate results. Treat fewer than 20 sessions as directional signal, not statistical proof. Report frequencies plainly, such as "3 of 5 testers encountered this."

## Common Failure Modes To Notice

- A tester cannot explain the product after the first screen.
- A primary action is visually hidden, disabled without explanation, or delayed without feedback.
- Copy creates risk anxiety: pricing, cancellation, privacy, data loss, or account changes feel unclear.
- Mobile layout changes the task, not just the screen size.
- Empty states, loading states, and errors sound like implementation details instead of helpful guidance.
- Visual design feels pretty but weakens readability, hierarchy, or confidence.