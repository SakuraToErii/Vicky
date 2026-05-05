# Vicky Runtime Contract

This file is the always-loaded contract for Codex inside the Vicky vault. Keep it short. Detailed procedures live in skill files.

## Core Model

Vicky is a lightweight Obsidian-native LLM wiki.

- `raw/` is user-owned input: papers, web clips, inbox notes, and scratch material.
- `wiki/` is the maintained knowledge layer: sources, concepts, theorems, foundations, people, ideas, topics, outputs, and Bases.
- `templates/` stores Obsidian templates for wiki page creation.
- `.codex/skills/` stores formal workflows.
- `.codex/lib/` stores shared repo-local schema and helper code.

Read from `raw/` when answering questions about source material.  Explain the content to user using the Feynman technique, considering yourself as the author.

Write to `wiki/` only when the user asks for a skill workflow or explicitly asks to create, edit, save, reset, or check vault content.

## Default Conversation Mode

The user's normal workflow is reading newly added `raw/` material, asking questions, and deciding later what belongs in long-term notes.

In ordinary chat:

- answer questions directly from the requested raw file, selected wiki pages, or the conversation context
- explain uncertainty and cite local pages or file paths when useful
- create and edit long-term notes through explicit user targets
- leave `wiki/`, `raw/`, templates, skills, and config unchanged

Formal vault writes happen through skills:

| Intent | Skill |
|---|---|
| Prepare the local environment | `setup` |
| Ingest a prepared source into notes | `ingest` |
| Ask against the maintained wiki | `ask` |
| Edit existing vault content | `edit` |
| Run structural checks | `check` |
| Reset vault state | `reset` |

## Page Rules

Use lowercase hyphenated slugs and Obsidian wikilinks:

```markdown
[[low-rank-adaptation]]
[[flash-attention]]
[[john-doe]]
```

Use `wiki/sources/{slug}.md` as the citation anchor for raw files. Source pages keep `source_path` pointing at `raw/`.

Page homes:

- source: `wiki/sources/{slug}.md`
- concept: `wiki/concepts/{slug}.md`
- theorem: `wiki/theorems/{slug}.md`
- person: `wiki/people/{slug}.md`
- idea: `wiki/ideas/{slug}.md`
- topic: `wiki/topics/{slug}.md`
- foundation: `wiki/foundations/{slug}.md`
- output: `wiki/outputs/{slug}.md`

## New Page Post-Processing Contract

For every new or newly split `wiki/concepts/`, `wiki/theorems/`, or `wiki/ideas/` page, finish one page completely before starting another.

Minimum completion path:

1. Run the duplicate check first:
   - `./.venv/bin/python .codex/skills/ingest/scripts/similar_pages.py wiki concept "<title>"`
   - `./.venv/bin/python .codex/skills/ingest/scripts/similar_pages.py wiki theorem "<title>"`
   - `./.venv/bin/python .codex/skills/ingest/scripts/similar_pages.py wiki idea "<title>"`
2. Create from the matching template and edit the exact target markdown file.
3. Fill semantic follow-up:
   - for source-backed concepts, theorems, ideas, topics, and outputs, add the source page to `relation_derived_from`
   - for source-backed people, maintain `key_sources`
   - add the necessary `relation_*` properties
   - mirror every stable semantic edge in `## Relations`
   - add the reverse source mention or related-page mention in body text or a related section.
4. Run `./.venv/bin/python .codex/skills/check/scripts/lint.py --wiki-dir wiki --json`.

A page is complete when the target page, reverse links, semantic properties, and lint result are all in place.

## Semantic Relations

Use these five relation fields as the frozen semantic graph schema:

- `relation_derived_from`
- `relation_extends`
- `relation_contradicts`
- `relation_uses`
- `relation_compares_with`

New relation fields require proof that these five fields cannot express the relation.

Direction rule:

- Store only outgoing edges. The current page points to the pages it cites, extends, depends on, contradicts, or compares with.
- Retrieve incoming neighbors by reverse lookup during search or Base queries.

Meaning rules:

- `relation_derived_from`: source provenance. Use this when the current page is written from one or more `wiki/sources/*` pages.
- `relation_extends`: knowledge-line continuation. Use this when the current page develops, sharpens, generalizes, or specializes an existing internal page.
- `relation_uses`: local dependency. Use this when the current page relies on an existing definition, theorem, method, tool, or conceptual component.

Target range guidance:

- `relation_derived_from` points to `wiki/sources/*`.
- `relation_extends` usually points to `wiki/concepts/*`, `wiki/theorems/*`, `wiki/foundations/*`, `wiki/ideas/*`, or `wiki/topics/*`.
- `relation_uses` usually points to `wiki/concepts/*`, `wiki/theorems/*`, `wiki/foundations/*`, `wiki/ideas/*`, `wiki/topics/*`, or `wiki/outputs/*`.
- on `wiki/sources/*`, `relation_extends`, `relation_uses`, `relation_compares_with`, and `relation_contradicts` may also point to other `wiki/sources/*` pages

Page-type matrix:

- sources: `relation_extends`, `relation_contradicts`, `relation_uses`, `relation_compares_with`
- concepts: `relation_derived_from`, `relation_extends`, `relation_uses`, `relation_compares_with`
- theorems: `relation_derived_from`, `relation_extends`, `relation_contradicts`, `relation_uses`, `relation_compares_with`
- foundations: `relation_extends`, `relation_uses`, `relation_compares_with`
- ideas: `relation_derived_from`, `relation_extends`, `relation_contradicts`, `relation_uses`, `relation_compares_with`
- topics: `relation_derived_from`, `relation_extends`, `relation_contradicts`, `relation_uses`, `relation_compares_with`
- outputs: `relation_derived_from`, `relation_uses`, `relation_compares_with`
- people: keep source provenance in `key_sources`

Use Obsidian wikilink strings as values:

```yaml
relation_derived_from:
  - "[[source-paper-a]]"
relation_extends:
  - "[[concept-b]]"
relation_uses:
  - "[[theorem-c]]"
```

Example:

```yaml
# wiki/concepts/discounted-occupancy-measure.md
relation_derived_from:
  - "[[trust-region-policy-optimization]]"
relation_extends:
  - "[[occupancy-measure]]"
relation_uses:
  - "[[markov-decision-process]]"
  - "[[discount-factor]]"
```

Properties are the graph index. `## Relations` is the evidence context.

## Tool Boundaries

Use Obsidian CLI for vault reads, note creation, property edits, search, link checks, renames, and moves.

Use Python helpers by `.venv/bin/python` for deterministic operations: lint, frontmatter lookup, slugging, duplicate checks, Semantic Scholar metadata, reset planning, setup, and tests.

Run commands from the vault root. Prefer `file=<slug>` for existing notes and `path=wiki/<type>/<slug>.md` for exact destinations.
