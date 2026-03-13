#!/bin/bash
# Version: 1.0.0
# Switch operational context to Gemini API
set -e

ENV_FILE="${AG_HOME:-$HOME/Agents}/antigravity-ops/.env"
CONFIG_DIR="${AG_HOME:-$HOME/Agents}/antigravity-ops/config"
STATE_FILE="$CONFIG_DIR/active-provider.json"

echo "🔄 Switching to Gemini context..."

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: .env file not found at $ENV_FILE"
    exit 1
fi

# Extract key for validation without sourcing into parent shell (not possible from script)
GEMINI_API_KEY=$(grep "GEMINI_API_KEY" "$ENV_FILE" | cut -d'"' -f2)

if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ Error: GEMINI_API_KEY not found in $ENV_FILE"
    exit 1
fi

# Update state file
mkdir -p "$CONFIG_DIR"
echo "{\"provider\": \"gemini\", \"last_switched\": \"$(date)\"}" > "$STATE_FILE"

echo "✅ Gemini API Key found and state updated."
echo "📍 State: $STATE_FILE"

# Quick connectivity test
echo "📡 Testing Google AI Studio connectivity..."
# Try listing models first to verify the key
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://generativelanguage.googleapis.com/v1beta/models?key=$GEMINI_API_KEY")

if [ "$HTTP_STATUS" == "200" ]; then
    echo "🚀 Success: API Key recognized (200 OK)"
else
    echo "⚠️ Error: API Key check failed with HTTP status $HTTP_STATUS"
    echo "This usually means the key is invalid or permissions are incorrect."
    exit 1
fi

echo "=================================="
echo "Next: You can now use '/yolo-full' with Gemini-first priority."
