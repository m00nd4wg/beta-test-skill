from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "beta-test-app" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from aggregate_reports import build_summary, main as aggregate_main  # noqa: E402
from validate_report import validate_report  # noqa: E402


class ReportValidationTests(unittest.TestCase):
    def load_example(self, name: str) -> dict:
        return json.loads((ROOT / "examples" / "reports" / name).read_text(encoding="utf-8"))

    def test_example_report_is_valid(self) -> None:
        report = self.load_example("run-001.json")
        self.assertEqual(validate_report(report), [])

    def test_schema_version_is_required(self) -> None:
        report = self.load_example("run-001.json")
        report.pop("schema_version")
        errors = validate_report(report)
        self.assertTrue(any("schema_version" in error for error in errors))

    def test_medium_confidence_needs_rationale(self) -> None:
        report = self.load_example("run-001.json")
        report["issues"][0].pop("confidence_rationale")
        errors = validate_report(report)
        self.assertTrue(any("confidence_rationale" in error for error in errors))

    def test_aggregate_clusters_matching_fingerprints(self) -> None:
        reports = [self.load_example("run-001.json"), self.load_example("run-002.json")]
        summary = build_summary(reports)
        top = summary["top_issues"][0]
        self.assertEqual(top["fingerprint"], "signup-cta-no-progress-feedback")
        self.assertEqual(top["frequency"], 2)

    def test_aggregate_writes_json_markdown_and_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_dir = tmp_path / "reports"
            output_dir = tmp_path / "summary"
            shutil.copytree(ROOT / "examples" / "reports", input_dir)
            exit_code = aggregate_main([str(input_dir), "--output", str(output_dir)])
            self.assertEqual(exit_code, 0)
            self.assertTrue((output_dir / "summary.json").is_file())
            self.assertTrue((output_dir / "summary.md").is_file())
            self.assertTrue((output_dir / "summary.csv").is_file())


if __name__ == "__main__":
    unittest.main()

