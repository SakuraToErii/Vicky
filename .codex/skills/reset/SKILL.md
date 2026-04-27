---
name: reset
description: Use when the user wants to reset part of the Vicky vault, preview the deletion plan, and confirm the scope before applying it.
---

# Reset

Reset part of the vault after showing a concrete deletion plan.

## Inputs

- `--scope wiki|raw|log|checkpoints|all`

## Workflow

1. Run `./.venv/bin/python .tools/reset_wiki.py --scope <scope>` to print the plan.
2. Show the plan to the user.
3. After explicit confirmation, run `./.venv/bin/python .tools/reset_wiki.py --scope <scope> --yes`.
4. For `wiki` scope, confirm `wiki/bases/Semantic Relations.base` and `wiki/bases/Current Page Neighbors.base` were restored.
5. Append a log line unless `log` was reset.

## Constraints

- Always show the deletion plan first.
- Treat `raw` reset as irreversible.
