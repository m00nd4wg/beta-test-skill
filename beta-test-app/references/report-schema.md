# Run Report Schema

Each beta-test session must produce one JSON file. Use stable field names so repeated runs can be validated and aggregated.

## Required Top-Level Fields

- `run_id`: string, for example `run-001`.
- `timestamp`: ISO-8601 string.
- `app_url`: string containing the tested URL or launch target.
- `persona`: object with `label`, `context`, `technical_comfort`, and `goals`.
- `viewport`: object with `device_label`, `width`, and `height`.
- `tasks_attempted`: array of strings.
- `task_outcomes`: array of objects with `task`, `status`, and `notes`.
- `issues`: array of issue objects.
- `overall_sentiment`: string in realistic tester language.
- `top_recommendations`: array of strings.

## Persona

`technical_comfort` must be `low`, `medium`, or `high`.

`goals` must be an array of strings that explain what this tester wanted to accomplish.

## Viewport

`width` and `height` must be positive integers. `device_label` should be a human label such as `desktop`, `mobile`, `tablet`, or `mobile Safari-sized viewport`.

## Task Outcomes

`status` must be one of:

- `success`
- `partial`
- `failed`
- `blocked`
- `abandoned`
- `not-attempted`

## Issues

Each issue must include:

- `title`: short string.
- `category`: one of `bug`, `usability`, `visual-design`, `performance`, `accessibility`, `content`, `trust`, `onboarding`, `conversion`, or `other`.
- `severity`: one of `blocker`, `high`, `medium`, `low`, or `note`.
- `confidence`: one of `high`, `medium`, or `low`.
- `where_seen`: page, route, modal, or UI area.
- `steps_to_reproduce`: array of strings.
- `expected`: string.
- `actual`: string.
- `evidence`: array of strings.
- `tester_reaction`: realistic user-facing reaction.

## Example

```json
{
  "run_id": "run-001",
  "timestamp": "2026-07-02T21:30:00Z",
  "app_url": "https://example.test",
  "persona": {
    "label": "Busy first-time buyer",
    "context": "Wants to compare options quickly during a lunch break.",
    "technical_comfort": "medium",
    "goals": ["Find a suitable plan", "Understand whether checkout is trustworthy"]
  },
  "viewport": {
    "device_label": "mobile",
    "width": 390,
    "height": 844
  },
  "tasks_attempted": ["Open pricing", "Compare plans", "Start checkout with test data"],
  "task_outcomes": [
    {
      "task": "Open pricing",
      "status": "success",
      "notes": "Pricing was reachable from the homepage navigation."
    }
  ],
  "issues": [
    {
      "title": "Checkout button gave no progress feedback",
      "category": "performance",
      "severity": "medium",
      "confidence": "medium",
      "where_seen": "Checkout form",
      "steps_to_reproduce": ["Open pricing", "Choose a plan", "Press checkout"],
      "expected": "The button should show loading or move to the next step promptly.",
      "actual": "The page appeared frozen for about 4 seconds.",
      "evidence": ["Observed spinner absence after pressing checkout"],
      "tester_reaction": "I would probably click twice or assume it broke."
    }
  ],
  "overall_sentiment": "The product made sense, but checkout felt a little fragile.",
  "top_recommendations": ["Add visible progress feedback during checkout."]
}
```
