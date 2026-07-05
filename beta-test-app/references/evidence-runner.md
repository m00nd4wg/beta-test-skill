# Optional Evidence Runner

The core skill does not require Playwright. Use the optional runner only when screenshots, console/network errors, or timing evidence would make the beta-test report more credible.

From the repository root:

```bash
cd runner
npm install
npx playwright install chromium
node evidence-runner.js capture --url http://localhost:4173 --out ../beta-test-results/run-001/evidence --viewport 390x844 --label mobile
```

The runner writes:

- `manifest.json`
- one screenshot
- console message summary
- failed network request summary
- basic navigation and paint timing data when available

Attach the manifest path to the run report's `evidence_manifest_paths`. Attach screenshot paths to the relevant issue's `screenshots`.

The runner is evidence capture, not the tester. The agent must still choose the persona, attempt realistic tasks, interpret UX friction, and write the report.