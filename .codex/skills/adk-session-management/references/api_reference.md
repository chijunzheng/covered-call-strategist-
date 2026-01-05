# ADK Session Management API Reference

## Table of Contents

- [Core Classes](#core-classes) - Session, State, GetSessionConfig
- [Events](#events) - Event, EventActions, EventCompaction
- [BaseSessionService Methods](#basesessionservice-methods)
- [Session Service Implementations](#session-service-implementations)
- [State Hierarchy & Merging](#state-hierarchy--merging)

## Core Classes

### Session

Pydantic model representing a series of interactions between a user and agents.

```python
from google.adk.sessions import Session

# Fields
session = Session(
    id="unique-session-id",           # Unique identifier
    app_name="my-agent",              # Application name
    user_id="user-123",               # User identifier
    state={"key": "value"},           # Session state dict
    events=[],                        # List of Event objects
    last_update_time=1234567890.0     # Unix timestamp
)
```

### State

Dict-like class with hierarchical prefixes and delta tracking.

```python
from google.adk.sessions import State

# Prefixes for state scoping
State.APP_PREFIX = "app:"    # Shared across all users
State.USER_PREFIX = "user:"  # Shared across user's sessions
State.TEMP_PREFIX = "temp:"  # Not persisted

# Usage in state dict
state = {
    "app:global_config": {"setting": "value"},  # App-level
    "user:preferences": {"theme": "dark"},      # User-level
    "counter": 5,                               # Session-level
    "temp:cache": {"data": []}                  # Temporary (not saved)
}
```

### GetSessionConfig

Configuration for retrieving sessions with filtering.

```python
from google.adk.sessions.base_session_service import GetSessionConfig

config = GetSessionConfig(
    num_recent_events=50,        # Limit to N most recent events
    after_timestamp=1234567890.0 # Events after this timestamp
)
```

### ListSessionsResponse

Response model for listing sessions.

```python
from google.adk.sessions.base_session_service import ListSessionsResponse

# Returns sessions without events/state populated
response = ListSessionsResponse(sessions=[session1, session2])
```

## Events

Events represent individual interactions in a conversation. Sessions contain a list of events.

### Event

Pydantic model representing an event in a conversation between agents and users.

```python
from google.adk.events import Event, EventActions
from google.genai import types

event = Event(
    author="user",                    # "user" or agent name
    invocation_id="inv-123",          # Required before appending to session
    actions=EventActions(),           # Actions attached to event
    content=types.Content(            # Message content
        parts=[types.Part(text="Hello")]
    ),
    branch="agent1.agent2",           # Optional: for sub-agent isolation
    long_running_tool_ids={"tool-1"}, # Optional: async tool tracking
)

# Auto-generated fields
event.id          # UUID, auto-generated
event.timestamp   # Unix timestamp, auto-generated
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Auto-generated UUID |
| `author` | str | "user" or agent name |
| `invocation_id` | str | Groups related events in one turn |
| `actions` | EventActions | State changes, transfers, etc. |
| `content` | types.Content | Message content with parts |
| `timestamp` | float | Unix timestamp |
| `branch` | str | Sub-agent hierarchy (e.g., "agent1.agent2") |
| `partial` | bool | True if streaming partial response |
| `turn_complete` | bool | True if agent turn is complete |
| `long_running_tool_ids` | set[str] | IDs of async function calls |

**Helper Methods:**

```python
# Check if final response (no pending function calls)
if event.is_final_response():
    print("Agent finished responding")

# Get function calls from event
func_calls = event.get_function_calls()  # list[types.FunctionCall]

# Get function responses from event
func_responses = event.get_function_responses()  # list[types.FunctionResponse]
```

### EventActions

Actions attached to an event that affect session state or agent flow.

```python
from google.adk.events import EventActions

actions = EventActions(
    # State management
    state_delta={                     # Update session/user/app state
        "app:config": "value",
        "user:pref": "dark",
        "counter": 5
    },

    # Artifact management
    artifact_delta={                  # Track artifact versions
        "output.pdf": 2               # filename: version
    },

    # Agent control flow
    transfer_to_agent="specialist",   # Hand off to another agent
    escalate=True,                    # Escalate to parent agent

    # Response control
    skip_summarization=True,          # Skip LLM summarization of tool response

    # Authentication
    requested_auth_configs={          # Auth requested by tools
        "func_call_id": AuthConfig(...)
    },

    # Tool confirmations
    requested_tool_confirmations={    # Confirmations needed
        "func_call_id": ToolConfirmation(...)
    },

    # Advanced
    compaction=EventCompaction(...),  # Compacted event history
    end_of_agent=True,                # Agent finished current run
    agent_state={"key": "value"},     # Agent internal state
    rewind_before_invocation_id="id", # Rewind to previous state
)
```

**Key Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `state_delta` | dict | State updates (uses prefixes) |
| `artifact_delta` | dict[str, int] | Artifact filename to version |
| `transfer_to_agent` | str | Transfer control to named agent |
| `escalate` | bool | Escalate to parent agent |
| `skip_summarization` | bool | Skip LLM summary of function response |
| `end_of_agent` | bool | Agent finished its run |
| `compaction` | EventCompaction | Compacted conversation history |

### EventCompaction

Represents compacted/summarized event history.

```python
from google.adk.events.event_actions import EventCompaction
from google.genai.types import Content

compaction = EventCompaction(
    start_timestamp=1704067200.0,     # Start of compacted range
    end_timestamp=1704070800.0,       # End of compacted range
    compacted_content=Content(        # Summary of compacted events
        parts=[Part(text="Summary of conversation...")]
    )
)
```

## BaseSessionService Methods

Abstract base class defining the session service interface.

### create_session

```python
async def create_session(
    self,
    *,
    app_name: str,              # Required: application name
    user_id: str,               # Required: user identifier
    state: dict[str, Any] = None,  # Optional: initial state
    session_id: str = None,     # Optional: client-provided ID
) -> Session:
```

### get_session

```python
async def get_session(
    self,
    *,
    app_name: str,
    user_id: str,
    session_id: str,
    config: GetSessionConfig = None,  # Optional filtering
) -> Optional[Session]:
```

### list_sessions

```python
async def list_sessions(
    self,
    *,
    app_name: str,
    user_id: str = None,  # If None, lists all users
) -> ListSessionsResponse:
```

### delete_session

```python
async def delete_session(
    self,
    *,
    app_name: str,
    user_id: str,
    session_id: str,
) -> None:
```

### append_event

```python
async def append_event(
    self,
    session: Session,
    event: Event,
) -> Event:
```

## Session Service Implementations

### InMemorySessionService

For development and testing only. Not thread-safe.

```python
from google.adk.sessions import InMemorySessionService

service = InMemorySessionService()

# Internal data structures
service.sessions    # dict[app_name][user_id][session_id] = Session
service.user_state  # dict[app_name][user_id][key] = value
service.app_state   # dict[app_name][key] = value
```

### DatabaseSessionService

Production-ready persistent storage using SQLAlchemy.

```python
from google.adk.sessions import DatabaseSessionService

# SQLite (development)
service = DatabaseSessionService("sqlite:///sessions.db")

# PostgreSQL (production)
service = DatabaseSessionService(
    "postgresql://user:pass@host:5432/dbname"
)

# MySQL
service = DatabaseSessionService(
    "mysql+pymysql://user:pass@host:3306/dbname"
)

# Cloud Spanner
service = DatabaseSessionService(
    "spanner+spanner:///projects/PROJECT/instances/INSTANCE/databases/DB"
)
```

**Database Tables:**
- `sessions` - Session metadata and session-level state
- `events` - Event storage with foreign key to sessions
- `app_states` - Application-level shared state
- `user_states` - User-level shared state

### VertexAiSessionService

Connects to Vertex AI Agent Engine Session Service.

```python
from google.adk.sessions import VertexAiSessionService

service = VertexAiSessionService(
    project="my-gcp-project",
    location="us-central1",
    agent_engine_id="123456789"  # ReasoningEngine ID
)

# Or using full resource name as app_name
service = VertexAiSessionService()
# Then use app_name="projects/P/locations/L/reasoningEngines/ID"
```

**Notes:**
- Does not support client-provided session IDs
- Supports Express Mode with `GOOGLE_GENAI_USE_VERTEXAI=true` + `GOOGLE_API_KEY`

## State Hierarchy & Merging

State is merged in order of precedence (session > user > app):

```python
# When retrieving a session, states are merged:
merged_state = {}

# 1. App state (lowest precedence)
for key in app_state:
    merged_state[f"app:{key}"] = app_state[key]

# 2. User state
for key in user_state:
    merged_state[f"user:{key}"] = user_state[key]

# 3. Session state (highest precedence, no prefix)
merged_state.update(session_state)
```

## Event State Delta Processing

When events are appended, state deltas are extracted and applied:

```python
from google.adk.sessions._session_util import extract_state_delta

# Input state delta from event
delta = {
    "app:config": "value",      # Updates app state
    "user:pref": "value",       # Updates user state
    "session_key": "value",     # Updates session state
    "temp:cache": "value"       # Ignored (not persisted)
}

# Extracted into separate buckets
result = extract_state_delta(delta)
# {
#     "app": {"config": "value"},
#     "user": {"pref": "value"},
#     "session": {"session_key": "value"}
# }
```
