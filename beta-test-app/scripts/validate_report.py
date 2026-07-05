#!/usr/bin/env python3
"""Validate one beta-test-app run report."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "2.0"
CATEGORIES = {
    "bug",
    "usability",
    "visual-design",
    "performance",
    "accessibility",
    "content",
    "trust",
    "onboarding",
    "conversion",
    "other",
}
SEVERITIES = {"blocker", "high", "medium", "low", "note"}
CONFIDENCES = {"high", "medium", "low"}
COMFORT_LEVELS = {"low", "medium", "high"}
TASK_STATUSES = {"success", "partial", "failed", "blocked", "abandoned", "not-attempted"}
FINGERPRINT_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

REQUIRED_TOP_LEVEL = [
    "schema_version",
    "run_id",
    "timestamp",
    "app_url",
    "persona",
    "viewport",
    "tasks_attempted",
    "task_outcomes",
    "issues",
    "overall_sentiment",
    "top_recommendations",
]

REQUIRED_ISSUE_FIELDS = [
    "title",
    "category",
    "severity",
    "confidence",
    "where_seen",
    "steps_to_reproduce",
    "expected",
    "actual",
    "evidence",
    "tester_reaction",
]

OPTIONAL_STRING_LISTS = ["assumptions", "safety_notes", "evidence_manifest_paths"]
OPTIONAL_ISSUE_STRING_LISTS = ["screenshots", "console_errors", "network_errors"]


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def list_of_strings(value: Any, *, allow_empty: bool = True) -> bool:
    return isinstance(value, list) and (allow_empty or len(value) > 0) and all(non_empty_string(item) for item in value)


def add_error(errors: list[str], path: str, message: str) -> None:
    errors.append(f"{path}: {message}")


def validate_timestamp(value: Any, errors: list[str]) -> None:
    if not non_empty_string(value):
        add_error(errors, "timestamp", "must be a non-empty ISO-8601 string")
        return
    normalized = value.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(normalized)
    except ValueError:
        add_error(errors, "timestamp", "must parse as ISO-8601")


def validate_int_range(value: Any, path: str, errors: list[str], *, minimum: int, maximum: int | None = None) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        add_error(errors, path, "must be an integer")
        return
    if value < minimum:
        add_error(errors, path, f"must be >= {minimum}")
    if maximum is not None and value > maximum:
        add_error(errors, path, f"must be <= {maximum}")


def validate_persona(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        add_error(errors, "persona", "must be an object")
        return
    for field in ["label", "context", "technical_comfort", "goals"]:
        if field not in value:
            add_error(errors, f"persona.{field}", "is required")
    for field in ["label", "context"]:
        if field in value and not non_empty_string(value[field]):
            add_error(errors, f"persona.{field}", "must be a non-empty string")
    if "technical_comfort" in value and value["technical_comfort"] not in COMFORT_LEVELS:
        add_error(errors, "persona.technical_comfort", f"must be one of {sorted(COMFORT_LEVELS)}")
    if "domain_familiarity" in value and value["domain_familiarity"] not in COMFORT_LEVELS:
        add_error(errors, "persona.domain_familiarity", f"must be one of {sorted(COMFORT_LEVELS)}")
    if "goals" in value and not list_of_strings(value["goals"], allow_empty=False):
        add_error(errors, "persona.goals", "must be a non-empty array of non-empty strings")
    if "biases" in value and not list_of_strings(value["biases"]):
        add_error(errors, "persona.biases", "must be an array of non-empty strings")


def validate_viewport(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        add_error(errors, "viewport", "must be an object")
        return
    for field in ["device_label", "width", "height"]:
        if field not in value:
            add_error(errors, f"viewport.{field}", "is required")
    if "device_label" in value and not non_empty_string(value["device_label"]):
        add_error(errors, "viewport.device_label", "must be a non-empty string")
    for field in ["width", "height"]:
        if field in value:
            validate_int_range(value[field], f"viewport.{field}", errors, minimum=1)


def validate_task_outcomes(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list):
        add_error(errors, "task_outcomes", "must be an array")
        return
    for index, outcome in enumerate(value):
        path = f"task_outcomes[{index}]"
        if not isinstance(outcome, dict):
            add_error(errors, path, "must be an object")
            continue
        for field in ["task", "status", "notes"]:
            if field not in outcome:
                add_error(errors, f"{path}.{field}", "is required")
        if "task" in outcome and not non_empty_string(outcome["task"]):
            add_error(errors, f"{path}.task", "must be a non-empty string")
        if "status" in outcome and outcome["status"] not in TASK_STATUSES:
            add_error(errors, f"{path}.status", f"must be one of {sorted(TASK_STATUSES)}")
        if "notes" in outcome and not non_empty_string(outcome["notes"]):
            add_error(errors, f"{path}.notes", "must be a non-empty string")
        if "friction_score" in outcome:
            validate_int_range(outcome["friction_score"], f"{path}.friction_score", errors, minimum=0, maximum=5)
        if "duration_ms" in outcome:
            validate_int_range(outcome["duration_ms"], f"{path}.duration_ms", errors, minimum=0)


def validate_fingerprint(value: Any, path: str, errors: list[str]) -> None:
    if not non_empty_string(value):
        add_error(errors, path, "must be a non-empty string")
        return
    if not FINGERPRINT_PATTERN.match(value):
        add_error(errors, path, "must be lowercase alphanumeric words separated by single hyphens")


def validate_issues(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list):
        add_error(errors, "issues", "must be an array")
        return
    for index, issue in enumerate(value):
        path = f"issues[{index}]"
        if not isinstance(issue, dict):
            add_error(errors, path, "must be an object")
            continue
        for field in REQUIRED_ISSUE_FIELDS:
            if field not in issue:
                add_error(errors, f"{path}.{field}", "is required")
        for field in ["title", "where_seen", "expected", "actual", "tester_reaction"]:
            if field in issue and not non_empty_string(issue[field]):
                add_error(errors, f"{path}.{field}", "must be a non-empty string")
        if "category" in issue and issue["category"] not in CATEGORIES:
            add_error(errors, f"{path}.category", f"must be one of {sorted(CATEGORIES)}")
        if "severity" in issue and issue["severity"] not in SEVERITIES:
            add_error(errors, f"{path}.severity", f"must be one of {sorted(SEVERITIES)}")
        if "confidence" in issue and issue["confidence"] not in CONFIDENCES:
            add_error(errors, f"{path}.confidence", f"must be one of {sorted(CONFIDENCES)}")
        if "steps_to_reproduce" in issue and not list_of_strings(issue["steps_to_reproduce"], allow_empty=False):
            add_error(errors, f"{path}.steps_to_reproduce", "must be a non-empty array of non-empty strings")
        if "evidence" in issue and not list_of_strings(issue["evidence"], allow_empty=False):
            add_error(errors, f"{path}.evidence", "must be a non-empty array of non-empty strings")
        if "fingerprint" in issue:
            validate_fingerprint(issue["fingerprint"], f"{path}.fingerprint", errors)
        if issue.get("confidence") in {"low", "medium"} and not non_empty_string(issue.get("confidence_rationale")):
            add_error(errors, f"{path}.confidence_rationale", "is required for low or medium confidence issues")
        if "confidence_rationale" in issue and not non_empty_string(issue["confidence_rationale"]):
            add_error(errors, f"{path}.confidence_rationale", "must be a non-empty string")
        if "friction_score" in issue:
            validate_int_range(issue["friction_score"], f"{path}.friction_score", errors, minimum=0, maximum=5)
        if "perceived_latency_ms" in issue:
            validate_int_range(issue["perceived_latency_ms"], f"{path}.perceived_latency_ms", errors, minimum=0)
        for field in OPTIONAL_ISSUE_STRING_LISTS:
            if field in issue and not list_of_strings(issue[field]):
                add_error(errors, f"{path}.{field}", "must be an array of non-empty strings")


def validate_report(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["$: report must be a JSON object"]

    for field in REQUIRED_TOP_LEVEL:
        if field not in data:
            add_error(errors, field, "is required")

    if "schema_version" in data and data["schema_version"] != SCHEMA_VERSION:
        add_error(errors, "schema_version", f"must be {SCHEMA_VERSION!r}")

    for field in ["run_id", "app_url", "overall_sentiment"]:
        if field in data and not non_empty_string(data[field]):
            add_error(errors, field, "must be a non-empty string")
    if "app_context" in data and not non_empty_string(data["app_context"]):
        add_error(errors, "app_context", "must be a non-empty string")

    if "timestamp" in data:
        validate_timestamp(data["timestamp"], errors)
    if "persona" in data:
        validate_persona(data["persona"], errors)
    if "viewport" in data:
        validate_viewport(data["viewport"], errors)
    if "tasks_attempted" in data and not list_of_strings(data["tasks_attempted"], allow_empty=False):
        add_error(errors, "tasks_attempted", "must be a non-empty array of non-empty strings")
    if "task_outcomes" in data:
        validate_task_outcomes(data["task_outcomes"], errors)
    if "issues" in data:
        validate_issues(data["issues"], errors)
    if "top_recommendations" in data and not list_of_strings(data["top_recommendations"]):
        add_error(errors, "top_recommendations", "must be an array of non-empty strings")
    for field in OPTIONAL_STRING_LISTS:
        if field in data and not list_of_strings(data[field]):
            add_error(errors, field, "must be an array of non-empty strings")

    return errors


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate one beta-test-app v2 run report JSON file.")
    parser.add_argument("report", help="Path to a run-NNN.json report file.")
    parser.add_argument("--quiet", action="store_true", help="Only print output when validation fails.")
    args = parser.parse_args(argv)

    path = Path(args.report)
    try:
        data = load_json(path)
    except FileNotFoundError:
        print(json.dumps({"valid": False, "file": str(path), "errors": ["file not found"]}, indent=2))
        return 1
    except json.JSONDecodeError as exc:
        print(json.dumps({"valid": False, "file": str(path), "errors": [f"invalid JSON: {exc}"]}, indent=2))
        return 1

    errors = validate_report(data)
    result = {
        "valid": not errors,
        "file": str(path),
        "schema_version": data.get("schema_version") if isinstance(data, dict) else None,
        "run_id": data.get("run_id") if isinstance(data, dict) else None,
        "issue_count": len(data.get("issues", [])) if isinstance(data, dict) and isinstance(data.get("issues"), list) else 0,
        "errors": errors,
    }
    if errors or not args.quiet:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())