#!/bin/bash
# Auto-update CONTEXT.md with current git state and test count
# Usage: ./scripts/update-context.sh

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# Get current state
BRANCH=$(git branch --show-current)
LAST_COMMIT=$(git log -1 --format="%h — %s")
TIMESTAMP=$(date +"%Y-%m-%d %H:%M")
TEST_COUNT=$(cd "$REPO_ROOT" && .venv/bin/python -m pytest tests/ --collect-only -q 2>/dev/null | tail -1 | grep -oE '[0-9]+' || echo "?")

# Update CONTEXT.md header
sed -i.bak \
  -e "s/^\*\*Last updated:\*\*.*/\*\*Last updated:\*\* $TIMESTAMP/" \
  -e "s/^\*\*Branch:\*\*.*/\*\*Branch:\*\* \`$BRANCH\`/" \
  -e "s/^\*\*Last commit:\*\*.*/\*\*Last commit:\*\* \`$LAST_COMMIT\`/" \
  CONTEXT.md

rm -f CONTEXT.md.bak

echo "✅ CONTEXT.md updated:"
echo "   Branch: $BRANCH"
echo "   Last commit: $LAST_COMMIT"
echo "   Tests: $TEST_COUNT"
echo "   Timestamp: $TIMESTAMP"
