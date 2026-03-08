#!/bin/bash
# Runs once after the container is created (postCreateCommand).
# Sets up firewall, git hooks, and project dependencies.

# Fix volume mount ownership — Docker initialises named volumes as root
sudo chown -R node:node /home/node/.config 2>/dev/null || true
sudo chown -R node:node /home/node/.npm 2>/dev/null || true
sudo chown -R node:node /home/node/.cache 2>/dev/null || true

set -e
WORKSPACE="/workspace"

echo "🚀 Setting up King Tide Alert dev environment..."

# ── 1. Firewall ──────────────────────────────────────────
echo ""
echo "Step 1/5: Initialising firewall..."
bash "$WORKSPACE/.devcontainer/init-firewall.sh"

# ── 2. Git configuration ─────────────────────────────────
echo ""
echo "Step 2/5: Configuring git..."

# Ensure we're in a git repo before installing hooks
if [ -d "$WORKSPACE/.git" ]; then
  bash "$WORKSPACE/.devcontainer/install-git-hooks.sh"
  echo "  ✓ Git hooks installed"
else
  echo "  ⚠ No .git directory found — skipping git hooks"
  echo "    Run .devcontainer/install-git-hooks.sh after git init"
fi

# ── 3. Make Claude hooks executable ──────────────────────
echo ""
echo "Step 3/5: Making Claude hooks executable..."
if [ -d "$WORKSPACE/.claude/hooks" ] && ls "$WORKSPACE/.claude/hooks/"*.sh &>/dev/null; then
  chmod +x "$WORKSPACE/.claude/hooks/"*.sh
  echo "  ✓ Hooks marked executable"
fi

# ── 4. Install project dependencies ──────────────────────
echo ""
echo "Step 4/5: Installing dependencies..."

# Check common locations for requirements.txt
REQ_FILE=""
for path in "requirements.txt" "backend/requirements.txt" "app/requirements.txt"; do
  if [ -f "$WORKSPACE/$path" ]; then
    REQ_FILE="$WORKSPACE/$path"
    break
  fi
done

if [ -f "$WORKSPACE/package.json" ]; then
  cd "$WORKSPACE" && npm install --silent
  echo "  ✓ npm install complete"
fi

if [ -n "$REQ_FILE" ]; then
  pip install -r "$REQ_FILE" -q --no-warn-script-location
  echo "  ✓ pip install complete ($REQ_FILE)"
elif [ -f "$WORKSPACE/pyproject.toml" ]; then
  pip install -e "$WORKSPACE" -q --no-warn-script-location
  echo "  ✓ pip install complete (pyproject.toml)"
else
  echo "  ⚠ No Python dependencies file found — skipping"
fi

# ── 5. Done ───────────────────────────────────────────────
echo ""
echo "Step 5/5: Final checks..."

# Verify Claude Code is available
if command -v claude &>/dev/null; then
  echo "  ✓ Claude Code: $(claude --version 2>/dev/null || echo 'installed')"
else
  echo "  ✗ Claude Code not found — run: npm install -g @anthropic-ai/claude-code"
fi

# Verify gh CLI
if command -v gh &>/dev/null; then
  echo "  ✓ GitHub CLI: $(gh --version | head -1)"
else
  echo "  ⚠ GitHub CLI not found"
fi

# Verify Python
if command -v python &>/dev/null; then
  echo "  ✓ Python: $(python --version)"
else
  echo "  ⚠ Python not found"
fi

echo ""
echo "✅ Container setup complete!"
echo ""
echo "Next steps:"
echo "  1. Run 'claude' to start Claude Code"
echo "  2. Run 'gh auth login' to authenticate with GitHub"
echo "  3. Copy backend/.env.example to backend/.env and fill in API keys"
echo "  4. cd backend && uvicorn app.main:app --reload    (start backend on :8000)"
echo "  5. cd frontend && npm run dev                      (start frontend on :5173)"
