#!/usr/bin/env python3
"""Validate one beta-test-app run report."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


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
TECHNICAL_COMFORT = {"low", "medium", "high"}
TASK_STATUSES = {"success", "partial", "failed", "blocked", "abandoned", "not-attempted"}

REQUIRED_TOP_LEVEL = [
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


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def list_of_strings(value: Any) -> bool:
    return isinstance(value, list) and all(non_empty_string(item) for item in value)


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


def validate_persona(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        add_error(errors, "persona", "must be an object")
        return
    for field in ["label", "context", "technical_comfort", "goals"]:
        if field not in value:
            add_error(errors, f"persona.{field}", "is required")
    if "label" in value and not non_empty_string(value["label"]):
        add_error(errors, "persona.label", "must be a non-empty string")
    if "context" in value and not non_empty_string(value["context"]):
        add_error(errors, "persona.context", "must be a non-empty string")
    if "technical_comfort" in value and value["technical_comfort"] not in TECHNICAL_COMFORT:
        add_error(errors, "persona.technical_comfort", f"must be one of {sorted(TECHNICAL_COMFORT)}")
    if "goals" in value and not list_of_strings(value["goals"]):
        add_error(errors, "persona.goals", "must be an array of non-empty strings")


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
        if field in value and (not isinstance(value[field], int) or value[field] <= 0):
            add_error(errors, f"viewport.{field}", "must be a positive integer")


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
        if "steps_to_reproduce" in issue and not list_of_strings(issue["steps_to_reproduce"]):
            add_error(errors, f"{path}.steps_to_reproduce", "must be an array of non-empty strings")
        if "evidence" in issue and not list_of_strings(issue["evidence"]):
            add_error(errors, f"{path}.evidence", "must be an array of non-empty strings")


def validate_report(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["$: report must be a JSON object"]

    for field in REQUIRED_TOP_LEVEL:
        if field not in data:
            add_error(errors, field, "is required")

    for field in ["run_id", "app_url", "overall_sentiment"]:
        if field in data and not non_empty_string(data[field]):
            add_error(errors, field, "must be a non-empty string")

    if "timestamp" in data:
        validate_timestamp(data["timestamp"], errors)
    if "persona" in data:
        validate_persona(data["persona"], errors)
    if "viewport" in data:
        validate_viewport(data["viewport"], errors)
    if "tasks_attempted" in data and not list_of_strings(data["tasks_attempted"]):
        add_error(errors, "tasks_attempted", "must be an array of non-empty strings")
    if "task_outcomes" in data:
        validate_task_outcomes(data["task_outcomes"], errors)
    if "issues" in data:
        validate_issues(data["issues"], errors)
    if "top_recommendations" in data and not list_of_strings(data["top_recommendations"]):
        add_error(errors, "top_recommendations", "must be an array of non-empty strings")

    return errors


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate one beta-test-app run report JSON file.")
    parser.add_argument("report", help="Path to a run-NNN.json report file.")
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
        "run_id": data.get("run_id") if isinstance(data, dict) else None,
        "issue_count": len(data.get("issues", [])) if isinstance(data, dict) and isinstance(data.get("issues"), list) else 0,
        "errors": errors,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
