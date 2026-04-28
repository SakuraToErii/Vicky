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
9. Use `wiki/bases/Semantic Relations.base#Relation review` after relation-property edits.
10. Append a log line for substantive changes with `obsidian append file=log content="## [YYYY-MM-DD] edit | ..."`.

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
- Prefer `file=<slug>` for existing notes and `path=` for exact destinations.
- Prefer Obsidian CLI for reads, property edits, appends, prepends, renames, and moves.
