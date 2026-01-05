#!/usr/bin/env python3
"""Run the Telegram bot locally in polling mode for development."""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Validate required environment variables
required_vars = ["TELEGRAM_BOT_TOKEN", "GOOGLE_API_KEY"]
missing = [var for var in required_vars if not os.environ.get(var)]
if missing:
    print(f"Error: Missing required environment variables: {', '.join(missing)}")
    print("Please set them in your .env file.")
    sys.exit(1)

# Run the bot
from src.telegram_bot.bot import run_polling

if __name__ == "__main__":
    print("Starting Telegram bot in local polling mode...")
    print("Press Ctrl+C to stop.")
    run_polling()
