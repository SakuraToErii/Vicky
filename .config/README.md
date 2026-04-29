# Configuration Templates

## Files

`setup.sh` performs the dependency preflight first, then writes these files.

### `.config/.env.example`

Copy it to the project root:

```bash
cp .config/.env.example .env
```

It currently exposes one optional variable:

- `SEMANTIC_SCHOLAR_API_KEY`

Vicky tools load only this whitelisted key from the project `.env`. Global `~/.env` loading requires `VICKY_LOAD_GLOBAL_ENV=1` and still uses the same whitelist.

### `.config/settings.local.json.example`

Copy it to `.codex/settings.local.json`:

```bash
mkdir -p .codex
cp .config/settings.local.json.example .codex/settings.local.json
```

This template grants Codex local file permissions plus scoped shell permissions for the Vicky command surface.
