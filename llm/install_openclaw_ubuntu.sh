#!/usr/bin/env bash
# =============================================================================
# install_openclaw_ubuntu.sh
# Install OpenClaw AI Agent on Ubuntu 24.04 (also works on 22.04, 20.04)
# =============================================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'
BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*"; exit 1; }
section() { echo -e "\n${BOLD}${CYAN}━━━ $* ━━━${RESET}\n"; }

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════╗"
echo -e "║   OpenClaw Install — Ubuntu 24.04 LTS    ║"
echo -e "╚══════════════════════════════════════════╝${RESET}"
echo ""

# Detect Ubuntu version
if [ -f /etc/os-release ]; then
  . /etc/os-release
  info "Detected OS: $PRETTY_NAME"
  if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
    warn "This script is optimised for Ubuntu/Debian. Proceeding anyway..."
  fi
fi

# =============================================================================
# STEP 1 — System update + dependencies
# =============================================================================
section "Step 1: System packages"

info "Updating package index..."
sudo apt-get update -qq

info "Installing required packages..."
sudo apt-get install -y \
  curl \
  git \
  gnupg \
  ca-certificates \
  build-essential \
  lsb-release \
  software-properties-common

success "System packages ready"

# =============================================================================
# STEP 2 — Node.js 24 LTS (recommended) via NodeSource
# =============================================================================
section "Step 2: Node.js 24 LTS"

REQUIRED_NODE=22   # minimum
RECOMMENDED_NODE=24

if command -v node &>/dev/null; then
  CURRENT_NODE=$(node --version | sed 's/v//' | cut -d. -f1)
  if [ "$CURRENT_NODE" -ge "$RECOMMENDED_NODE" ]; then
    success "Node.js $(node --version) already installed — skipping"
    SKIP_NODE=true
  elif [ "$CURRENT_NODE" -ge "$REQUIRED_NODE" ]; then
    warn "Node.js $(node --version) found — meets minimum (v22) but v24 is recommended"
    read -r -p "Upgrade to Node.js 24? (Y/n) " UPGRADE
    SKIP_NODE=$( [ "${UPGRADE,,}" = "n" ] && echo "true" || echo "false" )
  else
    warn "Node.js $(node --version) is too old — upgrading to Node.js 24..."
    SKIP_NODE=false
  fi
else
  info "Node.js not found — installing Node.js 24..."
  SKIP_NODE=false
fi

if [ "$SKIP_NODE" = false ]; then
  info "Adding NodeSource repository for Node.js 24..."
  curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
  sudo apt-get install -y nodejs
  success "Node.js $(node --version) installed"
fi

# Verify npm
info "npm version: $(npm --version)"
if [ "$(npm --version | cut -d. -f1)" -lt 8 ]; then
  info "Upgrading npm..."
  sudo npm install -g npm@latest
fi
success "npm ready: $(npm --version)"

# =============================================================================
# STEP 3 — Install OpenClaw
# =============================================================================
section "Step 3: Installing OpenClaw"

# Check if already installed
if command -v openclaw &>/dev/null; then
  CURRENT_VER=$(openclaw --version 2>/dev/null || echo "unknown")
  warn "OpenClaw already installed: $CURRENT_VER"
  read -r -p "Reinstall/upgrade? (Y/n) " REINSTALL
  if [ "${REINSTALL,,}" = "n" ]; then
    info "Skipping OpenClaw install — keeping existing version"
    SKIP_OPENCLAW=true
  else
    SKIP_OPENCLAW=false
  fi
else
  SKIP_OPENCLAW=false
fi

if [ "$SKIP_OPENCLAW" = false ]; then
  info "Running OpenClaw official installer (no onboarding — we'll do it next)..."

  # Official installer with --no-onboard so we can configure first
  curl -fsSL https://openclaw.ai/install.sh | bash -s -- --no-onboard

  # Add to PATH for this session if needed
  for BIN_DIR in "$HOME/.local/bin" "$HOME/.npm-global/bin" "$HOME/.openclaw/bin"; do
    if [ -x "$BIN_DIR/openclaw" ]; then
      export PATH="$BIN_DIR:$PATH"
      # Persist in .bashrc and .zshrc
      for RC in "$HOME/.bashrc" "$HOME/.zshrc"; do
        if [ -f "$RC" ] && ! grep -q "$BIN_DIR" "$RC" 2>/dev/null; then
          echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$RC"
        fi
      done
      break
    fi
  done

  # Fallback: npm global install
  if ! command -v openclaw &>/dev/null; then
    warn "Installer script didn't place openclaw in PATH — trying npm global install..."
    npm install -g openclaw@latest
  fi

  command -v openclaw &>/dev/null || error "OpenClaw installation failed. Check errors above."
  success "OpenClaw installed: $(openclaw --version 2>/dev/null)"
fi

# =============================================================================
# STEP 4 — Install systemd gateway service (optional, for always-on)
# =============================================================================
section "Step 4: Gateway service (systemd)"

read -r -p "Install OpenClaw as a systemd service (always-on)? (Y/n) " INSTALL_SERVICE

if [ "${INSTALL_SERVICE,,}" != "n" ]; then
  info "Installing and starting OpenClaw gateway service..."
  openclaw gateway install
  openclaw gateway start
  success "Gateway service installed and running"
  info "Check service: systemctl status openclaw-gateway"
  info "View logs:     journalctl -u openclaw-gateway -f"
else
  warn "Skipping gateway service — you can run OpenClaw manually with: openclaw start"
fi

# =============================================================================
# STEP 5 — Configure LLM provider
# =============================================================================
section "Step 5: LLM provider configuration"

CONFIG_DIR="$HOME/.config/openclaw"
mkdir -p "$CONFIG_DIR"
CONFIG_FILE="$CONFIG_DIR/openclaw.json"

info "Which LLM provider do you want to configure?"
echo "  1) Anthropic Claude (recommended — best quality)"
echo "  2) OpenAI GPT"
echo "  3) Google Gemini"
echo "  4) Cursor ACP (via Cursor Pro subscription — no API key needed)"
echo "  5) Ollama (local — no API key needed)"
echo "  6) Skip — I'll configure manually"
echo ""
read -r -p "Enter choice [1-6]: " PROVIDER_CHOICE

case "$PROVIDER_CHOICE" in
  1)
    read -r -p "Enter your Anthropic API key (sk-ant-...): " ANTHROPIC_KEY
    export ANTHROPIC_API_KEY="$ANTHROPIC_KEY"
    echo "export ANTHROPIC_API_KEY=\"$ANTHROPIC_KEY\"" >> "$HOME/.bashrc"
    success "Anthropic API key set"
    ;;
  2)
    read -r -p "Enter your OpenAI API key (sk-...): " OPENAI_KEY
    export OPENAI_API_KEY="$OPENAI_KEY"
    echo "export OPENAI_API_KEY=\"$OPENAI_KEY\"" >> "$HOME/.bashrc"
    success "OpenAI API key set"
    ;;
  3)
    read -r -p "Enter your Google Gemini API key (AIza...): " GOOGLE_KEY
    export GOOGLE_GENERATIVE_AI_API_KEY="$GOOGLE_KEY"
    echo "export GOOGLE_GENERATIVE_AI_API_KEY=\"$GOOGLE_KEY\"" >> "$HOME/.bashrc"
    success "Google Gemini API key set"
    ;;
  4)
    info "Installing Cursor ACP plugin..."
    npm install -g @rama_nigg/open-cursor
    cat > "$CONFIG_FILE" << 'EOF'
{
  "$schema": "https://openclaw.ai/config.json",
  "plugin": ["@rama_nigg/open-cursor@latest"],
  "provider": {
    "cursor-acp": {
      "name": "Cursor ACP",
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "baseURL": "http://127.0.0.1:32124/v1",
        "apiKey": "cursor-proxy"
      },
      "models": {
        "cursor-acp/claude-opus-4.6":           { "name": "Claude Opus 4.6" },
        "cursor-acp/claude-sonnet-4.6":         { "name": "Claude Sonnet 4.6" },
        "cursor-acp/claude-opus-4.6-thinking":  { "name": "Claude Opus 4.6 Thinking" },
        "cursor-acp/gemini-3.1-pro":            { "name": "Gemini 3.1 Pro" },
        "cursor-acp/composer-1.5":              { "name": "Cursor Composer 1.5" }
      }
    }
  },
  "model": "cursor-acp/claude-opus-4.6"
}
EOF
    success "Cursor ACP config written to $CONFIG_FILE"
    warn "Remember: Cursor IDE must be running on your machine (or tunnelled from your laptop)"
    ;;
  5)
    info "Checking for Ollama..."
    if ! command -v ollama &>/dev/null; then
      info "Installing Ollama..."
      curl -fsSL https://ollama.com/install.sh | sh
    fi
    success "Ollama ready: $(ollama --version)"
    info "Pull a model (e.g.: ollama pull qwen3:32b)"
    ;;
  6)
    warn "Skipping provider config — run 'openclaw onboard' to configure later"
    ;;
  *)
    warn "Invalid choice — skipping provider config"
    ;;
esac

# =============================================================================
# STEP 6 — Run onboarding (if not skipping)
# =============================================================================
section "Step 6: Onboarding"

if [ "$PROVIDER_CHOICE" != "6" ] && [ "$PROVIDER_CHOICE" != "4" ]; then
  read -r -p "Run OpenClaw onboarding wizard now? (Y/n) " RUN_ONBOARD
  if [ "${RUN_ONBOARD,,}" != "n" ]; then
    info "Launching onboarding..."
    openclaw onboard
  fi
fi

# =============================================================================
# DONE
# =============================================================================
section "Installation Complete!"

echo -e "${GREEN}OpenClaw is ready on Ubuntu 24.04!${RESET}"
echo ""
echo -e "${CYAN}Useful commands:${RESET}"
echo "  openclaw start               — start OpenClaw agent"
echo "  openclaw gateway status      — check gateway service"
echo "  openclaw onboard             — re-run configuration wizard"
echo "  openclaw skill install <id>  — install community skills"
echo "  openclaw --version           — check version"
echo ""
echo -e "${CYAN}Config file:${RESET} $CONFIG_DIR/openclaw.json"
echo -e "${CYAN}Docs:${RESET}        https://docs.openclaw.ai"
echo ""
echo -e "${YELLOW}Reload your shell to apply PATH changes:${RESET}"
echo "  source ~/.bashrc"
echo ""
