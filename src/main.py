"""CLI entry point for the Covered Call Strategist agent."""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv


def print_welcome():
    """Print welcome message and usage instructions."""
    print("\n" + "=" * 60)
    print("  COVERED CALL STRATEGIST")
    print("  Maximize your covered call premium income")
    print("=" * 60)
    print("\nHow to use:")
    print("  - Tell me a stock and how many shares you own")
    print("  - Example: 'I have 500 shares of AAPL'")
    print("  - Example: 'MSFT 300 shares'")
    print("\nI'll find the best covered call option to maximize your")
    print("annualized premium yield.")
    print("\nType 'quit' or 'exit' to end the conversation.")
    print("Press Ctrl+C to exit at any time.")
    print("-" * 60 + "\n")


async def main():
    """Main entry point for the CLI."""
    # Load environment variables
    load_dotenv()

    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY environment variable not set.")
        print("Please create a .env file with your Google API key:")
        print("  GOOGLE_API_KEY=your_api_key_here")
        sys.exit(1)

    # Import after environment is loaded
    from src.app import run_conversation, send_message

    print_welcome()

    # Start a new session
    user_id = "cli_user"
    session = await run_conversation(user_id=user_id)
    session_id = session.id

    debug = os.getenv("ADK_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}
    if not debug:
        logging.getLogger("google.genai").setLevel(logging.ERROR)
        logging.getLogger("google_genai").setLevel(logging.ERROR)

    print("Strategist: Hello! I'm ready to help you find the best covered call strategy.")
    print("            What stock do you own and how many shares?\n")

    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            if not user_input:
                continue

            # Check for exit commands
            if user_input.lower() in ["quit", "exit", "q", "bye"]:
                print("\nStrategist: Goodbye! Happy trading!")
                break

            # Send message and get response
            print("\nStrategist: Analyzing...\n")
            response = await send_message(session_id, user_id, user_input, debug=debug)

            if response:
                print(f"Strategist: {response}\n")
            else:
                print("Strategist: I encountered an issue processing your request. Please try again.\n")

        except KeyboardInterrupt:
            print("\n\nStrategist: Goodbye! Happy trading!")
            break
        except EOFError:
            print("\n\nStrategist: Goodbye! Happy trading!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("Please try again.\n")


if __name__ == "__main__":
    asyncio.run(main())
