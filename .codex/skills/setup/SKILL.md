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

1. Confirm the working directory contains `raw/`, `wiki/`, `.codex/`, and `.config/`, then run `./setup.sh`.
2. Report whether `.venv`, `.env`, and `.codex/settings.local.json` are ready.

## Constraints

- Preserve existing `.env` and `.codex/settings.local.json`; overwrite them with user approval.
- Keep setup focused on the local vault workflow.
