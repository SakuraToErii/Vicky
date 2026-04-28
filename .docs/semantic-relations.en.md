# Semantic Relations Contract

This page is the canonical contract for semantic relation fields, relation evidence, Bases views, and search-first retrieval.

## Frozen relation fields

Use these six `relation_*` properties for machine-searchable semantic edges:

- `relation_derived_from`
- `relation_extends`
- `relation_supports`
- `relation_contradicts`
- `relation_uses`
- `relation_compares_with`

Keep this set frozen. Add a new relation field only after proving these six fields cannot express the relation.

## Storage format

Store relation targets as Obsidian wikilink strings in frontmatter:

```yaml
relation_derived_from:
  - "[[source-paper-a]]"
relation_extends:
  - "[[concept-b]]"
```

Mirror each stable relation in the page body:

```markdown
## Relations

- Derived from [[source-paper-a]]: uses its proof setup and relaxes the boundedness assumption.
- Extends [[concept-b]]: generalizes the finite case to the stochastic setting.
```

Properties are the graph index. `## Relations` is the evidence layer.

## Bases workbenches

`wiki/bases/Semantic Relations.base` is the whole-vault relation table and review surface.

`wiki/bases/Current Page Neighbors.base` is the embeddable local neighborhood panel:

```markdown
![[Current Page Neighbors.base#Semantic neighbors]]
```

## Retrieval contract

Machine retrieval starts from Obsidian CLI search:

```bash
obsidian search query="<term>" path=wiki
obsidian search:context query="<term>" path=wiki
```

Then expand candidate pages through relation properties, `property:read`, `links`, `backlinks`, and `outline`.

Use Bases for human review, filtering, grouping, and neighborhood browsing.
