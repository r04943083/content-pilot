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
    error "Install it with: sudo apt install python3 (Ubuntu/Debian)"
    exit 1
}

# --- Ensure venv module is available ---
ensure_venv_module() {
    if ! "$PYTHON" -c "import venv" &>/dev/null; then
        warn "python3-venv not installed. Attempting to install..."
        version=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        if command -v apt &>/dev/null; then
            sudo apt update && sudo apt install -y "python${version}-venv"
        elif command -v dnf &>/dev/null; then
            sudo dnf install -y "python${version}-venv" || sudo dnf install -y python3-virtualenv
        elif command -v pacman &>/dev/null; then
            sudo pacman -S --noconfirm python
        else
            error "Cannot auto-install python3-venv. Please install it manually."
            exit 1
        fi
    fi
}

# --- Main ---
info "Content Pilot installer"
echo ""

cd "$(dirname "$0")"

find_python
ensure_venv_module

# Create venv
if [ -d "$VENV_DIR" ]; then
    warn "Virtual environment already exists at $VENV_DIR"
else
    info "Creating virtual environment..."
    "$PYTHON" -m venv "$VENV_DIR"
fi

# Activate and install
info "Installing dependencies..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip -q
pip install -e ".[dev]"

# Install Playwright browser
info "Installing Playwright Chromium..."
playwright install chromium

# Setup .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    info "Created .env from .env.example — please edit it with your API keys."
else
    info ".env already exists, skipping."
fi

# Create data directories
mkdir -p data/browser_contexts

echo ""
info "Installation complete!"
echo ""
echo "  Activate the virtual environment:"
echo "    source $VENV_DIR/bin/activate"
echo ""
echo "  Then run:"
echo "    content-pilot --help"
echo ""
echo "  Quick start:"
echo "    content-pilot login --platform xiaohongshu"
echo "    content-pilot generate --topic \"Python学习技巧\" --platform xiaohongshu"
echo ""
