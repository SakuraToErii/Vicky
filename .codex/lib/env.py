"""Shared environment loader for Vicky tools.

Loads whitelisted project-level variables from `.env` so API keys configured
for this vault are available when Codex starts a fresh shell. Global `~/.env`
loading is explicit opt-in through `VICKY_LOAD_GLOBAL_ENV=1`.

Usage in any tool:
    import env  # noqa: F401  (side-effect import, loads whitelisted vars)
"""

from __future__ import annotations

import os
import pathlib

_LOADED = False
ALLOWED_ENV_KEYS = frozenset({"SEMANTIC_SCHOLAR_API_KEY"})
GLOBAL_ENV_OPT_IN = "VICKY_LOAD_GLOBAL_ENV"
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
PROJECT_ENV_PATH = PROJECT_ROOT / ".env"


def _iter_env_pairs(env_path: pathlib.Path):
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            yield key.strip(), value.strip()
    except OSError:
        return


def load(env_path: pathlib.Path | None = None, allowed_keys: frozenset[str] = ALLOWED_ENV_KEYS) -> None:
    """Load whitelisted variables into os.environ without overriding existing values."""
    path = env_path or PROJECT_ENV_PATH
    if not path.exists():
        return
    for key, value in _iter_env_pairs(path):
        if key not in allowed_keys:
            continue
        if key and key not in os.environ:
            os.environ[key] = value


def load_once() -> None:
    """Load the project .env once for side-effect imports."""
    global _LOADED
    if _LOADED:
        return
    _LOADED = True
    load()
    if os.environ.get(GLOBAL_ENV_OPT_IN) == "1":
        load(pathlib.Path.home() / ".env")


# Auto-load on import
load_once()
