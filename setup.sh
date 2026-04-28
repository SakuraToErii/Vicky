#!/usr/bin/env bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC}  $1"; }
ok() { echo -e "${GREEN}[OK]${NC}    $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $1"; }
fail() { echo -e "${RED}[FAIL]${NC}  $1"; }

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo ""
echo "============================================"
echo "  Vicky — Setup"
echo "============================================"
echo ""

info "Checking prerequisites..."

if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
    PY_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
    PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
    if [ "$PY_MAJOR" -lt 3 ] || [ "$PY_MINOR" -lt 9 ]; then
        fail "Python >= 3.9 required, found $PY_VERSION"
        exit 1
    fi
    ok "Python $PY_VERSION"
else
    fail "python3 not found"
    exit 1
fi

echo ""
info "Checking required CLIs..."
"$PYTHON_CMD" .codex/lib/preflight.py commands codex obsidian rg
ok "Required CLIs available"

echo ""
info "Preparing .venv..."

if [ -d ".venv" ]; then
    warn ".venv already exists, reusing it"
else
    "$PYTHON_CMD" -m venv .venv
    ok "Created .venv"
fi

VENV_PYTHON=".venv/bin/python"
VENV_PYTHON_ABS="$PROJECT_ROOT/$VENV_PYTHON"
if [ ! -x "$VENV_PYTHON" ]; then
    fail "Expected $VENV_PYTHON"
    exit 1
fi

info "Installing dependencies..."
"$VENV_PYTHON" -m pip install --upgrade pip >/dev/null
"$VENV_PYTHON" -m pip install "requests>=2.28.0" "PyYAML>=6.0" >/dev/null
ok "Dependencies installed"

echo ""
info "Verifying Python packages..."
"$VENV_PYTHON_ABS" .codex/lib/preflight.py modules requests yaml
ok "Python packages available"

echo ""
info "Writing config files..."

if [ -f ".env" ]; then
    warn ".env already exists"
else
    cp .config/.env.example .env
    ok "Created .env"
fi

mkdir -p .codex
if [ -f ".codex/settings.local.json" ]; then
    warn ".codex/settings.local.json already exists"
else
    cp .config/settings.local.json.example .codex/settings.local.json
    ok "Created .codex/settings.local.json"
fi

echo ""
info "Verifying core imports..."

if PYTHONPATH="$PROJECT_ROOT/.codex/lib:$PROJECT_ROOT/.codex/skills/check/scripts:$PROJECT_ROOT/.codex/skills/ingest/scripts:$PROJECT_ROOT/.codex/skills/reset/scripts:$PROJECT_ROOT/.codex/skills/ask/scripts" "$VENV_PYTHON_ABS" -c "from schema import INDEXED_DIRS; from lint import run_lint; from fetch_s2 import search; from reset_wiki import plan; from slug import slugify; from similar_pages import find_similar_concept; from frontmatter_find import find_entities" >/dev/null 2>&1; then
    ok "Core scripts import cleanly"
else
    fail "Core script import failed"
    exit 1
fi

echo ""
ok "Setup complete"
echo ""
echo "Next steps:"
echo "  1. Put prepared sources in raw/papers/ or raw/web/"
echo "  2. Open the repository root in Obsidian"
echo "  3. Run: codex"
echo "  4. Ask Codex to ingest a source you choose from raw/"
echo "  5. Use wiki/bases/Semantic Relations.base for semantic relation review"
