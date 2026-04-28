"""Tests for Obsidian template properties and property type registration."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LIB_DIR = PROJECT_ROOT / ".codex" / "lib"
sys.path.insert(0, str(LIB_DIR))

from vicky.frontmatter import serialize_frontmatter
from vicky.schema import RELATION_FIELDS

TEMPLATE_DIR = PROJECT_ROOT / "templates"
TYPES_PATH = PROJECT_ROOT / ".obsidian" / "types.json"
DEPRECATED_TEMPLATE_FIELDS = {"date_updated", "source_ids"}
LIST_FIELDS = {"aliases", "authors", "key_sources", "tags", *RELATION_FIELDS}
TEXT_FIELDS = {"title", "name", "slug", "source_kind", "source_path", "domain", "status", "maturity", "theorem_kind", "affiliation"}


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    assert match, f"{path.name} needs YAML frontmatter"
    parsed = yaml.safe_load(match.group(1))
    assert isinstance(parsed, dict)
    return parsed


def test_templates_use_obsidian_friendly_property_values():
    for path in sorted(TEMPLATE_DIR.glob("Wiki_*.md")):
        frontmatter = _frontmatter(path)
        assert not (set(frontmatter) & DEPRECATED_TEMPLATE_FIELDS)
        assert all(value is not None for value in frontmatter.values())
        for field in LIST_FIELDS & set(frontmatter):
            assert isinstance(frontmatter[field], list), f"{path.name}:{field} should be a YAML list"
        for field in TEXT_FIELDS & set(frontmatter):
            assert isinstance(frontmatter[field], str), f"{path.name}:{field} should be text"
        if "priority" in frontmatter:
            assert isinstance(frontmatter["priority"], int)
        if "date_added" in frontmatter:
            assert frontmatter["date_added"] == "{{date:YYYY-MM-DD}}"


def test_source_template_keeps_year_optional():
    frontmatter = _frontmatter(TEMPLATE_DIR / "Wiki_Source.md")
    assert "year" not in frontmatter
    assert "source_ids" not in frontmatter


def test_foundation_template_supports_alias_matching():
    frontmatter = _frontmatter(TEMPLATE_DIR / "Wiki_Foundation.md")
    assert frontmatter["aliases"] == []


def test_obsidian_property_types_match_template_schema():
    types = json.loads(TYPES_PATH.read_text(encoding="utf-8"))["types"]
    assert "date_updated" not in types
    assert "source_ids" not in types
    assert types["aliases"] == "aliases"
    assert types["tags"] == "tags"
    assert types["priority"] == "number"
    assert types["year"] == "number"
    assert types["date_added"] == "date"
    for field in RELATION_FIELDS:
        assert types[field] == "multitext"


def test_frontmatter_serializer_uses_block_lists_and_number_literals():
    rendered = serialize_frontmatter(
        {
            "tags": ["ml", "optimization"],
            "relation_derived_from": ["[[paper-a]]"],
            "priority": 3,
        }
    )
    assert "tags:\n  - ml\n  - optimization\n" in rendered
    assert 'relation_derived_from:\n  - "[[paper-a]]"\n' in rendered
    assert "priority: 3\n" in rendered
