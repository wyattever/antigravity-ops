#!/bin/bash
# scripts/acp-start.sh
# Silently launches LiteLLM proxy and performs health check

set -eo pipefail

OPS_DIR="${AG_HOME:-$HOME/Agents}/antigravity-ops"
LITELLM_DIR="$OPS_DIR/litellm"
LOG_FILE="$LITELLM_DIR/litellm_silent.log"

# 1. Check if already running
if curl -s http://localhost:8000/health/readiness > /dev/null; then
    echo "Antigravity Control Plane running."
    exit 0
fi

# 2. Launch LiteLLM in background
# We use a subshell to ensure it truly detaches
(
    cd "$LITELLM_DIR"
    nohup bash "start-litellm.sh" > "$LOG_FILE" 2>&1 &
)

# 3. Wait for health check
MAX_RETRIES=30
COUNT=0
while ! curl -s http://localhost:8000/health/readiness > /dev/null; do
    sleep 1
    COUNT=$((COUNT+1))
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo "❌ Error: Antigravity Control Plane failed to start within ${MAX_RETRIES}s."
        tail -n 20 "$LOG_FILE"
        exit 1
    fi
done

echo "Antigravity Control Plane running."
