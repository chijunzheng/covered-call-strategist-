---
name: adk-session-management
description: Implement and manage agent session persistence using Google ADK's session service. Use this skill when building ADK agents that need conversation history, state management across interactions, or persistent storage. Triggers for implementing session services, managing session state (app/user/session levels), choosing between InMemory/Database/VertexAI backends, handling session CRUD operations, creating and appending events, working with EventActions for state updates and agent control flow, or implementing multi-agent conversation branching.
---

# ADK Session Management

## Overview

This skill provides guidance for implementing session management in Google ADK agents. Sessions track conversation history and state across user interactions.

## When to Use This Skill

- Adding session persistence to an ADK agent
- Choosing between InMemory, Database, or Vertex AI session backends
- Implementing conversation history that survives restarts
- Managing hierarchical state (app-level, user-level, session-level)
- Setting up database-backed sessions with PostgreSQL, MySQL, SQLite, or Cloud Spanner
- Integrating with Vertex AI Agent Engine for managed sessions
- Filtering or paginating session events
- Sharing state across users or sessions using state prefixes

## Quick Start - Choose Your Backend

| Backend | Use Case | Requirements |
|---------|----------|--------------|
| `InMemorySessionService` | Development/testing | None |
| `DatabaseSessionService` | Production with SQL | `sqlalchemy>=2.0` |
| `VertexAiSessionService` | Vertex AI Agent Engine | GCP project, Vertex AI |

## Implementation Patterns

### Basic Setup

```python
from google.adk.sessions import InMemorySessionService

# Development
session_service = InMemorySessionService()

# Production with database
from google.adk.sessions import DatabaseSessionService
session_service = DatabaseSessionService("postgresql://user:pass@host/db")

# Vertex AI
from google.adk.sessions import VertexAiSessionService
session_service = VertexAiSessionService(
    project="my-project",
    location="us-central1",
    agent_engine_id="123456789"
)
```

### Session CRUD Operations

```python
# Create session
session = await session_service.create_session(
    app_name="my-agent",
    user_id="user-123",
    state={"initial": "value"},  # Optional
    session_id="custom-id"       # Optional (not supported by VertexAI)
)

# Get session
session = await session_service.get_session(
    app_name="my-agent",
    user_id="user-123",
    session_id="session-456",
    config=GetSessionConfig(num_recent_events=50)  # Optional filtering
)

# List sessions
response = await session_service.list_sessions(
    app_name="my-agent",
    user_id="user-123"  # Optional, omit for all users
)

# Delete session
await session_service.delete_session(
    app_name="my-agent",
    user_id="user-123",
    session_id="session-456"
)
```

### State Hierarchy

ADK uses prefixed keys for hierarchical state:

```python
state = {
    "app:config": {...},      # Shared across ALL users (prefix: "app:")
    "user:preferences": {...}, # Shared across user's sessions (prefix: "user:")
    "conversation_turn": 5,    # Session-specific (no prefix)
    "temp:cache": {...}        # Temporary, NOT persisted (prefix: "temp:")
}
```

**State merging order:** app < user < session (session wins on conflicts)

### Integrating with ADK Agent

```python
from google.adk import Agent
from google.adk.sessions import DatabaseSessionService

session_service = DatabaseSessionService("sqlite:///sessions.db")

agent = Agent(
    name="my-agent",
    model="gemini-2.0-flash",
    session_service=session_service,
)

# Runner handles session automatically
async for event in agent.run_async(
    user_id="user-123",
    session_id="session-456",  # Creates if not exists
    user_content="Hello!"
):
    print(event)
```

## Database Service Configuration

### Supported Databases

```python
# SQLite (development)
DatabaseSessionService("sqlite:///sessions.db")

# PostgreSQL (recommended for production)
DatabaseSessionService("postgresql://user:pass@host:5432/dbname")

# MySQL
DatabaseSessionService("mysql+pymysql://user:pass@host:3306/dbname")

# Cloud Spanner
DatabaseSessionService(
    "spanner+spanner:///projects/P/instances/I/databases/D"
)
```

### Database Schema

Tables are auto-created:
- `sessions` - Session metadata, session-level state
- `events` - Conversation events (foreign key to sessions, CASCADE delete)
- `app_states` - Application-wide state
- `user_states` - User-scoped state

## Events

Events are the building blocks of conversation history. Each event represents a single interaction (user message, agent response, function call, etc.).

### Event Structure

```python
from google.adk.events import Event, EventActions
from google.genai import types

# User message event
user_event = Event(
    author="user",
    invocation_id="inv-001",
    content=types.Content(parts=[types.Part(text="Hello!")])
)

# Agent response event with state update
agent_event = Event(
    author="my-agent",
    invocation_id="inv-001",
    content=types.Content(parts=[types.Part(text="Hi there!")]),
    actions=EventActions(
        state_delta={"turn_count": 1}
    )
)

# Append to session
await session_service.append_event(session, user_event)
await session_service.append_event(session, agent_event)
```

### EventActions - Control Flow & State

```python
actions = EventActions(
    # State updates (uses prefixes for scope)
    state_delta={
        "app:global": "value",    # App-wide state
        "user:prefs": "value",    # User-scoped state
        "local": "value"          # Session-only state
    },

    # Agent handoff
    transfer_to_agent="specialist-agent",

    # Escalate to parent
    escalate=True,

    # Track file artifacts
    artifact_delta={"report.pdf": 1},

    # Skip LLM summarization of tool response
    skip_summarization=True,
)
```

### Working with Function Calls

```python
# Check for function calls in an event
func_calls = event.get_function_calls()
for fc in func_calls:
    print(f"Function: {fc.name}, Args: {fc.args}")

# Check for function responses
func_responses = event.get_function_responses()

# Check if event is final (no pending calls)
if event.is_final_response():
    print("Agent turn complete")
```

### Multi-Agent Branching

Use `branch` to isolate sub-agent conversations:

```python
# Sub-agent events use branch to track hierarchy
sub_event = Event(
    author="sub-agent",
    invocation_id="inv-002",
    branch="main-agent.sub-agent",  # Parent.child hierarchy
    content=types.Content(parts=[types.Part(text="Sub-agent response")])
)
```

## Common Patterns

### Resume or Create Session

```python
session = await session_service.get_session(
    app_name=app_name, user_id=user_id, session_id=session_id
)
if not session:
    session = await session_service.create_session(
        app_name=app_name, user_id=user_id, session_id=session_id
    )
```

### Filter Recent Events

```python
from google.adk.sessions.base_session_service import GetSessionConfig

# Last 50 events
config = GetSessionConfig(num_recent_events=50)

# Events after timestamp
config = GetSessionConfig(after_timestamp=1704067200.0)

session = await session_service.get_session(
    app_name="app", user_id="user", session_id="sess",
    config=config
)
```

### Update State via Events

State changes propagate through event actions:

```python
from google.adk.events import Event, EventActions

event = Event(
    author="agent",
    invocation_id="inv-123",
    actions=EventActions(
        state_delta={
            "app:global_setting": "new_value",  # Updates app state
            "user:preference": "dark",           # Updates user state
            "turn_count": 5,                     # Updates session state
        }
    )
)
await session_service.append_event(session, event)
```

## Resources

See [references/api_reference.md](references/api_reference.md) for complete API documentation including all method signatures and implementation details.
