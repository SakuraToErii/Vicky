---
name: setup
description: Use when working in the Vicky repo and the user wants to prepare the local environment by creating `.venv`, `.env`, and `.codex/settings.local.json`.
---

# Setup

Prepare the local environment for the Vicky vault.

## Inputs

- none

## Outputs

- `.venv/`
- `.env`
- `.codex/settings.local.json`

## Workflow

1. Confirm the working directory contains `raw/`, `wiki/`, `.tools/`, and `.config/`.
2. Run `./setup.sh`.
3. Report whether `.venv`, `.env`, and `.codex/settings.local.json` are ready.

## Constraints

- Do not overwrite an existing `.env` or `.codex/settings.local.json` without user approval.
- Keep setup focused on the local vault workflow.
