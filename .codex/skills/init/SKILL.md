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

- `templates/`

## Template Map

| Wiki path | Obsidian template |
|---|---|
| `wiki/sources/{slug}.md` | `Wiki_Source` |
| `wiki/concepts/{slug}.md` | `Wiki_Concept` |
| `wiki/theorems/{slug}.md` | `Wiki_Theorem` |
| `wiki/foundations/{slug}.md` | `Wiki_Foundation` |
| `wiki/people/{slug}.md` | `Wiki_Person` |
| `wiki/ideas/{slug}.md` | `Wiki_Idea` |
| `wiki/topics/{slug}.md` | `Wiki_Topic` |
| `wiki/outputs/{slug}.md` | `Wiki_Output` |

## Workflow

1. Confirm the project root contains `raw/`, `wiki/`, `templates/`, and `.codex/`.
2. Run `obsidian templates` and confirm the `Wiki_*` templates are available.
3. Confirm core folders with `obsidian folders folder=wiki`. Create missing folders with the filesystem when Obsidian has no folder-create command.
4. Create support files with Obsidian CLI when missing:
   - `obsidian create path="wiki/log.md" content="# Vicky Log\n\n"`
5. Restore default Base support files with `./.venv/bin/python .codex/skills/check/tools/lint.py --wiki-dir wiki --fix --json`.
6. If a topic was provided, create `wiki/topics/<slug>.md` with `obsidian create path="wiki/topics/<slug>.md" template="Wiki_Topic"`.
7. Fill the created page frontmatter with `obsidian property:set` and body fields with scoped page edits.
8. Append a log entry with `obsidian append file=log content="## [YYYY-MM-DD] init | wiki initialized"`.

## Constraints

- `raw/` stays read-only.
- Keep `topic` optional.
- Create wiki pages from `templates/` through Obsidian CLI when the template exists.
- Keep default Bases available for relation review.
- Use Obsidian CLI for support-file creation and log appends.
