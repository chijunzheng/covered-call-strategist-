"""Debug script for testing ADK setup."""

import asyncio
import os
from dotenv import load_dotenv
import traceback

load_dotenv()

async def test_simple_agent():
    """Test a simple agent to debug ADK issues."""
    from google.adk.agents import LlmAgent
    from google.adk.apps import App
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai.types import UserContent

    # Create a simple test agent
    test_agent = LlmAgent(
        name="test",
        description="A simple test agent",
        model="gemini-2.0-flash",
        instruction="You are a helpful assistant. Just say hello and acknowledge the user's message.",
    )

    app = App(name="test_app", root_agent=test_agent)
    session_service = InMemorySessionService()
    runner = Runner(app=app, session_service=session_service)

    # Create session
    session = await session_service.create_session(
        app_name="test_app",
        user_id="test_user",
    )

    print(f"Session created: {session.id}")
    print("Sending test message...")

    try:
        # Use UserContent for ADK 1.x
        user_message = UserContent("Hello, I have 100 shares of AAPL")

        async for event in runner.run_async(
            session_id=session.id,
            user_id="test_user",
            new_message=user_message,
        ):
            print(f"Event type: {type(event).__name__}")
            print(f"Event: {event}")
            print("---")
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not set")
    else:
        print(f"API Key set: {os.getenv('GOOGLE_API_KEY')[:10]}...")
        asyncio.run(test_simple_agent())
