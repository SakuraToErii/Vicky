---
name: check
description: Use when the user wants a structural health check of the Vicky wiki with Obsidian CLI diagnostics and strict Python lint checks.
---

# Check

Run the vault health checks.

## Inputs

- optional `--fix`
- optional `--dry-run`

## Workflow

1. Run Obsidian CLI diagnostics first:
   - `obsidian unresolved verbose format=json`
   - `obsidian properties counts format=json`
   - `obsidian files folder=wiki ext=md total`
2. Run repo-local graph diagnostics:
   - `./.venv/bin/python .codex/skills/check/scripts/wiki_graph.py wiki/ orphans`
   - `./.venv/bin/python .codex/skills/check/scripts/wiki_graph.py wiki/ deadends`
3. Run strict schema lint with `./.venv/bin/python .codex/skills/check/scripts/lint.py --wiki-dir wiki/ --json`.
4. If `--fix` is present, run `./.venv/bin/python .codex/skills/check/scripts/lint.py --wiki-dir wiki/ --fix --json`.
5. Report unresolved links, orphan pages, dead-end pages, duplicate slugs, missing fields, invalid values, missing source backlinks, and relation property/body drift.
6. Confirm default Base files exist under `wiki/bases/` and restore them with `--fix` when missing or malformed.
7. Append a log line with `obsidian append file=log content="## [YYYY-MM-DD] check | report: <red> red, <yellow> yellow, <blue> blue"`.

## Constraints

- Default mode is report-only.
- `--fix` should stay limited to deterministic repairs.
- Relation fields are semantic graph edges. Every relation property should point at an existing page and have a matching `## Relations` explanation.
- Treat `relation_derived_from`, `relation_extends`, `relation_supports`, `relation_contradicts`, `relation_uses`, and `relation_compares_with` as the frozen relation contract.
- Default Bases are support files for semantic relation review.
- Obsidian CLI diagnostics are the first pass; `lint.py` is the strict rule pass.
