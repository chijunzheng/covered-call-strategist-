"""Telegram message handlers for the Covered Call Strategist bot."""

import re
import logging
from telegram import Update
from telegram.constants import ParseMode

from src.tools.strategy_tools import run_covered_call_strategy
from src.telegram_bot.firestore_client import FirestoreClient
from src.telegram_bot.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# Initialize clients
db = FirestoreClient()
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)


def parse_stock_request(text: str) -> tuple[str, int] | None:
    """Parse user message for ticker and shares.

    Supported formats:
    - "AAPL 500 shares"
    - "500 shares of AAPL"
    - "AAPL 500"
    - "I have 500 shares of AAPL"

    Args:
        text: User message text.

    Returns:
        Tuple of (ticker, shares) or None if not parseable.
    """
    text = text.upper().strip()

    # Pattern 1: "TICKER NUM shares" or "TICKER NUM"
    pattern1 = r"([A-Z]{1,5})\s+(\d+)\s*(?:SHARES?)?"
    match1 = re.search(pattern1, text)
    if match1:
        return match1.group(1), int(match1.group(2))

    # Pattern 2: "NUM shares of TICKER"
    pattern2 = r"(\d+)\s*(?:SHARES?\s+(?:OF\s+)?)?([A-Z]{1,5})"
    match2 = re.search(pattern2, text)
    if match2:
        return match2.group(2), int(match2.group(1))

    # Pattern 3: "I have NUM shares of TICKER"
    pattern3 = r"(?:I\s+HAVE\s+)?(\d+)\s*SHARES?\s+(?:OF\s+)?([A-Z]{1,5})"
    match3 = re.search(pattern3, text)
    if match3:
        return match3.group(2), int(match3.group(1))

    return None


def format_for_telegram(text: str) -> str:
    """Format the recommendation text for Telegram markdown.

    Args:
        text: Raw recommendation text.

    Returns:
        Telegram-safe markdown text.
    """
    # Telegram uses a subset of Markdown
    # The recommendation already uses Markdown formatting
    # Just ensure we don't have unsupported elements
    return text


async def handle_start(update: Update, context) -> None:
    """Handle /start command."""
    user = update.effective_user
    logger.info(f"Start command from user {user.id}")

    welcome_message = (
        "👋 *Welcome to the Covered Call Strategist!*\n\n"
        "I help you find the optimal covered call options strategy "
        "to maximize premium income.\n\n"
        "*How to use:*\n"
        "Just tell me your stock ticker and number of shares.\n\n"
        "*Examples:*\n"
        "• `AAPL 500 shares`\n"
        "• `I have 200 shares of MSFT`\n"
        "• `NVDA 1000`\n\n"
        "*Commands:*\n"
        "• /help - Show this help message\n"
        "• /clear - Clear conversation history\n\n"
        "⚠️ *Note:* Shares must be a multiple of 100 (each option contract = 100 shares)."
    )

    await update.message.reply_text(
        welcome_message,
        parse_mode=ParseMode.MARKDOWN,
    )


async def handle_help(update: Update, context) -> None:
    """Handle /help command."""
    await handle_start(update, context)


async def handle_clear(update: Update, context) -> None:
    """Handle /clear command to reset conversation history."""
    user = update.effective_user
    logger.info(f"Clear command from user {user.id}")

    db.clear_conversation(str(user.id), platform="telegram")

    await update.message.reply_text(
        "🗑️ Conversation history cleared. Send a new stock analysis request!",
        parse_mode=ParseMode.MARKDOWN,
    )


async def handle_message(update: Update, context) -> None:
    """Handle incoming text messages."""
    user = update.effective_user
    text = update.message.text
    logger.info(f"Message from user {user.id}: {text[:50]}...")

    # Check if user is allowed
    if not db.is_telegram_user_allowed(user.id):
        await update.message.reply_text(
            "⛔ Sorry, you are not authorized to use this bot.\n\n"
            "Please contact the administrator to request access.",
        )
        logger.warning(f"Unauthorized access attempt from user {user.id}")
        return

    # Check rate limit
    allowed, wait_seconds = rate_limiter.is_allowed(str(user.id), platform="telegram")
    if not allowed:
        await update.message.reply_text(
            f"⏳ Rate limit exceeded. Please wait {wait_seconds} seconds before trying again.\n\n"
            f"Limit: 10 requests per minute.",
        )
        logger.warning(f"Rate limit exceeded for user {user.id}")
        return

    # Store user message in history
    db.add_message(str(user.id), "user", text, platform="telegram")

    # Send typing indicator
    await update.message.chat.send_action("typing")

    # Parse the request
    parsed = parse_stock_request(text)

    if not parsed:
        response = (
            "🤔 I couldn't understand your request.\n\n"
            "*Please try one of these formats:*\n"
            "• `AAPL 500 shares`\n"
            "• `I have 200 shares of MSFT`\n"
            "• `NVDA 1000`\n\n"
            "Remember: shares must be a multiple of 100."
        )
        db.add_message(str(user.id), "assistant", response, platform="telegram")
        await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
        return

    ticker, shares = parsed
    logger.info(f"Parsed request: {ticker} with {shares} shares")

    # Validate shares
    if shares <= 0 or shares % 100 != 0:
        response = (
            f"⚠️ Invalid number of shares: {shares}\n\n"
            "Shares must be a positive multiple of 100 "
            "(each option contract covers 100 shares)."
        )
        db.add_message(str(user.id), "assistant", response, platform="telegram")
        await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
        return

    # Run the covered call strategy
    try:
        result = run_covered_call_strategy(ticker, shares)

        if result.get("error"):
            response = f"❌ {result['formatted_text']}"
        else:
            response = result["formatted_text"]

        # Store response in history
        db.add_message(str(user.id), "assistant", response, platform="telegram")

        # Split long messages if needed (Telegram limit is 4096 chars)
        if len(response) > 4000:
            # Split at logical breaks
            parts = split_long_message(response)
            for i, part in enumerate(parts):
                await update.message.reply_text(
                    part,
                    parse_mode=ParseMode.MARKDOWN,
                )
        else:
            await update.message.reply_text(
                response,
                parse_mode=ParseMode.MARKDOWN,
            )

    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        response = (
            "❌ An error occurred while processing your request.\n\n"
            "Please try again later or contact support."
        )
        db.add_message(str(user.id), "assistant", response, platform="telegram")
        await update.message.reply_text(response)


def split_long_message(text: str, max_length: int = 4000) -> list[str]:
    """Split a long message into parts for Telegram.

    Args:
        text: The full message text.
        max_length: Maximum length per part.

    Returns:
        List of message parts.
    """
    if len(text) <= max_length:
        return [text]

    parts = []
    current = ""

    # Split by double newlines (paragraphs)
    paragraphs = text.split("\n\n")

    for para in paragraphs:
        if len(current) + len(para) + 2 <= max_length:
            if current:
                current += "\n\n" + para
            else:
                current = para
        else:
            if current:
                parts.append(current)
            # If single paragraph is too long, split by lines
            if len(para) > max_length:
                lines = para.split("\n")
                current = ""
                for line in lines:
                    if len(current) + len(line) + 1 <= max_length:
                        if current:
                            current += "\n" + line
                        else:
                            current = line
                    else:
                        if current:
                            parts.append(current)
                        current = line
            else:
                current = para

    if current:
        parts.append(current)

    return parts
