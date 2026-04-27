# Obsidian Bases Semantic Graph Workflow

Bases give Vicky a visible workbench for the semantic graph. Each Markdown note is a row. Frontmatter properties are columns. The `relation_*` fields are the graph edges.

## What Bases Replace

| Old surface | Bases surface | Result |
|---|---|---|
| Manual directory scanning | `Semantic Relations.base#Semantic graph` | All wiki pages appear in one grouped table |
| Manual checks for empty relation fields | `Semantic Relations.base#Relation review` | Relation gaps are visible after ingest |
| Opening many pages to compare relations | Relation columns in table views | Cross-page links can be reviewed in one place |
| Per-page backlink hunting | `Current Page Neighbors.base#Semantic neighbors` | A local neighborhood panel can be embedded in any note |

## What Stays Canonical

The canonical graph data stays in Markdown frontmatter:

```yaml
relation_derived_from:
  - "[[source-paper-a]]"
relation_extends:
  - "[[concept-b]]"
relation_supports:
  - "[[theorem-c]]"
```

The evidence stays in the page body:

```markdown
## Relations

- Derived from [[source-paper-a]]: uses its proof setup and relaxes the boundedness assumption.
```

`.tools/lint.py` checks that relation properties and `## Relations` explanations stay aligned.

The six `relation_*` fields are a frozen schema. Add a new relation field only after proving the existing six fields cannot express the relation.

## Default Bases

`wiki/bases/Semantic Relations.base` has five views:

- `Semantic graph`: all wiki pages grouped by page type
- `Relation review`: pages with zero semantic relation fields
- `Sources`: source metadata, authors, year, raw path, and tags
- `Concepts and theorems`: concept, theorem, and foundation relations
- `Ideas and outputs`: synthesis pages, ideas, topics, and saved answers

`wiki/bases/Current Page Neighbors.base` has three views:

- `Semantic neighbors`: pages that point at the current note through relation properties or wikilinks
- `Relation-only`: pages that point at the current note through relation properties
- `Mentions`: pages that mention the current note through wikilinks

Embed the neighborhood view in a note with:

```markdown
![[Current Page Neighbors.base#Semantic neighbors]]
```

## Ingest Workflow

1. Create or update the source page.
2. Add relation properties on approved knowledge pages.
3. Add matching `## Relations` bullets with evidence.
4. Open `Semantic Relations.base#Relation review`.
5. Fill missing high-value semantic edges.
6. Run `.tools/lint.py` for strict consistency checks.

Bases make relation review visual and fast. The Markdown properties remain the source of truth for AI retrieval, CLI search, and lint checks.
