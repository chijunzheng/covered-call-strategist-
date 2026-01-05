#!/bin/bash
# Set the Telegram webhook URL

set -e

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "Error: TELEGRAM_BOT_TOKEN environment variable is required"
    exit 1
fi

if [ -z "$1" ]; then
    echo "Usage: ./set_webhook.sh <webhook_url>"
    echo ""
    echo "Example: ./set_webhook.sh https://us-central1-myproject.cloudfunctions.net/covered-call-telegram-bot"
    exit 1
fi

WEBHOOK_URL="$1"

echo "Setting webhook to: $WEBHOOK_URL"

# Set the webhook
RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
    -d "url=$WEBHOOK_URL")

echo ""
echo "Response: $RESPONSE"

# Check if successful
if echo "$RESPONSE" | grep -q '"ok":true'; then
    echo ""
    echo "✅ Webhook set successfully!"
else
    echo ""
    echo "❌ Failed to set webhook"
    exit 1
fi

# Get webhook info
echo ""
echo "Webhook info:"
curl -s "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo" | python3 -m json.tool
