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

from frontmatter import serialize_frontmatter
from schema import RELATION_FIELDS

TEMPLATE_DIR = PROJECT_ROOT / "templates"
TYPES_PATH = PROJECT_ROOT / ".obsidian" / "types.json"
DEPRECATED_TEMPLATE_FIELDS = {"date_updated", "source_ids"}
LIST_FIELDS = {"aliases", "authors", "key_sources", "tags", *RELATION_FIELDS}
TEXT_FIELDS = {"title", "slug", "source_kind", "source_path", "domain", "status", "maturity", "theorem_kind", "affiliation"}
EXPECTED_TEMPLATE_FIELD_ORDER = {
    "Wiki_Concept.md": ["title", "slug", "tags", "aliases", "relation_derived_from", "relation_extends", "relation_uses", "relation_compares_with"],
    "Wiki_Foundation.md": ["title", "slug", "tags", "aliases", "relation_extends", "relation_uses", "relation_compares_with"],
    "Wiki_Idea.md": ["title", "slug", "tags", "priority", *RELATION_FIELDS],
    "Wiki_Output.md": ["title", "slug", "tags", "relation_derived_from", "relation_uses", "relation_compares_with"],
    "Wiki_Person.md": ["title", "slug", "tags", "affiliation", "key_sources"],
    "Wiki_Source.md": ["title", "slug", "tags", "authors", "source_kind", "source_path", "relation_extends", "relation_uses", "relation_compares_with", "relation_contradicts", "date_added"],
    "Wiki_Theorem.md": ["title", "slug", "tags", "theorem_kind", *RELATION_FIELDS],
    "Wiki_Topic.md": ["title", "slug", "tags", *RELATION_FIELDS],
}
EXPECTED_TEMPLATE_HEADINGS = {
    "Wiki_Concept.md": ["## Relations"],
    "Wiki_Foundation.md": ["## Relations"],
    "Wiki_Idea.md": ["## Relations"],
    "Wiki_Output.md": ["## Answer", "## Relations"],
    "Wiki_Person.md": ["## Notes"],
    "Wiki_Source.md": ["## Relations", "- Raw source:"],
    "Wiki_Theorem.md": ["## Statement", "## Relations"],
    "Wiki_Topic.md": ["## Relations"],
}


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    assert match, f"{path.name} needs YAML frontmatter"
    parsed = yaml.safe_load(match.group(1))
    assert isinstance(parsed, dict)
    return parsed


def _body_headings(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n.*?\n---\n\n?(.*)$", text, re.DOTALL)
    assert match, f"{path.name} needs a body after frontmatter"
    return [line.strip() for line in match.group(1).splitlines() if line.strip()]


def test_templates_use_obsidian_friendly_property_values():
    for path in sorted(TEMPLATE_DIR.glob("Wiki_*.md")):
        frontmatter = _frontmatter(path)
        assert not (set(frontmatter) & DEPRECATED_TEMPLATE_FIELDS)
        assert all(value is not None for value in frontmatter.values())
        assert list(frontmatter.keys()) == EXPECTED_TEMPLATE_FIELD_ORDER[path.name]
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


def test_templates_use_minimal_stable_body_anchors():
    for path in sorted(TEMPLATE_DIR.glob("Wiki_*.md")):
        assert _body_headings(path) == EXPECTED_TEMPLATE_HEADINGS[path.name]


def test_foundation_template_supports_alias_matching():
    frontmatter = _frontmatter(TEMPLATE_DIR / "Wiki_Foundation.md")
    assert frontmatter["aliases"] == []


def test_person_template_uses_title_field():
    frontmatter = _frontmatter(TEMPLATE_DIR / "Wiki_Person.md")
    assert "title" in frontmatter
    assert "name" not in frontmatter


def test_obsidian_property_types_match_template_schema():
    types = json.loads(TYPES_PATH.read_text(encoding="utf-8"))["types"]
    assert "date_updated" not in types
    assert "source_ids" not in types
    assert types["aliases"] == "aliases"
    assert types["tags"] == "multitext"
    assert types["priority"] == "number"
    assert types["year"] == "number"
    assert types["date_added"] == "date"
    assert "name" not in types
    for field in RELATION_FIELDS:
        assert types[field] == "multitext"
    assert "relation_derived_from" not in _frontmatter(TEMPLATE_DIR / "Wiki_Person.md")


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
