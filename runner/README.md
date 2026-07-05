# Optional Evidence Runner

This runner is optional. The `beta-test-app` skill works without it.

Use it when an agent wants repeatable evidence:

```bash
npm install
npx playwright install chromium
node evidence-runner.js capture --url http://localhost:4173 --out ../beta-test-results/run-001/evidence --viewport 390x844 --label mobile
```

The runner writes a screenshot, manifest, console messages, failed requests, and basic page timing data.

