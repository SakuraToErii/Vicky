---
name: init
description: Use when the user wants to initialize or rebuild the Vicky wiki scaffold and optionally seed a topic page with the repository templates.
---

# Init

Create the wiki scaffold for the current vault.

## Inputs

- `topic` (optional)

## Outputs

- `wiki/sources/`
- `wiki/concepts/`
- `wiki/theorems/`
- `wiki/foundations/`
- `wiki/people/`
- `wiki/ideas/`
- `wiki/topics/`
- `wiki/outputs/`
- `wiki/bases/`
- `wiki/bases/Semantic Relations.base`
- `wiki/bases/Current Page Neighbors.base`
- `wiki/log.md`

## References

- `references/wiki-bootstrap-templates.md`
- `templates/`

## Workflow

1. Confirm the project root contains `raw/`, `wiki/`, and `.tools/`.
2. Run `obsidian templates` and confirm the `Wiki_*` templates are available.
3. Read `references/wiki-bootstrap-templates.md` for the template-name map.
4. Confirm core folders with `obsidian folders folder=wiki`. Create missing folders with the filesystem only when Obsidian has no folder-create command.
5. Create support files with Obsidian CLI when missing:
   - `obsidian create path="wiki/log.md" content="# Vicky Log\n\n"`
6. Create missing default Base files from `.tools/_schemas.py`: `wiki/bases/Semantic Relations.base` and `wiki/bases/Current Page Neighbors.base`.
7. If a topic was provided, create `wiki/topics/<slug>.md` with `obsidian create path="wiki/topics/<slug>.md" template="Wiki_Topic"`.
8. Fill the created page frontmatter with `obsidian property:set` and body fields with scoped page edits.
9. Append a log entry with `obsidian append file=log content="## [YYYY-MM-DD] init | wiki initialized"`.

## Constraints

- `raw/` stays read-only.
- Keep `topic` optional.
- Create wiki pages from `templates/` through Obsidian CLI when the template exists.
- Keep default Bases available for relation review.
- Use Obsidian CLI for support-file creation and log appends.
