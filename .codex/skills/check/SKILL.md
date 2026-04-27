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
   - `obsidian orphans`
   - `obsidian deadends`
   - `obsidian properties counts format=json`
   - `obsidian files folder=wiki ext=md total`
2. Run strict schema lint with `./.venv/bin/python .tools/lint.py --wiki-dir wiki/ --json`.
3. If `--fix` is present, run `./.venv/bin/python .tools/lint.py --wiki-dir wiki/ --fix --json`.
4. Report unresolved links, orphan pages, dead-end pages, duplicate slugs, missing fields, invalid values, missing source backlinks, and relation property/body drift.
5. Confirm default Base files exist under `wiki/bases/` and restore them with `--fix` when missing or malformed.
6. Append a log line with `obsidian append file=log content="## [YYYY-MM-DD] check | report: <red> red, <yellow> yellow, <blue> blue"`.

## Constraints

- Default mode is report-only.
- `--fix` should stay limited to deterministic repairs.
- Relation fields are semantic graph edges. Every relation property should point at an existing page and have a matching `## Relations` explanation.
- The six `relation_*` fields are a frozen schema. Add a new relation field only after proving the existing six fields cannot express the relation.
- Default Bases are support files for semantic relation review.
- Obsidian CLI diagnostics are the first pass; `.tools/lint.py` is the strict rule pass.
