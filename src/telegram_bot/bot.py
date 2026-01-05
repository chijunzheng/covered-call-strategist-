"""Main Telegram bot configuration and application setup."""

import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from src.telegram_bot.handlers import (
    handle_start,
    handle_help,
    handle_clear,
    handle_message,
)

logger = logging.getLogger(__name__)


def create_application() -> Application:
    """Create and configure the Telegram bot application.

    Returns:
        Configured Telegram Application instance.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

    # Create application
    application = Application.builder().token(token).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(CommandHandler("help", handle_help))
    application.add_handler(CommandHandler("clear", handle_clear))

    # Add message handler for text messages
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    logger.info("Telegram bot application created successfully")
    return application


async def process_update(update_data: dict) -> None:
    """Process a single update from Telegram webhook.

    This is the main entry point for Cloud Function webhook handling.

    Args:
        update_data: The raw update data from Telegram.
    """
    application = create_application()

    # Initialize the application for processing
    async with application:
        update = Update.de_json(update_data, application.bot)
        await application.process_update(update)


def run_polling():
    """Run the bot in polling mode (for local development)."""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    application = create_application()
    logger.info("Starting bot in polling mode...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
