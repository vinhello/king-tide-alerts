#!/bin/bash
# Installs git pre-commit and commit-msg hooks.
# Called from setup-container.sh, but can also be run manually.

set -e
WORKSPACE="${1:-/workspace}"
HOOKS_DIR="$WORKSPACE/.git/hooks"

if [ ! -d "$WORKSPACE/.git" ]; then
  echo "Error: $WORKSPACE is not a git repository"
  exit 1
fi

echo "Installing git hooks into $HOOKS_DIR..."

# ── pre-commit ────────────────────────────────────────────
cat > "$HOOKS_DIR/pre-commit" << 'HOOK'
#!/bin/bash
# Pre-commit hook: blocks direct commits to main/master, runs linters.

set -e

BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")

# Block direct commits to protected branches
if [[ "$BRANCH" == "main" || "$BRANCH" == "master" ]]; then
  echo ""
  echo "╔════════════════════════════════════════════════════╗"
  echo "║  ❌  Direct commits to '$BRANCH' are not allowed.  ║"
  echo "║  Create a feature branch:                          ║"
  echo "║  git checkout -b feature/your-description          ║"
  echo "╚════════════════════════════════════════════════════╝"
  echo ""
  exit 1
fi

# Run backend linter (ruff)
if command -v ruff &>/dev/null && [ -d backend ]; then
  if ruff check backend/; then
    echo "  ✓ Backend lint passed (ruff)"
  else
    echo ""
    echo "  ❌ Backend lint errors. Run: cd backend && ruff check --fix ."
    echo ""
    exit 1
  fi
fi

# Run frontend linter (eslint)
if [ -f frontend/package.json ]; then
  if (cd frontend && npm run lint --silent 2>/dev/null); then
    echo "  ✓ Frontend lint passed (eslint)"
  else
    echo ""
    echo "  ❌ Frontend lint errors. Run: cd frontend && npm run lint"
    echo ""
    exit 1
  fi
fi

echo "  ✓ Pre-commit checks passed"
exit 0
HOOK

# ── commit-msg ────────────────────────────────────────────
cat > "$HOOKS_DIR/commit-msg" << 'HOOK'
#!/bin/bash
# Enforce conventional commit format:
# feat|fix|chore|docs|test|refactor|style: message

COMMIT_MSG_FILE="$1"
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

# Allow merge commits
if echo "$COMMIT_MSG" | grep -qE "^Merge "; then
  exit 0
fi

# Check for conventional commit format
if echo "$COMMIT_MSG" | grep -qE "^(feat|fix|chore|docs|test|refactor|style|perf|ci|build|revert)(\(.+\))?: .+"; then
  exit 0
fi

echo ""
echo "  ❌ Commit message format invalid."
echo ""
echo "  Use conventional commits:"
echo "    feat: add tide prediction caching"
echo "    fix: resolve NOAA API timeout handling"
echo "    chore: update Python dependencies"
echo "    docs: add API documentation"
echo ""
exit 1
HOOK

# Make hooks executable
chmod +x "$HOOKS_DIR/pre-commit"
chmod +x "$HOOKS_DIR/commit-msg"

echo "  ✓ pre-commit hook installed"
echo "  ✓ commit-msg hook installed"
