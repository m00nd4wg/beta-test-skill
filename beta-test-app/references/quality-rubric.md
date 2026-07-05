# Beta-Test Quality Rubric

Use this rubric to keep repeated runs realistic and comparable.

## Severity

- `blocker`: The tester cannot complete the primary task or cannot proceed safely.
- `high`: A major flow is confusing, broken, risky, or likely to cause abandonment.
- `medium`: Noticeable friction that slows the task, reduces trust, or causes repeated hesitation.
- `low`: Polish, readability, minor confusion, or subjective preference that does not block the task.
- `note`: Observation worth preserving but not currently actionable.

## Confidence

- `high`: Directly observed, reproducible, or supported by multiple evidence points.
- `medium`: Directly observed once, or strongly inferred from visible behavior.
- `low`: Subjective reaction, weak evidence, or a possible tester misunderstanding.

Always add `confidence_rationale` for medium and low confidence issues.

## Task Friction Score

- `0`: Effortless.
- `1`: Minor pause but task still feels smooth.
- `2`: Noticeable friction; tester adapts without losing confidence.
- `3`: Meaningful hesitation, second-guessing, or repeated action.
- `4`: Tester nearly abandons or needs a workaround.
- `5`: Blocked, unsafe, or likely to abandon.

## Realism Checks

- A real tester has a goal, mood, and time pressure.
- A real tester may misunderstand copy instead of reading every word.
- A real tester reports taste and trust reactions, not only bugs.
- A real tester can be wrong; mark those observations low confidence instead of deleting them.
- Do not convert every reaction into an engineering defect. Preserve subjective UX feedback separately.

## Issue Fingerprints

Use stable lowercase fingerprints that describe behavior:

- Good: `checkout-no-progress-feedback`
- Good: `mobile-pricing-link-hidden`
- Bad: `run-001-issue-2`
- Bad: `annoying-blue-button`

Fingerprints should survive wording differences across personas.