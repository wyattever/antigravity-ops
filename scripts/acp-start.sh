#!/bin/bash

# Antigravity Control Plane (ACP) - Silent Startup
# Responsibility: Launch LiteLLM gateway and verify health.

OPS_DIR="/Users/a00288946/Agents/antigravity-ops"
LOG_FILE="$OPS_DIR/litellm/litellm.log"

echo "🛰️  Starting Antigravity Control Plane..."

# 1. Clear existing port 8000
lsof -i :8000 -t | xargs kill -9 > /dev/null 2>&1 || true

# 2. Source env keys
if [ -f "$OPS_DIR/.env" ]; then
    source "$OPS_DIR/.env"
fi

# 3. Launch LiteLLM in background
source "$OPS_DIR/litellm/venv/bin/activate"
nohup litellm --config "$OPS_DIR/litellm/config.yaml" --port 8000 > "$LOG_FILE" 2>&1 &

# 4. Perform Health Check with Retry (max 10s)
echo "⏳ Waiting for Gateway readiness..."
COUNT=0
while [ $COUNT -lt 10 ]; do
    if curl -s http://localhost:8000/health/readiness | grep -q '"status":"healthy"'; then
        echo "✅ Gateway is LIVE."
        echo "------------------------------------------------"
        echo "🛰️  Antigravity Control Plane running."
        echo "------------------------------------------------"
        echo "👉 SETTING REMINDER:"
        echo "1. API Base: http://localhost:8000"
        echo "2. API Key: sk-antigravity-admin"
        echo "3. Model: antigravity-smart"
        echo "------------------------------------------------"
        exit 0
    fi
    sleep 1
    COUNT=$((COUNT+1))
done

echo "❌ Error: ACP Gateway failed to start within 10 seconds."
echo "Check logs at: $LOG_FILE"
exit 1
