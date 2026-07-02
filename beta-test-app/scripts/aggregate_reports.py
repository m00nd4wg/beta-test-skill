#!/usr/bin/env python3
"""Aggregate repeated beta-test-app run reports."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validate_report import validate_report


SEVERITY_SCORE = {"note": 0, "low": 1, "medium": 2, "high": 3, "blocker": 4}
CONFIDENCE_SCORE = {"low": 1, "medium": 2, "high": 3}
SCORE_SEVERITY = {value: key for key, value in SEVERITY_SCORE.items()}
SCORE_CONFIDENCE = {value: key for key, value in CONFIDENCE_SCORE.items()}
BUG_LIKE_CATEGORIES = {"bug", "performance", "accessibility"}
SUBJECTIVE_CATEGORIES = {"usability", "visual-design", "content", "trust", "onboarding", "conversion", "other"}
EXCLUDED_JSON_NAMES = {"summary.json", "benchmark.json", "grading.json", "timing.json"}
STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "there",
    "when",
    "then",
    "into",
    "onto",
    "page",
    "screen",
    "button",
    "link",
    "user",
    "users",
    "app",
    "site",
    "website",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def discover_reports(inputs: list[str]) -> list[Path]:
    discovered: list[Path] = []
    for raw in inputs:
        path = Path(raw)
        if path.is_dir():
            discovered.extend(
                item for item in path.rglob("*.json") if item.name not in EXCLUDED_JSON_NAMES
            )
        elif path.is_file():
            discovered.append(path)
        else:
            raise FileNotFoundError(f"input not found: {path}")

    seen: set[Path] = set()
    unique: list[Path] = []
    for path in sorted(discovered, key=lambda item: str(item).lower()):
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def tokenize(text: str) -> set[str]:
    cleaned = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return {token for token in cleaned.split() if len(token) > 2 and token not in STOPWORDS}


def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def persona_label(report: dict[str, Any]) -> str:
    persona = report.get("persona")
    if isinstance(persona, dict):
        label = persona.get("label")
        if isinstance(label, str) and label.strip():
            return label.strip()
    return "Unknown persona"


def report_tasks(report: dict[str, Any]) -> list[str]:
    outcomes = report.get("task_outcomes")
    if isinstance(outcomes, list):
        friction_tasks = [
            item.get("task", "").strip()
            for item in outcomes
            if isinstance(item, dict)
            and item.get("status") in {"partial", "failed", "blocked", "abandoned"}
            and isinstance(item.get("task"), str)
            and item.get("task", "").strip()
        ]
        if friction_tasks:
            return friction_tasks
    tasks = report.get("tasks_attempted")
    if isinstance(tasks, list):
        return [task.strip() for task in tasks if isinstance(task, str) and task.strip()]
    return []


def issue_tokens(issue: dict[str, Any]) -> set[str]:
    text = " ".join(
        str(issue.get(field, ""))
        for field in ["title", "where_seen", "actual", "tester_reaction"]
    )
    return tokenize(text)


def title_tokens(issue: dict[str, Any]) -> set[str]:
    return tokenize(str(issue.get("title", "")))


def choose_representative(entries: list[dict[str, Any]]) -> dict[str, Any]:
    return sorted(
        entries,
        key=lambda entry: (
            -SEVERITY_SCORE.get(entry["issue"].get("severity", "note"), 0),
            entry["issue"].get("title", "").lower(),
            entry["report"].get("run_id", ""),
        ),
    )[0]["issue"]


def unique_sorted(values: list[str], limit: int | None = None) -> list[str]:
    result = sorted({value for value in values if value})
    return result if limit is None else result[:limit]


def confidence_label(score: float) -> str:
    rounded = max(1, min(3, int(round(score))))
    return SCORE_CONFIDENCE[rounded]


def engineering_triage(category: str, severity: str, frequency: int, report_count: int) -> str:
    rate = f"{frequency} of {report_count} runs"
    if category in BUG_LIKE_CATEGORIES:
        if severity in {"blocker", "high"}:
            return f"Prioritize investigation; reproduced or observed in {rate} and has high user impact."
        return f"Investigate after higher-severity blockers; observed in {rate}."
    if category in SUBJECTIVE_CATEGORIES:
        return f"Review with product/design; {rate} reported similar friction, so validate before dismissing as taste."
    return f"Triage with product owner; observed in {rate}."


def cluster_issues(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for report in reports:
        for issue in report.get("issues", []):
            if not isinstance(issue, dict):
                continue
            category = issue.get("category", "other")
            tokens = issue_tokens(issue)
            title_only_tokens = title_tokens(issue)
            best_index: int | None = None
            best_score = 0.0
            for index, group in enumerate(groups):
                if group["category"] != category:
                    continue
                score = max(
                    jaccard(tokens, group["tokens"]),
                    jaccard(title_only_tokens, group["title_tokens"]),
                )
                if score > best_score:
                    best_index = index
                    best_score = score
            entry = {"report": report, "issue": issue}
            if best_index is not None and best_score >= 0.45:
                groups[best_index]["entries"].append(entry)
                groups[best_index]["tokens"] |= tokens
                groups[best_index]["title_tokens"] |= title_only_tokens
            else:
                groups.append(
                    {
                        "category": category,
                        "tokens": set(tokens),
                        "title_tokens": set(title_only_tokens),
                        "entries": [entry],
                    }
                )
    return groups


def summarize_group(group: dict[str, Any], report_count: int) -> dict[str, Any]:
    entries = group["entries"]
    representative = choose_representative(entries)
    run_ids = unique_sorted([str(entry["report"].get("run_id", "")) for entry in entries])
    frequency = len(run_ids)
    severities = [SEVERITY_SCORE.get(entry["issue"].get("severity", "note"), 0) for entry in entries]
    confidences = [CONFIDENCE_SCORE.get(entry["issue"].get("confidence", "low"), 1) for entry in entries]
    max_severity_score = max(severities) if severities else 0
    avg_confidence = sum(confidences) / len(confidences) if confidences else 1.0
    severity = SCORE_SEVERITY[max_severity_score]
    confidence = confidence_label(avg_confidence)
    category = str(representative.get("category", group["category"]))
    score = (frequency * 10) + (max_severity_score * 3) + avg_confidence + math.log1p(len(entries))

    personas = unique_sorted([persona_label(entry["report"]) for entry in entries], limit=6)
    tasks: list[str] = []
    for entry in entries:
        tasks.extend(report_tasks(entry["report"]))

    return {
        "title": representative.get("title", "Untitled issue"),
        "category": category,
        "frequency": frequency,
        "occurrences": len(entries),
        "severity": severity,
        "average_confidence": confidence,
        "score": round(score, 3),
        "affected_run_ids": run_ids,
        "affected_personas": personas,
        "affected_tasks": unique_sorted(tasks, limit=8),
        "sample_where_seen": unique_sorted(
            [str(entry["issue"].get("where_seen", "")) for entry in entries],
            limit=5,
        ),
        "sample_tester_reactions": unique_sorted(
            [str(entry["issue"].get("tester_reaction", "")) for entry in entries],
            limit=5,
        ),
        "sample_steps_to_reproduce": representative.get("steps_to_reproduce", []),
        "engineering_triage": engineering_triage(category, severity, frequency, report_count),
    }


def sort_issue_summaries(summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        summaries,
        key=lambda item: (
            -float(item["score"]),
            -int(item["frequency"]),
            -SEVERITY_SCORE.get(str(item["severity"]), 0),
            str(item["title"]).lower(),
        ),
    )


def build_summary(reports: list[dict[str, Any]]) -> dict[str, Any]:
    report_count = len(reports)
    groups = cluster_issues(reports)
    top_issues = sort_issue_summaries([summarize_group(group, report_count) for group in groups])
    reproducible_bugs = [
        issue for issue in top_issues if issue["category"] in BUG_LIKE_CATEGORIES and issue["frequency"] >= 1
    ]
    subjective_ux_feedback = [
        issue for issue in top_issues if issue["category"] in SUBJECTIVE_CATEGORIES
    ]
    task_statuses = Counter()
    sentiments: list[str] = []
    recommendations: list[str] = []
    for report in reports:
        sentiments.append(str(report.get("overall_sentiment", "")).strip())
        recommendations.extend(
            item.strip()
            for item in report.get("top_recommendations", [])
            if isinstance(item, str) and item.strip()
        )
        for outcome in report.get("task_outcomes", []):
            if isinstance(outcome, dict) and isinstance(outcome.get("status"), str):
                task_statuses[outcome["status"]] += 1

    return {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "input_report_count": report_count,
        "run_ids": unique_sorted([str(report.get("run_id", "")) for report in reports]),
        "issue_count": sum(len(report.get("issues", [])) for report in reports),
        "task_status_counts": dict(sorted(task_statuses.items())),
        "top_issues": top_issues,
        "reproducible_bugs": reproducible_bugs,
        "subjective_ux_feedback": subjective_ux_feedback,
        "common_recommendations": [item for item, _ in Counter(recommendations).most_common(10)],
        "sample_sentiments": unique_sorted(sentiments, limit=8),
    }


def escape_table(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def issue_table(issues: list[dict[str, Any]]) -> str:
    if not issues:
        return "_None recorded._\n"
    lines = [
        "| Issue | Category | Runs | Severity | Confidence | Tester reaction |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for issue in issues:
        reaction = "; ".join(issue.get("sample_tester_reactions", [])[:2])
        lines.append(
            "| {title} | {category} | {frequency} | {severity} | {confidence} | {reaction} |".format(
                title=escape_table(issue["title"]),
                category=escape_table(issue["category"]),
                frequency=issue["frequency"],
                severity=escape_table(issue["severity"]),
                confidence=escape_table(issue["average_confidence"]),
                reaction=escape_table(reaction),
            )
        )
    return "\n".join(lines) + "\n"


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Beta Test Summary",
        "",
        f"Reports analyzed: {summary['input_report_count']}",
        f"Issues recorded: {summary['issue_count']}",
        "",
        "## Top Recurring Issues",
        "",
        issue_table(summary["top_issues"][:10]),
        "## Reproducible Bugs And Technical Issues",
        "",
        issue_table(summary["reproducible_bugs"][:10]),
        "## Subjective UX Feedback",
        "",
        issue_table(summary["subjective_ux_feedback"][:10]),
        "## Common Recommendations",
        "",
    ]
    recommendations = summary.get("common_recommendations", [])
    if recommendations:
        lines.extend(f"{index}. {item}" for index, item in enumerate(recommendations, start=1))
    else:
        lines.append("_None recorded._")
    lines.extend(["", "## Sample Sentiments", ""])
    sentiments = summary.get("sample_sentiments", [])
    if sentiments:
        lines.extend(f"- {item}" for item in sentiments)
    else:
        lines.append("_None recorded._")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate beta-test-app run report JSON files into summary.json and summary.md."
    )
    parser.add_argument("inputs", nargs="+", help="Run report JSON files or directories containing reports.")
    parser.add_argument(
        "--output",
        default="beta-test-summary",
        help="Directory where summary.json and summary.md will be written. Default: beta-test-summary",
    )
    args = parser.parse_args(argv)

    try:
        paths = discover_reports(args.inputs)
    except FileNotFoundError as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, indent=2))
        return 1

    if not paths:
        print(json.dumps({"ok": False, "errors": ["no report JSON files found"]}, indent=2))
        return 1

    reports: list[dict[str, Any]] = []
    invalid: dict[str, list[str]] = {}
    for path in paths:
        try:
            data = load_json(path)
        except json.JSONDecodeError as exc:
            invalid[str(path)] = [f"invalid JSON: {exc}"]
            continue
        errors = validate_report(data)
        if errors:
            invalid[str(path)] = errors
            continue
        reports.append(data)

    if invalid:
        print(json.dumps({"ok": False, "invalid_reports": invalid}, indent=2, sort_keys=True))
        return 1

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = build_summary(reports)
    summary_json = output_dir / "summary.json"
    summary_md = output_dir / "summary.md"
    summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_md.write_text(render_markdown(summary), encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "reports": len(reports),
                "summary_json": str(summary_json),
                "summary_md": str(summary_md),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
