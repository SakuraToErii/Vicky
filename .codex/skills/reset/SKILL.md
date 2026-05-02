---
name: reset
description: Use when the user wants to reset part of the Vicky vault, preview the deletion plan, and confirm the scope before applying it.
---

# Reset

Reset part of the vault after showing a concrete deletion plan with a hash.

## Inputs

- `--scope wiki|raw|log|checkpoints|all`
- `--include-raw` is required for any reset that includes `raw`
- `--plan-hash <hash>` is required with `--yes`
- `--rollback .trash/vicky-reset-<timestamp>` restores files moved by a raw reset

## Workflow

1. Run `./.venv/bin/python .codex/skills/reset/scripts/reset_wiki.py --scope <scope>` and show the plan plus `plan_hash`.
2. After explicit confirmation, run `./.venv/bin/python .codex/skills/reset/scripts/reset_wiki.py --scope <scope> --yes --plan-hash <hash>`.
3. Add `--include-raw` for explicitly confirmed raw input deletion.
4. For `wiki` scope, confirm `wiki/bases/Semantic Relations.base` and `wiki/bases/Current Page Neighbors.base` were restored.
5. Append a log line for scopes that keep `wiki/log.md`.

## Constraints

- Show the deletion plan first.
- Reset execution verifies `AGENTS.md`, `.obsidian/types.json`, and `wiki/` before moving files.
- Raw reset moves deleted files to `.trash/vicky-reset-<timestamp>/`.
