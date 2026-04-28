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
   - `./.venv/bin/python .tools/research_wiki.py query wiki/ orphans`
   - `./.venv/bin/python .tools/research_wiki.py query wiki/ deadends`
3. Run strict schema lint with `./.venv/bin/python .tools/lint.py --wiki-dir wiki/ --json`.
4. If `--fix` is present, run `./.venv/bin/python .tools/lint.py --wiki-dir wiki/ --fix --json`.
5. Report unresolved links, orphan pages, dead-end pages, duplicate slugs, missing fields, invalid values, missing source backlinks, and relation property/body drift.
6. Confirm default Base files exist under `wiki/bases/` and restore them with `--fix` when missing or malformed.
7. Append a log line with `obsidian append file=log content="## [YYYY-MM-DD] check | report: <red> red, <yellow> yellow, <blue> blue"`.

## Constraints

- Default mode is report-only.
- `--fix` should stay limited to deterministic repairs.
- Relation fields are semantic graph edges. Every relation property should point at an existing page and have a matching `## Relations` explanation.
- Follow `.docs/semantic-relations.en.md` for the frozen relation field contract.
- Default Bases are support files for semantic relation review.
- Obsidian CLI diagnostics are the first pass; `.tools/lint.py` is the strict rule pass.
