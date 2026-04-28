# Vicky Runtime Contract

This file is the global contract for Codex inside the Vicky vault.

## Repository Layout

`raw/` is the source layer:

- `raw/papers/` stores prepared paper sources as `.tex` or `.md`
- `raw/web/` stores web clips or exported pages
- `raw/inbox/` stores temporary snippets, prompts, and scratch material

Treat `raw/` as user-owned input. Read from it and write to `wiki/`.

`wiki/` is the maintained knowledge layer:

- `wiki/sources/` stores one page per ingested source
- `wiki/concepts/` stores reusable concepts
- `wiki/theorems/` stores definitions, lemmas, propositions, theorems, examples, algorithms, and formal notes
- `wiki/foundations/` stores stable background knowledge
- `wiki/people/` stores author and researcher pages
- `wiki/ideas/` stores developing thoughts and open directions
- `wiki/topics/` stores higher-level maps across multiple pages
- `wiki/outputs/` stores saved answers, comparisons, and syntheses
- `wiki/bases/` stores Obsidian Bases workbenches
- `wiki/log.md` is append-only

`templates/` stores one Obsidian template per wiki page type. `.obsidian/templates.json` points Obsidian CLI at `templates/`.

`.codex/` contains Codex skills, skill-local scripts, and shared helper code:

- `.codex/skills/*/SKILL.md` holds workflow instructions
- `.codex/skills/*/scripts/` holds executable helpers owned by one skill
- `.codex/skills/*/agents/openai.yaml` holds optional product metadata for the skill package
- `.codex/lib/` holds repo-local shared schema, frontmatter, markdown, slug, and support-file helpers

The shared `.codex/lib/` package is a Vicky repo convention. Skill scripts add it to `sys.path` so duplicated schema logic stays centralized while each skill keeps executable helpers in the standard `scripts/` directory.

## Page And Link Rules

Use lowercase hyphenated slugs with Obsidian wikilinks:

```markdown
[[low-rank-adaptation]]
[[flash-attention]]
[[john-doe]]
```

Use `wiki/sources/{slug}.md` as the citation anchor for raw files. Other wiki pages cite source pages through `key_sources` or relation fields. Source pages keep `source_path` pointing at `raw/`.

During ingest, create the source page automatically. Create or update non-source knowledge pages after the user names the target or approves a proposal.

| Forward action | Expected reverse update |
|---|---|
| `sources/A` links `[[concept-B]]` | `concepts/B` includes `A` in `key_sources` |
| `sources/A` links `[[theorem-C]]` | `theorems/C` includes `A` in `key_sources` |
| `sources/A` links `[[person-D]]` | `people/D` includes `A` in `key_sources` |
| `concepts/K` links `[[topic-T]]` | `topics/T` mentions `K` in body or related section |
| any page links `[[foundation-X]]` | foundation pages can receive one-way links |

## New Page Post-Processing Contract

Treat each new or newly split knowledge page as one finished unit of work. Complete its post-processing before creating the next new page in the same turn.

For every new `wiki/concepts/`, `wiki/theorems/`, or `wiki/ideas/` page:

1. Run the duplicate check before writing:
   - `./.venv/bin/python .codex/skills/ingest/scripts/similar_pages.py wiki concept "<title>"`
   - `./.venv/bin/python .codex/skills/ingest/scripts/similar_pages.py wiki theorem "<title>"`
   - `./.venv/bin/python .codex/skills/ingest/scripts/similar_pages.py wiki idea "<title>"`
2. Resolve the exact target page path from the page type and slug:
   - source: `wiki/sources/{slug}.md`
   - concept: `wiki/concepts/{slug}.md`
   - theorem: `wiki/theorems/{slug}.md`
   - person: `wiki/people/{slug}.md`
   - idea: `wiki/ideas/{slug}.md`
   - topic: `wiki/topics/{slug}.md`
   - foundation: `wiki/foundations/{slug}.md`
   - output: `wiki/outputs/{slug}.md`
3. Create the missing page from its template, then edit that exact markdown file directly for body content.
4. Verify the new-page body edit with `git diff -- <exact-target-path>`.
5. Fill the mandatory semantic follow-up immediately:
   - add `key_sources` when the page comes from a source-backed claim
   - add the necessary `relation_*` properties
   - mirror every stable semantic edge in `## Relations`
   - add the reverse source mention or related-page mention in body text or a related section
6. Append the `wiki/log.md` entry for that page.
7. Run `./.venv/bin/python .codex/skills/check/scripts/lint.py --wiki-dir wiki --json`.

A page is complete when the target page, reverse links, semantic properties, log entry, and lint result are all in place.

## Semantic Relations

Use these six relation fields as the frozen semantic graph schema:

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
relation_extends:
  - "[[concept-b]]"
relation_supports: []
relation_contradicts: []
relation_uses: []
relation_compares_with: []
```

Mirror every stable relation property in a `## Relations` body section with a short evidence sentence:

```markdown
## Relations

- Derived from [[source-paper-a]]: uses its proof setup and relaxes the boundedness assumption.
- Extends [[concept-b]]: generalizes the finite case to the stochastic setting.
```

Properties are the graph index. `## Relations` is the evidence context.

## Bases And Retrieval

`wiki/bases/Semantic Relations.base` is the human-facing semantic graph workbench. It shows all wiki pages with page type, source links, relation fields, relation counts, and a relation-review queue.

`wiki/bases/Current Page Neighbors.base` is the embeddable local neighborhood panel:

```markdown
![[Current Page Neighbors.base#Semantic neighbors]]
```

Machine retrieval starts with Obsidian CLI search and context search, then expands through properties, links, backlinks, outlines, and selected page reads.

## Obsidian CLI Defaults

Run commands from the vault root. Existing notes use `file=<slug>`. Exact destinations use `path=wiki/<type>/<slug>.md`.

| Task | Command |
|---|---|
| Read a note | `obsidian read file=<slug>` |
| Read a property | `obsidian property:read file=<slug> name=<field>` |
| Set a scalar property | `obsidian property:set file=<slug> name=<field> value=<value> type=text` |
| Set a plain list property | `obsidian property:set file=<slug> name=tags value="paper,attention" type=list` |
| Create a page | `obsidian create path="wiki/concepts/<slug>.md" template="Wiki_Concept"` |
| Append to a note | `obsidian append file=<slug> content="<markdown>"` |
| Search text | `obsidian search query="<term>" path=wiki` |
| Search with context | `obsidian search:context query="<term>" path=wiki` |
| Outgoing links | `obsidian links file=<slug>` |
| Backlinks | `obsidian backlinks file=<slug>` |
| Outline | `obsidian outline file=<slug> format=json` |
| Unresolved links | `obsidian unresolved verbose format=json` |
| List wiki files | `obsidian files folder=wiki ext=md` |

Repo-local graph checks use Obsidian CLI plus path filters:

```bash
obsidian orphans | rg '^wiki/(sources|concepts|theorems|foundations|people|ideas|topics|outputs)/' | rg -v '^wiki/outputs/' || true
obsidian deadends | rg '^wiki/(sources|concepts|theorems|foundations|people|ideas|topics|outputs)/' | rg -v '^wiki/outputs/' || true
```

## Log Format

`wiki/log.md` is chronological and append-only:

```markdown
## [YYYY-MM-DD] ingest | added sources/<slug> | updated: concepts/<slug>, topics/<slug>
## [YYYY-MM-DD] ask | <question-slug> | saved: outputs/<slug>
```

Append log entries with:

```bash
obsidian append file=log content="## [YYYY-MM-DD] ..."
```

## Tool Boundaries

Use Obsidian CLI for vault reads, note creation, property edits, search, link checks, log appends, renames, and moves.

Use Python for:

- strict lint rules: `.codex/skills/check/scripts/lint.py`
- frontmatter lookup fallback: `.codex/skills/ask/scripts/frontmatter_find.py`
- deterministic slugging: `.codex/skills/ingest/scripts/slug.py`
- pre-create duplicate checks: `.codex/skills/ingest/scripts/similar_pages.py`
- Semantic Scholar metadata: `.codex/skills/ingest/scripts/fetch_s2.py`
- reset previews and guarded reset execution: `.codex/skills/reset/scripts/reset_wiki.py`
- tests and setup checks

## Legacy Research Wiki Command Map

The old monolithic `.tools/research_wiki.py` command surface is split by skill ownership:

| Old command | Current owner |
|---|---|
| `init` | repository skeleton ships with GitHub checkout; setup and check verify the existing scaffold |
| `slug` | `.codex/skills/ingest/scripts/slug.py` and `.codex/lib/slug_utils.py` |
| `find` | `.codex/skills/ask/scripts/frontmatter_find.py` |
| `find-similar-concept` | `.codex/skills/ingest/scripts/similar_pages.py wiki concept "<title>"` |
| `find-similar-theorem` | `.codex/skills/ingest/scripts/similar_pages.py wiki theorem "<title>"` |
| `find-similar-idea` | `.codex/skills/ingest/scripts/similar_pages.py wiki idea "<title>"` |
| `query orphans` / `query deadends` | `obsidian orphans` / `obsidian deadends` plus Vicky path filters |
| `log` | `obsidian append file=log content="..."` |
| `read-meta` | `obsidian property:read file=<slug> name=<field>` |
| `set-meta` | `obsidian property:set file=<slug> name=<field> value=<value> type=<type>` |
| `stats` | `obsidian files folder=wiki ext=md total` and Bases views |
| `maturity` | `wiki/bases/Semantic Relations.base` review views |
| `transition` | `edit` skill status-property edits plus log entry |
| `checkpoint-*` | `wiki/log.md` plus conversational ingest state; reset can clear legacy `wiki/.checkpoints/*.json` |

## Skills

| Skill | File |
|---|---|
| `setup` | `.codex/skills/setup/SKILL.md` |
| `reset` | `.codex/skills/reset/SKILL.md` |
| `ingest` | `.codex/skills/ingest/SKILL.md` |
| `edit` | `.codex/skills/edit/SKILL.md` |
| `ask` | `.codex/skills/ask/SKILL.md` |
| `check` | `.codex/skills/check/SKILL.md` |
