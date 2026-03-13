#!/bin/bash
# Start LiteLLM Proxy for Antigravity Control Plane

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPS_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$OPS_DIR/.env"
CONFIG_FILE="$SCRIPT_DIR/config.yaml"

if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
    echo "✅ Environment variables loaded."
else
    echo "⚠️ Warning: .env file not found at $ENV_FILE"
fi

echo "🚀 Starting LiteLLM Proxy on port 8000..."
echo "📍 Config: $CONFIG_FILE"

# Run litellm from venv
source "$OPS_DIR/litellm/venv/bin/activate"
litellm --config "$CONFIG_FILE" --port 8000
