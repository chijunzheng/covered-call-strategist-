"""ADK App and Runner setup for the Covered Call Strategist."""

from google.adk.apps import App
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import UserContent

from src.agents.coordinator import coordinator_agent
from src.agents.recommender import recommender_agent


# Create the ADK App with the coordinator as root agent
app = App(
    name="covered_call_strategist",
    root_agent=coordinator_agent,
)

# Session service for managing conversation state
session_service = InMemorySessionService()

# Runner for executing the agent
runner = Runner(
    app=app,
    session_service=session_service,
)


async def run_conversation(user_id: str = "default_user"):
    """Run an interactive conversation with the Covered Call Strategist.

    Args:
        user_id: Unique identifier for the user session.

    Returns:
        The session object for the conversation.
    """
    session = await session_service.create_session(
        app_name="covered_call_strategist",
        user_id=user_id,
    )
    return session


async def send_message(session_id: str, user_id: str, message: str, debug: bool = False) -> str:
    """Send a message to the agent and get the response.

    Args:
        session_id: The session ID from run_conversation.
        user_id: The user ID for the session.
        message: The user's message.
        debug: If True, print event debug info.

    Returns:
        The agent's response text.
    """
    response_by_author = {}
    final_author = None

    visible_authors = {
        coordinator_agent.name,
        recommender_agent.name,
    }

    # Convert string message to UserContent for ADK 1.x
    user_content = UserContent(message)

    async for event in runner.run_async(
        session_id=session_id,
        user_id=user_id,
        new_message=user_content,
    ):
        if debug:
            event_author = getattr(event, "author", "UNKNOWN")
            is_final = bool(getattr(event, "is_final_response", lambda: False)())
            has_content = bool(getattr(event, "content", None))
            parts = getattr(getattr(event, "content", None), "parts", []) or []
            part_types = []
            for part in parts:
                if getattr(part, "function_call", None):
                    part_types.append("function_call")
                elif getattr(part, "function_response", None):
                    part_types.append("function_response")
                elif getattr(part, "text", None):
                    part_types.append("text")
                else:
                    part_types.append("other")
            actions = getattr(event, "actions", None)
            state_delta = getattr(actions, "state_delta", None) if actions else None
            transfer_to = getattr(actions, "transfer_to_agent", None) if actions else None
            print(
                "DEBUG event: "
                f"author={event_author} "
                f"final={is_final} "
                f"content={has_content} "
                f"parts={part_types} "
                f"transfer={transfer_to} "
                f"state_delta={bool(state_delta)}"
            )

        if event.author not in visible_authors:
            if debug:
                print(f"DEBUG skipping author: {event.author}")
            continue

        # Handle different event types from ADK 1.x
        if hasattr(event, 'content') and event.content:
            content = event.content
            if hasattr(content, 'parts') and content.parts:
                for part in content.parts:
                    if hasattr(part, 'text') and part.text:
                        # Skip thought parts if marked
                        if not getattr(part, 'thought', False):
                            response_by_author.setdefault(event.author, "")
                            response_by_author[event.author] += part.text
        elif hasattr(event, 'text') and event.text:
            response_by_author.setdefault(event.author, "")
            response_by_author[event.author] += event.text

        if event.is_final_response():
            final_author = event.author

    if final_author and response_by_author.get(final_author):
        return response_by_author[final_author]

    if response_by_author:
        return (
            response_by_author.get(recommender_agent.name)
            or response_by_author.get(coordinator_agent.name)
            or next(iter(response_by_author.values()))
        )

    return ""
