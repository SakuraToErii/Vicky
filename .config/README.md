# Configuration Templates

## Files

### `.config/.env.example`

Copy it to the project root:

```bash
cp .config/.env.example .env
```

It currently exposes one optional variable:

- `SEMANTIC_SCHOLAR_API_KEY`

### `.config/settings.local.json.example`

Copy it to `.codex/settings.local.json`:

```bash
mkdir -p .codex
cp .config/settings.local.json.example .codex/settings.local.json
```

This template grants Codex the basic local file and shell permissions needed to maintain the vault.
