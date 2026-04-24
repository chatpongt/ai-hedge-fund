#!/usr/bin/env bash
# setup.sh — one-time environment setup for the MD&A extraction pipeline
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECTS_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
KG_DIR="$PROJECTS_DIR/ai-knowledge-graph"

echo ""
echo "══════════════════════════════════════════════════"
echo "  MD&A Pipeline — Setup"
echo "══════════════════════════════════════════════════"
echo ""

# ── Python deps ───────────────────────────────────────────────────────────────
echo "▶ Installing Python dependencies…"
pip install --quiet \
    pymupdf4llm \
    pypdf \
    anthropic \
    rich \
    tomli \
    networkx \
    pyvis

echo "  ✓ Core deps installed"

# marker-pdf is optional (heavy, ~1 GB with models) — install if not present
if ! python -c "import marker" 2>/dev/null; then
    echo ""
    echo "  marker-pdf not found. Installing… (this may take a few minutes)"
    pip install --quiet marker-pdf
    echo "  ✓ marker-pdf installed"
else
    echo "  ✓ marker-pdf already installed"
fi

# ── System tools check ────────────────────────────────────────────────────────
echo ""
echo "▶ Checking system tools…"
for tool in pdftotext pdffonts; do
    if command -v "$tool" &>/dev/null; then
        echo "  ✓ $tool"
    else
        echo "  ✗ $tool not found — install poppler-utils:"
        echo "      Ubuntu/Debian:  sudo apt install poppler-utils"
        echo "      macOS:          brew install poppler"
    fi
done

# ── Clone ai-knowledge-graph ──────────────────────────────────────────────────
echo ""
echo "▶ Setting up ai-knowledge-graph…"
if [ -d "$KG_DIR/.git" ]; then
    echo "  ✓ Already cloned at $KG_DIR"
    git -C "$KG_DIR" pull --quiet origin main || true
else
    echo "  Cloning into $KG_DIR…"
    git clone --quiet https://github.com/robert-mcdermott/ai-knowledge-graph.git "$KG_DIR"
    echo "  ✓ Cloned"
fi

# Install ai-knowledge-graph deps
if [ -f "$KG_DIR/requirements.txt" ]; then
    echo "  Installing ai-knowledge-graph requirements…"
    pip install --quiet -r "$KG_DIR/requirements.txt"
    echo "  ✓ ai-knowledge-graph deps installed"
fi

# ── API key check ─────────────────────────────────────────────────────────────
echo ""
echo "▶ Checking API key…"
if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
    echo "  ✓ ANTHROPIC_API_KEY is set"
else
    echo "  ✗ ANTHROPIC_API_KEY not set"
    echo "    Add this to your shell profile:"
    echo "      export ANTHROPIC_API_KEY=sk-ant-..."
fi

# ── Create input dir ──────────────────────────────────────────────────────────
mkdir -p "$SCRIPT_DIR/data/input"
echo ""
echo "══════════════════════════════════════════════════"
echo "  Setup complete!"
echo ""
echo "  Next steps:"
echo "    1. Drop PDF annual reports into:  $SCRIPT_DIR/data/input/"
echo "    2. Naming: TICKER_YEAR.pdf  e.g.  CPALL_2024.pdf"
echo "    3. Run:    python batch.py --dry-run"
echo "    4. Run:    python batch.py"
echo "══════════════════════════════════════════════════"
echo ""
