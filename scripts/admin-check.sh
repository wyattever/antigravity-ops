#!/usr/bin/env bash
# Admin check: dry-run report of server vs local otter/admin (no local changes).
# Server: webaim-deploy:/var/websites/webaim/htdocs/otter/admin/
# Local:  Projects/otter/admin (or OTTER_ADMIN_LOCAL).
# Usage: bash scripts/admin-check.sh [optional: path to cursor-ops]

set -euo pipefail

OTTER_ADMIN_LOCAL="${OTTER_ADMIN_LOCAL:-$HOME/Projects/otter/admin}"
REMOTE="webaim-deploy:/var/websites/webaim/htdocs/otter/admin/"

echo "Admin check (dry-run): server → local"
echo "  Remote:  $REMOTE"
echo "  Local:   $OTTER_ADMIN_LOCAL"
echo ""

if [ ! -d "$OTTER_ADMIN_LOCAL" ]; then
  echo "Local directory does not exist: $OTTER_ADMIN_LOCAL"
  exit 1
fi

rsync -avzn --delete \
  --exclude='.git' --exclude='*.log' \
  "$REMOTE" \
  "$OTTER_ADMIN_LOCAL/"

echo ""
echo "Done (no files changed). Run admin-sync with --execute to apply."
