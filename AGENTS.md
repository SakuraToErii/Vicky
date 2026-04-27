# Vicky — Runtime Schema

This file defines the working contract for the Vicky vault in Codex.

## Repository layout

### `raw/` is the source layer

- `raw/papers/` stores user-owned paper sources that are already prepared as `.tex` or `.md`
- `raw/web/` stores user-owned web clips or exported pages
- `raw/inbox/` stores temporary snippets, prompts, and scratch material

Treat `raw/` as read-only input. The LLM reads from it and writes nowhere under it.

### `wiki/` is the maintained knowledge layer

- `wiki/sources/` stores one page per ingested source
- `wiki/concepts/` stores reusable concepts
- `wiki/theorems/` stores definitions, theorems, propositions, examples, and related formal objects
- `wiki/foundations/` stores stable background knowledge
- `wiki/people/` stores author and researcher pages
- `wiki/ideas/` stores developing thoughts and open directions
- `wiki/topics/` stores higher-level maps across multiple pages
- `wiki/outputs/` stores saved answers, comparisons, and syntheses
- `wiki/bases/` stores Obsidian Bases workbenches for relation review
- `wiki/log.md` is append-only

Open `.docs/runtime-directory-structure.en.md` for the full directory map.
Open `templates/` for the Obsidian page templates.
Open `.codex/skills/init/references/wiki-bootstrap-templates.md` for the template-name map and support-file commands.
Open `.codex/skills/ingest/references/wiki-update-templates.md` for ingest-time template selection and relation rules.
Open `.docs/obsidian-cli-workflows.en.md` for the default vault command set.
Open `.docs/runtime-page-templates.en.md` and `.docs/runtime-support-files.en.md` for concise summaries.
Open `.docs/obsidian-bases-semantic-graph.en.md` for the Bases relation workflow.

## Page types

`sources`, `concepts`, `topics`, `people`, `ideas`, `theorems`, `foundations`.

## Link syntax

Use Obsidian wikilinks everywhere:

```markdown
[[low-rank-adaptation]]
[[flash-attention]]
[[john-doe]]
```

Use lowercase hyphenated slugs with no spaces.

## Cross-reference rules

When writing a forward link, also maintain the relevant source backlinks.
Use `wiki/sources/{slug}.md` as the citation anchor for raw files. Other wiki pages should cite source pages through `key_sources` or relation fields, while source pages keep `source_path` pointing at `raw/`.

During ingest, create the source page automatically. Create or update non-source knowledge pages after the user names the target or approves a proposal.

| Forward action | Expected reverse update |
|---|---|
| `sources/A` links `[[concept-B]]` | `concepts/B` includes `A` in `key_sources` |
| `sources/A` links `[[theorem-C]]` | `theorems/C` includes `A` in `key_sources` |
| `sources/A` links `[[person-D]]` | `people/D` includes `A` in `key_sources` |
| `concepts/K` links `[[topic-T]]` | `topics/T` should mention `K` in body or related section |
| any page links `[[foundation-X]]` | no reverse link is required |

## Semantic relations

Use relation properties for machine-searchable semantic edges:

- `relation_derived_from`
- `relation_extends`
- `relation_supports`
- `relation_contradicts`
- `relation_uses`
- `relation_compares_with`

Use Obsidian wikilink strings as values:

```yaml
relation_derived_from:
  - "[[source-paper-a]]"
```

The six relation fields are a frozen schema. Add a new `relation_*` field only after proving the existing six fields cannot express the relation.

Mirror every stable relation property in a `## Relations` body section with a short explanation. Properties are the graph index; `## Relations` is the evidence context.

## Bases, index, and log

`wiki/bases/Semantic Relations.base` is the primary human-facing workbench for semantic relations. It shows all wiki pages with page type, source links, relation fields, relation counts, and a relation-review queue.

`wiki/bases/Current Page Neighbors.base` is an embeddable neighborhood view. Embed it with `![[Current Page Neighbors.base#Semantic neighbors]]` when a page needs a local relation panel.

Use Obsidian CLI search, context search, properties, links, backlinks, and outlines as the machine retrieval path.

`wiki/log.md` is chronological. Standard format:

```markdown
## [YYYY-MM-DD] ingest | added sources/<slug> | updated: concepts/<slug>, topics/<slug>
```

Append log entries with `obsidian append file=log content="## [YYYY-MM-DD] ..."` from the vault root.

## Constraints

- `raw/` is user-owned input and read-only.
- `wiki/` is the maintained layer.
- `sources/` is the source page layer.
- The vault relies on plain Markdown and Obsidian links, not on generated graph state.
- `Semantic Scholar` metadata is optional enrichment, not a hard dependency.
- `foundations/` are stable background notes. They can receive links from other pages.
- `outputs/` can hold query results and saved syntheses. They use a lighter schema focused on saved answers, citations, and stable relation links.
- Obsidian CLI is the default interface for vault reads, note creation, property edits, search, link checks, log appends, renames, and moves.
- Python tools are reserved for strict lint rules, Semantic Scholar metadata, setup, tests, and reset dry-runs.

## Template references

- `templates/` stores one Obsidian template per wiki page type.
- `.obsidian/templates.json` points Obsidian CLI at `templates/`.
- `.codex/skills/init/references/wiki-bootstrap-templates.md` maps wiki paths to template names and support-file commands.
- `.codex/skills/ingest/references/wiki-update-templates.md` maps ingest page types to template names and relation rules.

## Skills

| Skill | File |
|---|---|
| `setup` | `.codex/skills/setup/SKILL.md` |
| `reset` | `.codex/skills/reset/SKILL.md` |
| `init` | `.codex/skills/init/SKILL.md` |
| `ingest` | `.codex/skills/ingest/SKILL.md` |
| `edit` | `.codex/skills/edit/SKILL.md` |
| `ask` | `.codex/skills/ask/SKILL.md` |
| `check` | `.codex/skills/check/SKILL.md` |
