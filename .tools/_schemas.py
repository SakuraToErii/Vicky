"""Single source of truth for the Vicky wiki schema.

The repository is now an Obsidian-first LLM wiki for shared human/AI note
maintenance. Raw sources stay under ``raw/``. Structured knowledge lives under
``wiki/``.
"""

from __future__ import annotations

ENTITY_DIRS = [
    "sources",
    "concepts",
    "topics",
    "people",
    "ideas",
    "theorems",
    "foundations",
]

INDEXED_DIRS = ENTITY_DIRS + ["outputs"]

RAW_DIRS = ["papers", "web", "inbox"]

BASES_DIR = "bases"
SUPPORT_DIRS = [BASES_DIR]

# Frozen semantic relation schema.
RELATION_SCHEMA_STATUS = "frozen"
RELATION_SCHEMA_CHANGE_POLICY = "New relation fields require proof that the six existing fields cannot express the relation."
RELATION_FIELDS = [
    "relation_derived_from",
    "relation_extends",
    "relation_supports",
    "relation_contradicts",
    "relation_uses",
    "relation_compares_with",
]

REQUIRED_FIELDS = {
    "sources": ["title", "slug", "source_kind", "source_path"],
    "concepts": ["title", "slug", "tags", "maturity", "key_sources"],
    "topics": ["title", "slug", "tags"],
    "people": ["name", "slug", "tags"],
    "ideas": ["title", "slug", "status", "tags", "priority"],
    "theorems": ["title", "slug", "theorem_kind", "status", "key_sources"],
    "foundations": ["title", "slug", "domain", "status"],
}

VALID_VALUES = {
    "sources.source_kind": {"paper", "blog", "chapter", "book", "web", "note", "other"},
    "concepts.maturity": {"seed", "working", "stable", "archived"},
    "ideas.status": {"fleeting", "working", "stable", "archived"},
    "ideas.priority": {"1", "2", "3", "4", "5"},
    "theorems.theorem_kind": {
        "definition",
        "lemma",
        "proposition",
        "theorem",
        "corollary",
        "example",
        "counterexample",
        "algorithm",
        "note",
    },
    "theorems.status": {"draft", "stable", "historical"},
    "foundations.status": {"canonical", "historical"},
}

FIELD_DEFAULTS = {
    "sources": {"source_kind": "other", "tags": "[]"},
    "concepts": {"tags": "[]", "maturity": "seed", "key_sources": "[]"},
    "topics": {"tags": "[]"},
    "people": {"tags": "[]"},
    "ideas": {"status": "fleeting", "tags": "[]", "priority": "3"},
    "theorems": {"theorem_kind": "note", "status": "draft", "key_sources": "[]", "tags": "[]"},
    "foundations": {"status": "canonical"},
}

SEMANTIC_RELATIONS_BASE = """filters:
  and:
    - 'file.ext == "md"'
    - or:
        - 'file.inFolder("wiki/sources")'
        - 'file.inFolder("wiki/concepts")'
        - 'file.inFolder("wiki/theorems")'
        - 'file.inFolder("wiki/foundations")'
        - 'file.inFolder("wiki/people")'
        - 'file.inFolder("wiki/ideas")'
        - 'file.inFolder("wiki/topics")'
        - 'file.inFolder("wiki/outputs")'
formulas:
  page_type: 'file.folder.replace("wiki/", "")'
  display_title: 'if(title, title, if(name, name, file.basename))'
  relation_count: 'if(file.hasProperty("relation_derived_from"), list(relation_derived_from).length, 0) + if(file.hasProperty("relation_extends"), list(relation_extends).length, 0) + if(file.hasProperty("relation_supports"), list(relation_supports).length, 0) + if(file.hasProperty("relation_contradicts"), list(relation_contradicts).length, 0) + if(file.hasProperty("relation_uses"), list(relation_uses).length, 0) + if(file.hasProperty("relation_compares_with"), list(relation_compares_with).length, 0)'
  source_count: 'if(file.hasProperty("key_sources"), list(key_sources).length, 0)'
  needs_relation_review: 'formula.relation_count == 0 && (file.inFolder("wiki/concepts") || file.inFolder("wiki/theorems") || file.inFolder("wiki/foundations") || file.inFolder("wiki/people") || file.inFolder("wiki/ideas") || file.inFolder("wiki/topics") || file.inFolder("wiki/outputs"))'
properties:
  formula.display_title:
    displayName: Title
  formula.page_type:
    displayName: Page type
  formula.relation_count:
    displayName: Relation count
  formula.source_count:
    displayName: Source count
  formula.needs_relation_review:
    displayName: Needs relation review
  key_sources:
    displayName: Key sources
  relation_derived_from:
    displayName: Derived from
  relation_extends:
    displayName: Extends
  relation_supports:
    displayName: Supports
  relation_contradicts:
    displayName: Contradicts
  relation_uses:
    displayName: Uses
  relation_compares_with:
    displayName: Compares with
views:
  - type: table
    name: Semantic graph
    groupBy:
      property: formula.page_type
      direction: ASC
    order:
      - formula.display_title
      - file.path
      - formula.page_type
      - tags
      - maturity
      - status
      - theorem_kind
      - key_sources
      - relation_derived_from
      - relation_extends
      - relation_supports
      - relation_contradicts
      - relation_uses
      - relation_compares_with
      - formula.relation_count
    summaries:
      formula.relation_count: Sum
  - type: table
    name: Relation review
    filters:
      and:
        - 'formula.needs_relation_review == true'
    groupBy:
      property: formula.page_type
      direction: ASC
    order:
      - formula.display_title
      - file.path
      - formula.page_type
      - tags
      - maturity
      - status
      - key_sources
      - formula.source_count
      - formula.relation_count
  - type: table
    name: Sources
    filters:
      and:
        - 'file.inFolder("wiki/sources")'
    order:
      - formula.display_title
      - source_kind
      - authors
      - year
      - source_path
      - tags
  - type: table
    name: Concepts and theorems
    filters:
      or:
        - 'file.inFolder("wiki/concepts")'
        - 'file.inFolder("wiki/theorems")'
        - 'file.inFolder("wiki/foundations")'
    groupBy:
      property: formula.page_type
      direction: ASC
    order:
      - formula.display_title
      - theorem_kind
      - maturity
      - status
      - key_sources
      - relation_derived_from
      - relation_extends
      - relation_supports
      - relation_uses
      - relation_compares_with
      - formula.relation_count
  - type: table
    name: Ideas and outputs
    filters:
      or:
        - 'file.inFolder("wiki/ideas")'
        - 'file.inFolder("wiki/topics")'
        - 'file.inFolder("wiki/outputs")'
    groupBy:
      property: formula.page_type
      direction: ASC
    order:
      - formula.display_title
      - status
      - priority
      - tags
      - relation_derived_from
      - relation_supports
      - relation_compares_with
      - formula.relation_count
"""

CURRENT_PAGE_NEIGHBORS_BASE = """filters:
  and:
    - 'file.ext == "md"'
    - 'file.path != this.file.path'
    - or:
        - 'file.inFolder("wiki/sources")'
        - 'file.inFolder("wiki/concepts")'
        - 'file.inFolder("wiki/theorems")'
        - 'file.inFolder("wiki/foundations")'
        - 'file.inFolder("wiki/people")'
        - 'file.inFolder("wiki/ideas")'
        - 'file.inFolder("wiki/topics")'
        - 'file.inFolder("wiki/outputs")'
formulas:
  page_type: 'file.folder.replace("wiki/", "")'
  display_title: 'if(title, title, if(name, name, file.basename))'
  mentions_current: 'file.hasLink(this.file)'
  derived_from_current: 'if(file.hasProperty("relation_derived_from"), list(relation_derived_from).contains(this.file), false)'
  extends_current: 'if(file.hasProperty("relation_extends"), list(relation_extends).contains(this.file), false)'
  supports_current: 'if(file.hasProperty("relation_supports"), list(relation_supports).contains(this.file), false)'
  contradicts_current: 'if(file.hasProperty("relation_contradicts"), list(relation_contradicts).contains(this.file), false)'
  uses_current: 'if(file.hasProperty("relation_uses"), list(relation_uses).contains(this.file), false)'
  compares_with_current: 'if(file.hasProperty("relation_compares_with"), list(relation_compares_with).contains(this.file), false)'
  semantic_edge_to_current: 'formula.derived_from_current || formula.extends_current || formula.supports_current || formula.contradicts_current || formula.uses_current || formula.compares_with_current'
  incoming_reason: 'if(formula.semantic_edge_to_current, "semantic property", if(formula.mentions_current, "wikilink", ""))'
properties:
  formula.display_title:
    displayName: Title
  formula.page_type:
    displayName: Page type
  formula.incoming_reason:
    displayName: Why shown
  formula.semantic_edge_to_current:
    displayName: Semantic edge
  formula.mentions_current:
    displayName: Mentions current page
  relation_derived_from:
    displayName: Derived from
  relation_extends:
    displayName: Extends
  relation_supports:
    displayName: Supports
  relation_contradicts:
    displayName: Contradicts
  relation_uses:
    displayName: Uses
  relation_compares_with:
    displayName: Compares with
views:
  - type: table
    name: Semantic neighbors
    filters:
      or:
        - 'formula.semantic_edge_to_current == true'
        - 'formula.mentions_current == true'
    groupBy:
      property: formula.incoming_reason
      direction: DESC
    order:
      - formula.display_title
      - file.path
      - formula.page_type
      - formula.incoming_reason
      - relation_derived_from
      - relation_extends
      - relation_supports
      - relation_contradicts
      - relation_uses
      - relation_compares_with
  - type: table
    name: Relation-only
    filters:
      and:
        - 'formula.semantic_edge_to_current == true'
    groupBy:
      property: formula.page_type
      direction: ASC
    order:
      - formula.display_title
      - file.path
      - relation_derived_from
      - relation_extends
      - relation_supports
      - relation_contradicts
      - relation_uses
      - relation_compares_with
  - type: table
    name: Mentions
    filters:
      and:
        - 'formula.mentions_current == true'
    groupBy:
      property: formula.page_type
      direction: ASC
    order:
      - formula.display_title
      - file.path
      - formula.incoming_reason
      - tags
"""

BASE_FILE_TEMPLATES = {
    "bases/Semantic Relations.base": SEMANTIC_RELATIONS_BASE,
    "bases/Current Page Neighbors.base": CURRENT_PAGE_NEIGHBORS_BASE,
}
