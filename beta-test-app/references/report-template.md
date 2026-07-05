# Beta-Test Run Note

Use this template for an optional human-readable note alongside the JSON report.

```markdown
# Beta Test Run: <run_id>

Tested: <app_url>
Persona: <label>
Viewport: <device_label> (<width>x<height>)
Schema: 2.0

## What I Tried

- <task>
- <task>

## What Happened

<A short narrative in the tester's voice. Include confusion, pleasant surprises, impatience, visual reactions, and whether the main goal was completed.>

## Issues Noticed

| Severity | Category | Friction | Issue | Where | Reaction |
| --- | --- | ---: | --- | --- | --- |
| medium | usability | 3 | <title> | <where_seen> | <tester_reaction> |

## Evidence

- Screenshots: <paths or none>
- Console/network notes: <short notes or none>
- Perceived latency: <duration or none>

## Overall Sentiment

<One or two sentences that sound like a real beta tester, not a release manager.>

## Top Recommendations

1. <recommendation>
2. <recommendation>
```

Keep the Markdown concise. The JSON report is the source of truth for aggregation.