"""Single source of truth for the Vicky wiki schema."""

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

WIKI_PAGE_FOLDERS = [f"wiki/{name}" for name in INDEXED_DIRS]
KNOWLEDGE_PAGE_FOLDERS = [folder for folder in WIKI_PAGE_FOLDERS if folder != "wiki/sources"]
FORMAL_PAGE_FOLDERS = [f"wiki/{name}" for name in ("concepts", "theorems", "foundations")]
SYNTHESIS_PAGE_FOLDERS = [f"wiki/{name}" for name in ("ideas", "topics", "outputs")]

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
RELATION_DISPLAY_NAMES = {
    "relation_derived_from": "Derived from",
    "relation_extends": "Extends",
    "relation_supports": "Supports",
    "relation_contradicts": "Contradicts",
    "relation_uses": "Uses",
    "relation_compares_with": "Compares with",
}

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
    "foundations": {"aliases": "[]", "status": "canonical"},
}

PAGE_TYPE_FORMULA = 'file.folder.replace("wiki/", "")'
DISPLAY_TITLE_FORMULA = "if(title, title, if(name, name, file.basename))"


def _folder_lines(folders: list[str], indent: str = "        ") -> str:
    return "\n".join(f"{indent}- 'file.inFolder(\"{folder}\")'" for folder in folders)


def _relation_order_lines(indent: str = "      ", fields: list[str] | None = None) -> str:
    active_fields = fields or RELATION_FIELDS
    return "\n".join(f"{indent}- {field}" for field in active_fields)


def _relation_property_lines(indent: str = "  ") -> str:
    lines = []
    for field in RELATION_FIELDS:
        label = RELATION_DISPLAY_NAMES[field]
        lines.append(f"{indent}{field}:")
        lines.append(f"{indent}  displayName: {label}")
    return "\n".join(lines)


def _relation_count_formula() -> str:
    terms = []
    for field in RELATION_FIELDS:
        terms.append(f'if(file.hasProperty("{field}"), list({field}).length, 0)')
    return " + ".join(terms)


def _relation_alias(field: str) -> str:
    return field.removeprefix("relation_")


def _knowledge_folder_predicate() -> str:
    return " || ".join(f'file.inFolder("{folder}")' for folder in KNOWLEDGE_PAGE_FOLDERS)


def _current_edge_formula_lines() -> str:
    lines = []
    for field in RELATION_FIELDS:
        alias = _relation_alias(field)
        lines.append(
            f'  {alias}_current: \'if(file.hasProperty("{field}"), list({field}).contains(this.file), false)\''
        )
    return "\n".join(lines)


def _current_edge_predicate() -> str:
    return " || ".join(f"formula.{_relation_alias(field)}_current" for field in RELATION_FIELDS)


SEMANTIC_RELATIONS_BASE = f"""filters:
  and:
    - 'file.ext == "md"'
    - or:
{_folder_lines(WIKI_PAGE_FOLDERS)}
formulas:
  page_type: '{PAGE_TYPE_FORMULA}'
  display_title: '{DISPLAY_TITLE_FORMULA}'
  relation_count: '{_relation_count_formula()}'
  source_count: 'if(file.hasProperty("key_sources"), list(key_sources).length, 0)'
  needs_relation_review: 'formula.relation_count == 0 && ({_knowledge_folder_predicate()})'
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
{_relation_property_lines()}
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
{_relation_order_lines()}
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
{_folder_lines(FORMAL_PAGE_FOLDERS)}
    groupBy:
      property: formula.page_type
      direction: ASC
    order:
      - formula.display_title
      - theorem_kind
      - maturity
      - status
      - key_sources
{_relation_order_lines(fields=["relation_derived_from", "relation_extends", "relation_supports", "relation_uses", "relation_compares_with"])}
      - formula.relation_count
  - type: table
    name: Ideas and outputs
    filters:
      or:
{_folder_lines(SYNTHESIS_PAGE_FOLDERS)}
    groupBy:
      property: formula.page_type
      direction: ASC
    order:
      - formula.display_title
      - status
      - priority
      - tags
{_relation_order_lines(fields=["relation_derived_from", "relation_supports", "relation_compares_with"])}
      - formula.relation_count
"""

CURRENT_PAGE_NEIGHBORS_BASE = f"""filters:
  and:
    - 'file.ext == "md"'
    - 'file.path != this.file.path'
    - or:
{_folder_lines(WIKI_PAGE_FOLDERS)}
formulas:
  page_type: '{PAGE_TYPE_FORMULA}'
  display_title: '{DISPLAY_TITLE_FORMULA}'
  mentions_current: 'file.hasLink(this.file)'
{_current_edge_formula_lines()}
  semantic_edge_to_current: '{_current_edge_predicate()}'
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
{_relation_property_lines()}
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
{_relation_order_lines()}
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
{_relation_order_lines()}
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
