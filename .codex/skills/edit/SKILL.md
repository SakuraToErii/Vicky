---
name: edit
description: Use when the user wants targeted edits in `wiki/` or explicit file operations in `raw/` while preserving Vicky page conventions.
---

# Edit

Apply a targeted vault edit.

## Inputs

- a user request about `raw/` or `wiki/`

## Workflow

1. Parse whether the request targets `raw/` input placement or `wiki/` knowledge pages.
2. For `raw/`, touch files only under explicit user instruction.
3. For existing `wiki/` pages, read with `obsidian read file=<slug>`. Use `path=wiki/<type>/<slug>.md` when a slug is ambiguous.
4. For property-only edits, use `obsidian property:set file=<slug> name=<field> value=<value> type=<type>`.
5. For appending short notes, use `obsidian append file=<slug> content="<markdown>"`.
6. For prepending short notes, use `obsidian prepend file=<slug> content="<markdown>"`.
7. For renames and moves, use `obsidian rename file=<slug> name=<new-name>` or `obsidian move file=<slug> to="wiki/<type>/<slug>.md"`.
8. For body edits that rewrite sections, read the note first, apply the scoped edit, then verify with `obsidian read file=<slug>`.
9. Before creating a concept, theorem, or idea page through an edit request, run `./.venv/bin/python .codex/skills/ingest/scripts/similar_pages.py wiki concept "<title>"`, `./.venv/bin/python .codex/skills/ingest/scripts/similar_pages.py wiki theorem "<title>"`, or `./.venv/bin/python .codex/skills/ingest/scripts/similar_pages.py wiki idea "<title>"`.
10. When an edit creates a new page or splits one page into several pages, finish one page at a time through the full post-processing path:
    - add `key_sources` when the page comes from a source-backed claim
    - add the necessary `relation_*` properties
    - mirror every stable semantic edge in `## Relations`
    - add the reverse source mention or related-page mention in body text or a related section
11. Use `wiki/bases/Semantic Relations.base#Relation review` after relation-property edits.
12. Append a `wiki/log.md` line for substantive changes with `obsidian append file=log content="## [YYYY-MM-DD] edit | ..."`.
13. Run `./.venv/bin/python .codex/skills/check/scripts/lint.py --wiki-dir wiki --json` after substantive knowledge-page edits and use the clean result as the completion signal.

## Relation Fields

- `relation_derived_from`
- `relation_extends`
- `relation_supports`
- `relation_contradicts`
- `relation_uses`
- `relation_compares_with`

## Constraints

- Treat `raw/` as user-owned input.
- Keep edits scoped to the pages the user asked for.
- Keep relation properties visible in the semantic Bases workbench.
- Treat the six listed `relation_*` fields as the frozen relation contract.
- Finish one new page completely before moving to the next new page in the same turn.
- Prefer `file=<slug>` for existing notes and `path=` for exact destinations.
- Prefer Obsidian CLI for reads, property edits, appends, prepends, renames, and moves.
