# Vicky Runtime Contract

This file is the always-loaded contract for Codex inside the Vicky vault. Keep it short. Detailed procedures live in skill files.

## Core Model

Vicky is a lightweight Obsidian-native LLM wiki.

- `raw/` is user-owned input: papers, web clips, inbox notes, and scratch material.
- `wiki/` is the maintained knowledge layer: sources, concepts, theorems, foundations, people, ideas, topics, outputs, Bases, and log.
- `templates/` stores Obsidian templates for wiki page creation.
- `.codex/skills/` stores formal workflows.
- `.codex/lib/` stores shared repo-local schema and helper code.

Read from `raw/` when answering questions about source material. Write to `wiki/` only when the user asks for a skill workflow or explicitly asks to create, edit, save, reset, or check vault content.

## Default Conversation Mode

The user's normal workflow is reading newly added `raw/` material, asking questions, and deciding later what belongs in long-term notes.

In ordinary chat:

- answer questions directly from the requested raw file, selected wiki pages, or the conversation context
- explain uncertainty and cite local pages or file paths when useful
- suggest candidate notes only when it helps the user's decision
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
   - for source-backed concepts, theorems, and ideas, add the source page to `relation_derived_from`
   - for source-backed people, maintain `key_sources`
   - add the necessary `relation_*` properties
   - mirror every stable semantic edge in `## Relations`
   - add the reverse source mention or related-page mention in body text or a related section
4. Append the `wiki/log.md` entry.
5. Run `./.venv/bin/python .codex/skills/check/scripts/lint.py --wiki-dir wiki --json`.

A page is complete when the target page, reverse links, semantic properties, log entry, and lint result are all in place.

## Semantic Relations

Use these six relation fields as the frozen semantic graph schema:

- `relation_derived_from`
- `relation_extends`
- `relation_supports`
- `relation_contradicts`
- `relation_uses`
- `relation_compares_with`

New relation fields require proof that these six fields cannot express the relation.

Use Obsidian wikilink strings as values:

```yaml
relation_derived_from:
  - "[[source-paper-a]]"
relation_extends:
  - "[[concept-b]]"
```

Properties are the graph index. `## Relations` is the evidence context.

## Tool Boundaries

Use Obsidian CLI for vault reads, note creation, property edits, search, link checks, log appends, renames, and moves.

Use Python helpers for deterministic operations: lint, frontmatter lookup, slugging, duplicate checks, Semantic Scholar metadata, reset planning, setup, and tests.

Run commands from the vault root. Prefer `file=<slug>` for existing notes and `path=wiki/<type>/<slug>.md` for exact destinations.
