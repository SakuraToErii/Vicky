---
name: edit
description: Use when the user wants targeted edits or file operations under `wiki/` while preserving Vicky page conventions.
---

# Edit

Apply a targeted edit under `wiki/`.

## Inputs

- a user request about `wiki/`

## References

- `AGENTS.md` for page homes, relation fields, and the new-page post-processing contract
- Obsidian CLI reference: https://obsidian.md/help/cli

## Workflow

1. Resolve every target to a unique wiki slug or exact `wiki/<type>/<slug>.md` path. Edit only files under `wiki/`.
2. Read existing wiki pages directly from the filesystem.
3. Apply scoped frontmatter and body edits directly to the exact markdown file, then verify with `git diff -- <exact-target-path>`.
4. Use Obsidian CLI for vault operations that should preserve Obsidian behavior: append/prepend, move, rename, delete, and property commands when needed.
5. Append a `wiki/log.md` line for substantive changes, then run `.venv/bin/python .codex/skills/check/scripts/lint.py --wiki-dir wiki --json`.

## Obsidian CLI Usage

Run commands from the vault root.

- Use `file=<slug>` for existing wiki notes in a lint-clean vault. Use `path=wiki/<type>/<slug>.md` for ambiguous slugs or exact-path fallback.
- Append to an existing note or log: `obsidian append file=<slug> content="<text>"` or `obsidian append file=log content="## [YYYY-MM-DD] edit | ..."`.
- Prepend after frontmatter for tiny additions: `obsidian prepend file=<slug> content="<text>"`.
- Move a note with an exact destination path: `obsidian move file=<slug> to="wiki/foundations/<slug>.md"`.
- Rename a note in place: `obsidian rename file=<slug> name="<new-slug>"`.
- Delete a wiki note after explicit confirmation: `obsidian delete file=<slug>`.
- Property commands, when a CLI property edit is useful: `obsidian property:set file=<slug> name=<field> value=<value> type=text|list|number|checkbox|date|datetime`, `obsidian property:remove file=<slug> name=<field>`, and `obsidian property:read file=<slug> name=<field>`.
- Move and rename commands can update internal links when the vault setting for automatic internal-link updates is enabled.

## Constraints

- Keep edits inside `wiki/`.
- Keep edits scoped to the pages the user asked for.
- Treat open-ended requests as scoped edits to existing named wiki pages.
- Keep relation properties visible in the semantic Bases workbench.
- Prefer `file=<slug>` for existing notes. Use exact `to="wiki/..."` paths for moves and `path=wiki/...` for ambiguous targets.
- Prefer direct edits to the exact markdown file for frontmatter and body writing.
- Use Obsidian CLI for append, prepend, move, rename, delete, and property operations.
