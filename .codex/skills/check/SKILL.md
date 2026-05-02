---
name: check
description: Use when the user wants a structural health check of the Vicky wiki with Obsidian CLI diagnostics and strict Python lint checks.
---

# Check

Run the vault health checks.

## Inputs

- optional `--fix`
- optional `--dry-run`

## References

- `AGENTS.md` for relation fields, page homes, and support-file expectations

## Workflow

1. Run Obsidian CLI diagnostics:
   - `obsidian unresolved verbose format=json`
   - `obsidian properties counts format=json`
   - `obsidian files folder=wiki ext=md total`
2. Run graph diagnostics with path filters:
   - `obsidian orphans | rg '^wiki/(sources|concepts|theorems|foundations|people|ideas|topics|outputs)/' | rg -v '^wiki/outputs/' || true`
   - `obsidian deadends | rg '^wiki/(sources|concepts|theorems|foundations|people|ideas|topics|outputs)/' | rg -v '^wiki/outputs/' || true`
3. Run strict schema lint with `./.venv/bin/python .codex/skills/check/scripts/lint.py --wiki-dir wiki/ --json`; add `--fix` for deterministic repairs when requested.
4. Report unresolved links, orphan pages, dead-end pages, duplicate slugs, missing fields, invalid values, missing source backlinks, relation property/body drift, and Base-file status.
5. Append a log line with `obsidian append file=log content="## [YYYY-MM-DD] check | report: <red> red, <yellow> yellow, <blue> blue"`.

## Constraints

- Default mode reports findings.
- `--fix` applies deterministic repairs.
- Relation properties point at existing pages and have matching `## Relations` explanations.
- Default Bases are support files for semantic relation review.
- Obsidian CLI diagnostics are the first pass; `lint.py` is the strict rule pass.
- Orphan and dead-end reporting stays scoped to the Vicky knowledge-page folders.
- Empty filtered output means the graph is clean for that check.
