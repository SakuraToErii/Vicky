#!/usr/bin/env python3
"""Shared frontmatter helpers for Vicky tools."""

from __future__ import annotations

from datetime import date, datetime
import re
from pathlib import Path

import yaml

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


class FrontmatterDumper(yaml.SafeDumper):
    """Stable YAML dumper for Obsidian-friendly frontmatter."""

    def increase_indent(self, flow: bool = False, indentless: bool = False):
        return super().increase_indent(flow, False)


def _needs_quotes(value: str) -> bool:
    if value == "":
        return True
    if value[0].isspace() or value[-1].isspace():
        return True
    if "\n" in value or "\r" in value or "\t" in value:
        return True
    if any(ch in value for ch in ':#{}[]&*!|>\',"'):
        return True
    if value.startswith(("-", "?", "@", "`")):
        return True
    try:
        parsed = yaml.safe_load(value)
    except yaml.YAMLError:
        return True
    return parsed is None or not isinstance(parsed, str)


def _represent_str(dumper: FrontmatterDumper, value: str):
    style = '"' if _needs_quotes(value) else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


FrontmatterDumper.add_representer(str, _represent_str)


def parse_scalar(value: str):
    if value == "":
        return ""
    if re.fullmatch(r"\[\[[^\]]+\]\]", value):
        return value
    try:
        parsed = yaml.safe_load(value)
    except yaml.YAMLError:
        parsed = value
    return "" if parsed is None else parsed


def _load_yaml_block(text: str) -> dict:
    try:
        parsed = yaml.safe_load(text)
    except yaml.YAMLError:
        return {}
    return _normalize_yaml_value(parsed) if isinstance(parsed, dict) else {}


def _normalize_yaml_value(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, list):
        return [_normalize_yaml_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize_yaml_value(item) for key, item in value.items()}
    return value


def parse_frontmatter(content: str) -> dict:
    match = FRONTMATTER_RE.match(content)
    if not match:
        return {}
    return _load_yaml_block(match.group(1))


def parse_frontmatter_file(path: Path) -> dict:
    try:
        return parse_frontmatter(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return {}


def serialize_frontmatter(frontmatter: dict) -> str:
    return yaml.dump(
        frontmatter,
        Dumper=FrontmatterDumper,
        allow_unicode=True,
        default_flow_style=False,
        indent=2,
        sort_keys=False,
        width=1000,
    )


def update_frontmatter_field(content: str, field: str, value, append: bool = False):
    match = FRONTMATTER_RE.match(content)
    if not match:
        raise ValueError("No frontmatter found")
    frontmatter = _load_yaml_block(match.group(1))
    if field not in frontmatter and not append:
        raise ValueError(f"Field '{field}' not found in frontmatter")
    old_value = frontmatter.get(field, "")
    if isinstance(old_value, list):
        old_value = list(old_value)
    elif isinstance(old_value, dict):
        old_value = dict(old_value)
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
