#!/usr/bin/env bash
# Admin check with diffs: dry-run + list of updated files + unified diff of changed code.
# Server: webaim-deploy:/var/websites/webaim/htdocs/otter/admin/
# Local:  Projects/otter/admin (or OTTER_ADMIN_LOCAL).
# Writes report to stdout and optionally to a file (ADMIN_CHECK_REPORT_PATH).
# Usage: bash scripts/admin-check-with-diffs.sh

set -euo pipefail

OTTER_ADMIN_LOCAL="${OTTER_ADMIN_LOCAL:-$HOME/Projects/otter/admin}"
REMOTE_HOST="webaim-deploy"
REMOTE_BASE="/var/websites/webaim/htdocs/otter/admin"
REMOTE_RSYNC="${REMOTE_HOST}:${REMOTE_BASE}/"
REPORT_PATH="${ADMIN_CHECK_REPORT_PATH:-}"
if [[ -z "$REPORT_PATH" && -n "${CURSOR_OPS:-}" ]]; then
  REPORT_PATH="${CURSOR_OPS}/relocate/docs/status/admin-check-report-$(date +%Y-%m-%d-%H%M%S).txt"
  mkdir -p "$(dirname "$REPORT_PATH")"
fi

# Optional: write report to file (e.g. relocate/docs/status/)
if [[ -n "$REPORT_PATH" ]]; then
  exec 3> >(tee "$REPORT_PATH")
else
  exec 3>&1
fi

echo "## ADMIN_CHECK_REPORT" >&3
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >&3
echo "Remote: $REMOTE_RSYNC" >&3
echo "Local: $OTTER_ADMIN_LOCAL" >&3
echo "" >&3

if [[ ! -d "$OTTER_ADMIN_LOCAL" ]]; then
  echo "ERROR: Local directory does not exist: $OTTER_ADMIN_LOCAL" >&3
  exit 1
fi

# 1) Get itemized dry-run output
RSYNC_OUT=$(mktemp -t admin-check-rsync.XXXXXX)
trap 'rm -f "$RSYNC_OUT"' EXIT

rsync -avzn --delete \
  --exclude='.git' --exclude='*.log' \
  --out-format='%i %n' \
  "$REMOTE_RSYNC" \
  "$OTTER_ADMIN_LOCAL/" 2>/dev/null > "$RSYNC_OUT" || true

UPDATED_FILES=()
DELETED_FILES=()

while IFS= read -r line || [[ -n "$line" ]]; do
  if [[ "$line" == *"*deleting"* ]]; then
    path="${line#*deleting }"
    path="${path#"${path%%[! ]*}"}"   # trim leading spaces
    [[ -n "$path" ]] && DELETED_FILES+=("$path")
  elif [[ "$line" == ">"* ]]; then
    if [[ "$line" =~ ^[^\ ]+\ (.+)$ ]]; then
      path="${BASH_REMATCH[1]}"
      [[ -n "$path" && "$path" != */ ]] && UPDATED_FILES+=("$path")
    fi
  fi
done < "$RSYNC_OUT"

# If no itemized output, try parsing verbose output
if [[ ${#UPDATED_FILES[@]} -eq 0 && ${#DELETED_FILES[@]} -eq 0 ]]; then
  rsync -avzn --delete \
    --exclude='.git' --exclude='*.log' \
    "$REMOTE_RSYNC" \
    "$OTTER_ADMIN_LOCAL/" 2>&1 | while IFS= read -r line; do
      if [[ "$line" == deleting* ]]; then
        echo "DELETE:${line#deleting }"
      elif [[ -n "$line" && "$line" != /* && "$line" != total* && "$line" != sent* ]]; then
        echo "UPDATE:$line"
      fi
    done > "$RSYNC_OUT"
  while IFS= read -r line; do
    [[ "$line" == DELETE:* ]] && DELETED_FILES+=("${line#DELETE:}")
    [[ "$line" == UPDATE:* ]] && UPDATED_FILES+=("${line#UPDATE:}")
  done < "$RSYNC_OUT"
fi

echo "## SUMMARY" >&3
echo "Updated/added: ${#UPDATED_FILES[@]}  |  Would delete: ${#DELETED_FILES[@]}" >&3
echo "" >&3
echo "## UPDATED_FILES" >&3
for f in "${UPDATED_FILES[@]}"; do
  echo "- \`$f\`" >&3
done
if [[ ${#UPDATED_FILES[@]} -eq 0 ]]; then
  echo "- (none)" >&3
fi
echo "" >&3
echo "## DELETED_FILES" >&3
for f in "${DELETED_FILES[@]}"; do
  echo "- \`$f\`" >&3
done
if [[ ${#DELETED_FILES[@]} -eq 0 ]]; then
  echo "- (none)" >&3
fi
echo "" >&3
echo "## DIFFS (server vs local; use for targeted code analysis)" >&3

DIFF_COUNT=0
TEMP_FILES=()
for relpath in "${UPDATED_FILES[@]}"; do
  local_file="${OTTER_ADMIN_LOCAL}/${relpath}"
  if [[ -d "$local_file" ]]; then
    continue
  fi
  server_file=$(mktemp -t "admin-srv-XXXXXX")
  TEMP_FILES+=("$server_file")
  if ssh -o ConnectTimeout=10 "$REMOTE_HOST" "cat '${REMOTE_BASE}/${relpath}'" 2>/dev/null > "$server_file"; then
    if [[ ! -f "$local_file" ]]; then
      echo "" >&3
      echo "### FILE: \`$relpath\` (new on server)" >&3
      echo "\`\`\`" >&3
      head -80 "$server_file" | sed 's/^/  /' >&3
      echo "  ..." >&3
      echo "\`\`\`" >&3
      ((DIFF_COUNT++)) || true
    elif ! diff -q "$local_file" "$server_file" >/dev/null 2>&1; then
      echo "" >&3
      echo "### FILE: \`$relpath\`" >&3
      echo "\`\`\`diff" >&3
      diff -u "$local_file" "$server_file" >&3 || true
      echo "\`\`\`" >&3
      ((DIFF_COUNT++)) || true
    fi
  fi
done
for f in "${TEMP_FILES[@]}"; do rm -f "$f"; done

if [[ $DIFF_COUNT -eq 0 && ${#UPDATED_FILES[@]} -eq 0 ]]; then
  echo "(no changes)" >&3
fi

echo "" >&3
echo "## AGENT_ACTION" >&3
echo "After reading this report, perform targeted code analysis on the changes above and return a **concise summary of changes** to chat (e.g. which files changed, what was added/fixed/removed, and any impact)." >&3
echo "" >&3
echo "---" >&3
echo "End of report. Run \`admin-sync --execute\` to apply." >&3

if [[ -n "$REPORT_PATH" ]]; then
  echo ""
  echo "Report written to: $REPORT_PATH"
fi
