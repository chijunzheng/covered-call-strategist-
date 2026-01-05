#!/bin/bash
# Deploy the Telegram bot to Google Cloud Functions

set -e

# Configuration
FUNCTION_NAME="covered-call-telegram-bot"
REGION="us-central1"
RUNTIME="python311"
MEMORY="512MB"
TIMEOUT="300s"

# Check for required environment variables
if [ -z "$GCP_PROJECT_ID" ]; then
    echo "Error: GCP_PROJECT_ID environment variable is required"
    exit 1
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "Error: TELEGRAM_BOT_TOKEN environment variable is required"
    exit 1
fi

if [ -z "$GOOGLE_API_KEY" ]; then
    echo "Error: GOOGLE_API_KEY environment variable is required"
    exit 1
fi

echo "Deploying to project: $GCP_PROJECT_ID"
echo "Function name: $FUNCTION_NAME"
echo "Region: $REGION"

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Deploy the Cloud Function
gcloud functions deploy "$FUNCTION_NAME" \
    --project="$GCP_PROJECT_ID" \
    --region="$REGION" \
    --runtime="$RUNTIME" \
    --memory="$MEMORY" \
    --timeout="$TIMEOUT" \
    --trigger-http \
    --allow-unauthenticated \
    --entry-point=telegram_webhook \
    --source=. \
    --set-env-vars="TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN,GOOGLE_API_KEY=$GOOGLE_API_KEY" \
    --gen2

echo ""
echo "✅ Deployment complete!"
echo ""

# Get the function URL
FUNCTION_URL=$(gcloud functions describe "$FUNCTION_NAME" \
    --project="$GCP_PROJECT_ID" \
    --region="$REGION" \
    --format="value(serviceConfig.uri)" \
    --gen2)

echo "Function URL: $FUNCTION_URL"
echo ""
echo "Now set the Telegram webhook with:"
echo ""
echo "  curl -X POST \"https://api.telegram.org/bot\$TELEGRAM_BOT_TOKEN/setWebhook?url=$FUNCTION_URL\""
echo ""
