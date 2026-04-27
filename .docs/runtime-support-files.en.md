# Runtime Support Files

Canonical page templates live in `templates/`. Support-file commands live in:

- `.codex/skills/init/references/wiki-bootstrap-templates.md`
- `.codex/skills/ingest/references/wiki-update-templates.md`

This page keeps the behavior summary short.

## `bases/*.base`

`wiki/bases/Semantic Relations.base` is the main semantic graph workbench. It collects Markdown pages from `wiki/sources`, `wiki/concepts`, `wiki/theorems`, `wiki/foundations`, `wiki/people`, `wiki/ideas`, `wiki/topics`, and `wiki/outputs`.

Its views cover:

- `Semantic graph`: all wiki pages grouped by page type
- `Relation review`: pages whose relation fields are empty
- `Sources`: source metadata and raw file paths
- `Concepts and theorems`: formal knowledge pages with relation columns
- `Ideas and outputs`: synthesis pages and developing directions

`wiki/bases/Current Page Neighbors.base` is designed for embedding in a note:

```markdown
![[Current Page Neighbors.base#Semantic neighbors]]
```

When embedded, it shows pages that point at the current note through `relation_*` properties or normal wikilinks.

The six `relation_*` fields are a frozen schema. Add a new relation field only after proving the existing six fields cannot express the relation.

## Search-first retrieval

Machine retrieval starts from Obsidian CLI search and expands through metadata and links:

```bash
obsidian files folder=wiki ext=md
obsidian search query="<term>" path=wiki
obsidian search:context query="<term>" path=wiki
obsidian property:read file=<slug> name=<field>
obsidian links file=<slug>
obsidian backlinks file=<slug>
obsidian outline file=<slug> format=json
```

Use `wiki/bases/Semantic Relations.base` as the human-facing relation workbench and Obsidian CLI as the machine retrieval path.

## `log.md`

`log.md` is append-only and chronological:

```markdown
## [2026-04-27] ingest | added sources/attention-is-all-you-need | updated: concepts/self-attention
## [2026-04-27] ask | attention vs recurrence | saved: outputs/attention-vs-recurrence
## [2026-04-27] check | report: 1 🔴, 2 🟡, 3 🔵
```

The agent should append via:

```bash
obsidian append file=log content="## [YYYY-MM-DD] ingest | added sources/<slug> | updated: <paths>"
```
