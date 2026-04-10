#!/usr/bin/env bash
# ============================================================
# RSI Hybrid System — MLX Setup & Model Testing Script
# ============================================================
# This script:
#   1. Checks system prerequisites (Python, pip)
#   2. Installs mlx-lm and project dependencies
#   3. Downloads required models
#   4. Starts the MLX server on localhost:8080
#   5. Runs a smoke test against each model
#
# Usage:
#   chmod +x setup_mlx.sh
#   ./setup_mlx.sh              # Full setup
#   ./setup_mlx.sh --test-only  # Skip install, just test
# ============================================================

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*"; }
info() { echo -e "${BLUE}[i]${NC} $*"; }

# ── Config ────────────────────────────────────────────────────
MLX_PORT=8080
MLX_HOST="127.0.0.1"
MAIN_MODEL="mlx-community/Qwen3-32B-4bit"
FAST_MODEL="mlx-community/Qwen3-4B-4bit"
REASONING_MODEL="mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit"

# ── Prerequisites ─────────────────────────────────────────────
check_prerequisites() {
    info "Checking prerequisites..."

    if ! command -v python3 &>/dev/null; then
        err "Python 3 not found. Install Python 3.11+ first."
        exit 1
    fi

    PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    log "Python $PY_VERSION found"

    if ! command -v pip3 &>/dev/null && ! python3 -m pip --version &>/dev/null; then
        err "pip not found. Install pip first."
        exit 1
    fi
    log "pip available"

    # Check if on Apple Silicon (for MLX)
    if [[ "$(uname -s)" == "Darwin" ]]; then
        ARCH=$(uname -m)
        if [[ "$ARCH" != "arm64" ]]; then
            warn "MLX requires Apple Silicon (arm64). Detected: $ARCH"
            warn "MLX will not work on this machine. Skipping model download."
            exit 1
        fi
        log "Apple Silicon detected ($ARCH)"
    else
        warn "Not on macOS — MLX requires Apple Silicon Mac"
        warn "This script will install dependencies but MLX models won't run here"
    fi
}

# ── Install Dependencies ─────────────────────────────────────
install_deps() {
    info "Installing Python dependencies..."

    python3 -m pip install --upgrade pip

    # Core dependencies
    python3 -m pip install \
        mlx-lm \
        httpx \
        pydantic \
        pytest \
        pytest-asyncio

    log "Dependencies installed"
}

# ── Download Models ───────────────────────────────────────────
download_models() {
    info "Downloading MLX models (this may take a while)..."

    for MODEL in "$FAST_MODEL" "$MAIN_MODEL" "$REASONING_MODEL"; do
        info "Downloading $MODEL..."
        python3 -c "
from huggingface_hub import snapshot_download
try:
    snapshot_download('$MODEL', local_files_only=False)
    print('Downloaded: $MODEL')
except Exception as e:
    print(f'Download error for $MODEL: {e}')
    print('Will retry on first use.')
"
        log "Model ready: $MODEL"
    done
}

# ── Start MLX Server ─────────────────────────────────────────
start_server() {
    info "Starting MLX server on $MLX_HOST:$MLX_PORT..."

    # Check if already running
    if curl -s "http://$MLX_HOST:$MLX_PORT/v1/models" &>/dev/null; then
        warn "MLX server already running on port $MLX_PORT"
        return
    fi

    # Start with the fast model loaded by default
    python3 -m mlx_lm.server \
        --model "$FAST_MODEL" \
        --host "$MLX_HOST" \
        --port "$MLX_PORT" &

    SERVER_PID=$!
    echo "$SERVER_PID" > /tmp/mlx_server.pid
    info "Server PID: $SERVER_PID"

    # Wait for server to be ready
    for i in $(seq 1 30); do
        if curl -s "http://$MLX_HOST:$MLX_PORT/v1/models" &>/dev/null; then
            log "MLX server is ready!"
            return
        fi
        sleep 2
    done

    err "MLX server failed to start within 60 seconds"
    exit 1
}

# ── Smoke Tests ───────────────────────────────────────────────
run_smoke_test() {
    local model_name="$1"
    local test_prompt="$2"

    info "Testing model: $model_name"

    RESPONSE=$(curl -s -X POST "http://$MLX_HOST:$MLX_PORT/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"$model_name\",
            \"messages\": [{\"role\": \"user\", \"content\": \"$test_prompt\"}],
            \"max_tokens\": 100,
            \"temperature\": 0.3
        }" 2>&1)

    if echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['choices'][0]['message']['content'][:200])" 2>/dev/null; then
        log "Model $model_name: OK"
    else
        err "Model $model_name: FAILED"
        echo "$RESPONSE" | head -5
    fi
}

run_all_tests() {
    info "Running smoke tests..."
    echo ""

    run_smoke_test "$FAST_MODEL" "What is the SET index? Answer in one sentence."
    echo ""

    run_smoke_test "$MAIN_MODEL" "Analyze the Thai banking sector outlook in 2-3 sentences."
    echo ""

    run_smoke_test "$REASONING_MODEL" "What is the Nash equilibrium in a simple market scenario? Brief answer."
    echo ""

    log "All smoke tests completed"
}

# ── Health Check ──────────────────────────────────────────────
health_check() {
    info "Running health check..."

    if curl -s "http://$MLX_HOST:$MLX_PORT/v1/models" | python3 -c "
import sys, json
data = json.load(sys.stdin)
models = [m['id'] for m in data.get('data', [])]
print(f'Available models: {len(models)}')
for m in models:
    print(f'  - {m}')
" 2>/dev/null; then
        log "Health check passed"
    else
        err "Health check failed — server not responding"
        exit 1
    fi
}

# ── Main ──────────────────────────────────────────────────────
main() {
    echo ""
    echo "╔══════════════════════════════════════════════╗"
    echo "║   RSI Hybrid System — MLX Setup              ║"
    echo "╚══════════════════════════════════════════════╝"
    echo ""

    if [[ "${1:-}" == "--test-only" ]]; then
        health_check
        run_all_tests
        exit 0
    fi

    check_prerequisites
    install_deps
    download_models
    start_server
    health_check
    run_all_tests

    echo ""
    log "Setup complete! MLX server running on http://$MLX_HOST:$MLX_PORT"
    info "To stop: kill \$(cat /tmp/mlx_server.pid)"
    info "To test: ./setup_mlx.sh --test-only"
    info "To run pipeline: python orchestrator.py"
    echo ""
}

main "$@"
