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

1. Run `./.venv/bin/python .codex/skills/reset/scripts/reset_wiki.py --scope <scope>` to print the plan and `plan_hash`.
2. Show the plan to the user.
3. After explicit confirmation, run `./.venv/bin/python .codex/skills/reset/scripts/reset_wiki.py --scope <scope> --yes --plan-hash <hash>`.
4. Add `--include-raw` only when the user explicitly confirms raw input deletion.
5. For `wiki` scope, confirm `wiki/bases/Semantic Relations.base` and `wiki/bases/Current Page Neighbors.base` were restored.
6. Append a log line unless `log` was reset.

## Constraints

- Always show the deletion plan first.
- Reset execution verifies `AGENTS.md`, `.obsidian/types.json`, and `wiki/` before moving files.
- Raw reset moves deleted files to `.trash/vicky-reset-<timestamp>/`.
