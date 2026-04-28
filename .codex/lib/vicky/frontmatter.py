#!/usr/bin/env python3
"""Shared frontmatter helpers for Vicky tools."""

from __future__ import annotations

import re
from pathlib import Path

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def parse_scalar(value: str):
    if not value:
        return ""
    if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()]
    if value.lower() in {"true", "yes"}:
        return True
    if value.lower() in {"false", "no"}:
        return False
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    return value


def _parse_block_list(lines: list[str]) -> list:
    items: list = []
    current_dict: dict | None = None
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            if current_dict is not None:
                items.append(current_dict)
                current_dict = None
            item_content = stripped[2:].strip()
            if ":" in item_content:
                current_dict = {}
                key, _, value = item_content.partition(":")
                current_dict[key.strip()] = parse_scalar(value.strip())
            else:
                items.append(parse_scalar(item_content))
            continue
        if current_dict is not None and ":" in stripped:
            key, _, value = stripped.partition(":")
            current_dict[key.strip()] = parse_scalar(value.strip())
    if current_dict is not None:
        items.append(current_dict)
    return items


def _parse_block_value(lines: list[str]):
    content_lines = [line for line in lines if line.strip()]
    if not content_lines:
        return ""
    first = content_lines[0].strip()
    if first.startswith("- "):
        return _parse_block_list(lines)
    if ":" in first:
        result = {}
        for line in content_lines:
            stripped = line.strip()
            if ":" not in stripped:
                continue
            key, _, value = stripped.partition(":")
            result[key.strip()] = parse_scalar(value.strip())
        return result
    return ""


def parse_yaml_block(text: str) -> dict:
    result: dict = {}
    lines = text.split("\n")
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        if ":" not in stripped or line.startswith(" "):
            index += 1
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if value:
            result[key] = parse_scalar(value)
            index += 1
            continue
        block_lines: list[str] = []
        index += 1
        while index < len(lines):
            next_line = lines[index]
            if next_line and not next_line[0].isspace():
                break
            block_lines.append(next_line)
            index += 1
        result[key] = _parse_block_value(block_lines)
    return result


def parse_frontmatter(content: str) -> dict:
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}
    return parse_yaml_block(match.group(1))


def parse_frontmatter_file(path: Path) -> dict:
    try:
        return parse_frontmatter(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return {}


def serialize_frontmatter(frontmatter: dict) -> str:
    lines: list[str] = []
    for key, value in frontmatter.items():
        if value in ("", None):
            lines.append(f'{key}: ""')
        elif isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, (int, float)):
            lines.append(f"{key}: {value}")
        elif isinstance(value, str):
            if any(ch in value for ch in ':#{}[]&*!|>\',"'):
                lines.append(f'{key}: "{value}"')
            else:
                lines.append(f"{key}: {value}")
        elif isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
            elif all(not isinstance(item, dict) for item in value):
                lines.append(f"{key}:")
                for item in value:
                    rendered = str(item)
                    if isinstance(item, str) and any(ch in item for ch in ":#,[]"):
                        rendered = f'"{item}"'
                    lines.append(f"  - {rendered}")
            else:
                lines.append(f"{key}:")
                for item in value:
                    if isinstance(item, dict):
                        first = True
                        for dict_key, dict_value in item.items():
                            prefix = "  - " if first else "    "
                            first = False
                            lines.append(f"{prefix}{dict_key}: {dict_value}")
                    else:
                        lines.append(f"  - {item}")
        elif isinstance(value, dict):
            lines.append(f"{key}:")
            for dict_key, dict_value in value.items():
                lines.append(f"  {dict_key}: {dict_value}")
    return "\n".join(lines) + "\n"


def update_frontmatter_field(content: str, field: str, value, append: bool = False):
    match = FRONTMATTER_RE.match(content)
    if not match:
        raise ValueError("No frontmatter found")
    frontmatter = parse_yaml_block(match.group(1))
    if field not in frontmatter and not append:
        raise ValueError(f"Field '{field}' not found in frontmatter")
    old_value = frontmatter.get(field, "")
    if append:
        existing = frontmatter.get(field, [])
        if isinstance(existing, list):
            if value not in existing:
                existing.append(value)
            frontmatter[field] = existing
        elif existing:
            frontmatter[field] = [existing, value]
        else:
            frontmatter[field] = [value]
    else:
        frontmatter[field] = value
    new_content = f"---\n{serialize_frontmatter(frontmatter)}---{content[match.end():]}"
    return new_content, old_value, frontmatter[field]
