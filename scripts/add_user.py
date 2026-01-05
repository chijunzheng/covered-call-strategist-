#!/usr/bin/env python3
"""Add a user to the Firestore allowlist."""

import os
import sys
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.telegram_bot.firestore_client import FirestoreClient


def main():
    parser = argparse.ArgumentParser(description="Add a user to the allowlist")
    parser.add_argument(
        "phone_number",
        help="Phone number with country code (e.g., +1234567890)",
    )
    parser.add_argument(
        "--telegram-id",
        type=int,
        help="Telegram user ID (optional, can be linked later)",
    )
    parser.add_argument(
        "--name",
        help="User name for reference (optional)",
    )

    args = parser.parse_args()

    db = FirestoreClient()
    success = db.add_allowed_user(
        phone_number=args.phone_number,
        telegram_id=args.telegram_id,
        name=args.name,
    )

    if success:
        print(f"✅ User added: {args.phone_number}")
        if args.telegram_id:
            print(f"   Telegram ID: {args.telegram_id}")
        if args.name:
            print(f"   Name: {args.name}")
    else:
        print("❌ Failed to add user")
        sys.exit(1)


if __name__ == "__main__":
    main()
