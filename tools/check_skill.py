#!/usr/bin/env python3
"""Small dependency-free skill structure validator for CI."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def parse_frontmatter(text: str) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    if text.startswith("\ufeff"):
        errors.append("SKILL.md must be UTF-8 without BOM")
        text = text.lstrip("\ufeff")
    if not text.startswith("---\n"):
        errors.append("SKILL.md must start with YAML frontmatter")
        return {}, errors
    try:
        _, frontmatter, _ = text.split("---", 2)
    except ValueError:
        errors.append("SKILL.md frontmatter must be closed with ---")
        return {}, errors
    fields: dict[str, str] = {}
    for raw_line in frontmatter.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if ":" not in line:
            errors.append(f"frontmatter line is not key/value: {raw_line}")
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"')
    return fields, errors


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"
    if not skill_dir.is_dir():
        return [f"{skill_dir} is not a directory"]
    if not skill_file.is_file():
        return [f"{skill_file} is missing"]

    text = skill_file.read_text(encoding="utf-8")
    fields, parse_errors = parse_frontmatter(text)
    errors.extend(parse_errors)
    name = fields.get("name")
    description = fields.get("description")
    if not name:
        errors.append("frontmatter.name is required")
    elif name != skill_dir.name:
        errors.append(f"frontmatter.name must match directory name {skill_dir.name!r}")
    elif not NAME_PATTERN.match(name):
        errors.append("frontmatter.name must be lowercase letters, digits, and single hyphens")
    if not description:
        errors.append("frontmatter.description is required")
    elif len(description) > 1024:
        errors.append("frontmatter.description must be <= 1024 characters")

    if "references/" not in text or "scripts/" not in text:
        errors.append("SKILL.md should mention references/ and scripts/ resources")
    if not (skill_dir / "agents" / "openai.yaml").is_file():
        errors.append("agents/openai.yaml is missing")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate this repo's Agent Skill structure.")
    parser.add_argument("skill_dir", help="Path to the skill directory.")
    args = parser.parse_args(argv)
    errors = validate_skill(Path(args.skill_dir))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Skill structure is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

