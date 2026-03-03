#!/usr/bin/env bash
set -euo pipefail

VENV_DIR=".venv"
PYTHON=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# --- Find Python 3.11+ ---
find_python() {
    for cmd in python3.13 python3.12 python3.11 python3 python; do
        if command -v "$cmd" &>/dev/null; then
            version=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
            major=$(echo "$version" | cut -d. -f1)
            minor=$(echo "$version" | cut -d. -f2)
            if [ "$major" -ge 3 ] && [ "$minor" -ge 11 ]; then
                PYTHON="$cmd"
                info "Found $cmd (Python $version)"
                return 0
            fi
        fi
    done
    error "Python 3.11+ is required but not found."
    error "Install with:"
    error "  Ubuntu/Debian: sudo apt install python3"
    error "  macOS: brew install python@3.12"
    exit 1
}

# --- Ensure venv works properly (pip + activate must exist) ---
ensure_venv_works() {
    local testdir
    testdir=$(mktemp -d)
    "$PYTHON" -m venv "$testdir/test" 2>/dev/null || true

    if [ ! -f "$testdir/test/bin/activate" ] || [ ! -f "$testdir/test/bin/pip" ]; then
        rm -rf "$testdir"
        warn "python3-venv is missing or broken. Installing..."
        version=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        if command -v apt-get &>/dev/null; then
            sudo apt-get update -qq && sudo apt-get install -y -qq "python${version}-venv"
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y "python${version}-venv" 2>/dev/null || sudo dnf install -y python3-virtualenv
        elif command -v pacman &>/dev/null; then
            sudo pacman -S --noconfirm python
        elif command -v brew &>/dev/null; then
            info "macOS detected — venv should be bundled with Homebrew Python."
        else
            error "Cannot auto-install python3-venv."
            error "Please install it manually:"
            error "  Ubuntu/Debian: sudo apt install python${version}-venv"
            exit 1
        fi

        # Verify fix worked
        rm -rf "$testdir"
        testdir=$(mktemp -d)
        "$PYTHON" -m venv "$testdir/test" 2>/dev/null || true
        if [ ! -f "$testdir/test/bin/activate" ]; then
            rm -rf "$testdir"
            error "python3-venv still broken after install. Please fix manually."
            exit 1
        fi
    fi
    rm -rf "$testdir"
}

# --- Check if Playwright system deps are already installed ---
playwright_deps_ok() {
    python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    b.close()
" 2>/dev/null
}

# --- Main ---
info "Content Pilot installer"
echo ""

cd "$(dirname "$0")"

find_python
ensure_venv_works

# Create venv (delete broken one if activate is missing)
if [ -d "$VENV_DIR" ] && [ ! -f "$VENV_DIR/bin/activate" ]; then
    warn "Existing venv is broken (no activate script). Recreating..."
    rm -rf "$VENV_DIR"
fi

if [ -d "$VENV_DIR" ]; then
    info "Virtual environment already exists"
else
    info "Creating virtual environment..."
    "$PYTHON" -m venv "$VENV_DIR"
fi

# Activate and install
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
info "Installing dependencies..."
pip install --upgrade pip -q
pip install -e ".[dev]" -q

# Install Playwright browser + system dependencies
if playwright install --dry-run chromium 2>&1 | grep -q "already"; then
    info "Playwright Chromium already installed"
else
    info "Installing Playwright Chromium..."
    playwright install chromium
fi

if playwright_deps_ok; then
    info "Playwright system dependencies already installed"
else
    info "Installing Playwright system dependencies (needs sudo)..."
    if command -v apt-get &>/dev/null; then
        sudo playwright install-deps chromium
    else
        warn "Non-Debian system. If browser launch fails, run:"
        warn "  sudo playwright install-deps chromium"
    fi
fi

# Setup .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    info "Created .env from .env.example — edit it to add your API key"
else
    info ".env already exists, skipping"
fi

# Create data directories
mkdir -p data/browser_contexts

echo ""
info "Installation complete!"
echo ""
echo "  Usage:"
echo ""
echo "  1. source $VENV_DIR/bin/activate"
echo "  2. nano .env                          # fill in your API key"
echo "  3. content-pilot login -p xiaohongshu # scan QR code to login"
echo "  4. content-pilot generate -t \"Python学习技巧\" -p xiaohongshu"
echo "                                        # AI generates draft, you review"
echo "  5. content-pilot publish -c 1 --dry-run  # preview before publish"
echo "  6. content-pilot publish -c 1             # publish to platform"
echo ""
echo "  Or launch the Web GUI:"
echo "     content-pilot gui                       # opens http://127.0.0.1:8080"
echo ""
echo "  Full docs: see README.md"
echo ""
