"""Tests for shared frontmatter helpers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LIB_DIR = PROJECT_ROOT / ".codex" / "lib"
sys.path.insert(0, str(LIB_DIR))

from vicky.frontmatter import parse_frontmatter, parse_scalar, serialize_frontmatter, update_frontmatter_field


def test_parse_frontmatter_reads_block_lists_and_numbers():
    content = """---
title: "Flash Attention"
tags:
  - attention
  - kernels
priority: 3
relation_derived_from:
  - "[[paper-a]]"
---

## Summary
"""
    parsed = parse_frontmatter(content)
    assert parsed["title"] == "Flash Attention"
    assert parsed["tags"] == ["attention", "kernels"]
    assert parsed["priority"] == 3
    assert parsed["relation_derived_from"] == ["[[paper-a]]"]


def test_parse_frontmatter_normalizes_dates_to_strings():
    content = """---
title: "Flash Attention"
date_added: 2026-04-28
---
"""
    parsed = parse_frontmatter(content)
    assert parsed["date_added"] == "2026-04-28"
    json.dumps(parsed, ensure_ascii=False)


def test_parse_scalar_uses_yaml_rules_with_string_fallback():
    assert parse_scalar("[]") == []
    assert parse_scalar("3") == 3
    assert parse_scalar("working") == "working"
    assert parse_scalar("[[paper-a]]") == "[[paper-a]]"


def test_serializer_keeps_block_lists_and_quotes_wikilinks():
    rendered = serialize_frontmatter(
        {
            "title": "Flash Attention",
            "tags": ["attention", "kernels"],
            "priority": 3,
            "relation_derived_from": ["[[paper-a]]"],
        }
    )
    assert "title: Flash Attention\n" in rendered
    assert "tags:\n  - attention\n  - kernels\n" in rendered
    assert "priority: 3\n" in rendered
    assert 'relation_derived_from:\n  - "[[paper-a]]"\n' in rendered


def test_update_frontmatter_field_appends_without_duplicates():
    content = """---
title: "Flash Attention"
tags:
  - attention
---

## Summary
    """
    updated, old_value, new_value = update_frontmatter_field(content, "tags", "kernels", append=True)
    assert old_value == ["attention"]
    assert new_value == ["attention", "kernels"]
    assert "  - attention\n  - kernels\n" in updated

    updated_again, _, final_value = update_frontmatter_field(updated, "tags", "kernels", append=True)
    assert final_value == ["attention", "kernels"]
    assert updated_again.count("  - kernels\n") == 1
