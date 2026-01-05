"""Google Cloud Function entry point for Telegram webhook.

This file is at the project root for GCP Cloud Functions deployment.
"""

import json
import asyncio
import logging
import functions_framework
from flask import Request

from src.telegram_bot.bot import process_update

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


@functions_framework.http
def telegram_webhook(request: Request):
    """HTTP Cloud Function for Telegram webhook.

    This function receives webhook updates from Telegram and processes them.

    Args:
        request: The Flask request object containing the Telegram update.

    Returns:
        Tuple of (response_body, status_code).
    """
    # Verify request method
    if request.method != "POST":
        logger.warning(f"Invalid request method: {request.method}")
        return "Method not allowed", 405

    # Parse the update
    try:
        update_data = request.get_json(force=True)
    except Exception as e:
        logger.error(f"Failed to parse request JSON: {e}")
        return "Bad request", 400

    if not update_data:
        logger.warning("Empty update received")
        return "No update data", 400

    logger.info(f"Received update: {json.dumps(update_data)[:200]}...")

    # Process the update asynchronously
    try:
        # Create new event loop for Cloud Function environment
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(process_update(update_data))
        finally:
            loop.close()

        return "OK", 200

    except Exception as e:
        logger.error(f"Error processing update: {e}", exc_info=True)
        # Return 200 anyway to prevent Telegram from retrying
        # We log the error for debugging
        return "OK", 200


@functions_framework.http
def health_check(request: Request):
    """Health check endpoint.

    Args:
        request: The Flask request object.

    Returns:
        Health status response.
    """
    return {"status": "healthy", "service": "covered-call-strategist-bot"}, 200
