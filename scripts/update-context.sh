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
TEST_COUNT=$(cd "$REPO_ROOT" && .venv/bin/python -m pytest tests/ --collect-only -q 2>/dev/null | awk '/tests? collected/ {print $1; found=1} END {if (!found) print "?"}')

escape_sed_replacement() {
  printf '%s' "$1" | sed 's/[\/&|]/\\&/g'
}

BRANCH_ESC=$(escape_sed_replacement "$BRANCH")
LAST_COMMIT_ESC=$(escape_sed_replacement "$LAST_COMMIT")
TIMESTAMP_ESC=$(escape_sed_replacement "$TIMESTAMP")

# Update CONTEXT.md header
sed -i.bak \
  -e "s|^\*\*Last updated:\*\*.*|\*\*Last updated:\*\* $TIMESTAMP_ESC|" \
  -e "s|^\*\*Branch:\*\*.*|\*\*Branch:\*\* \`$BRANCH_ESC\`|" \
  -e "s|^\*\*Last commit:\*\*.*|\*\*Last commit:\*\* \`$LAST_COMMIT_ESC\`|" \
  CONTEXT.md

rm -f CONTEXT.md.bak

echo "✅ CONTEXT.md updated:"
echo "   Branch: $BRANCH"
echo "   Last commit: $LAST_COMMIT"
echo "   Tests: $TEST_COUNT"
echo "   Timestamp: $TIMESTAMP"
