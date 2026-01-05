# Logging Plugin API Reference

## BasePlugin Callback Methods

All callbacks are async methods that return `Optional[T]`. Returning `None` allows normal execution; returning a value short-circuits remaining plugins/callbacks.

### Lifecycle Callbacks

#### `on_user_message_callback`
Called when a user message is received before invocation starts.

```python
async def on_user_message_callback(
    self,
    *,
    invocation_context: InvocationContext,
    user_message: types.Content,
) -> Optional[types.Content]:
```

**Parameters:**
- `invocation_context`: Full context for the invocation
- `user_message`: The user's message content

**Returns:** `Content` to replace user message, or `None` to proceed

---

#### `before_run_callback`
Called before the ADK runner starts processing.

```python
async def before_run_callback(
    self,
    *,
    invocation_context: InvocationContext,
) -> Optional[types.Content]:
```

**Returns:** `Content` to halt execution and return immediately, or `None` to proceed

---

#### `after_run_callback`
Called after the runner completes an invocation.

```python
async def after_run_callback(
    self,
    *,
    invocation_context: InvocationContext,
) -> None:
```

---

#### `on_event_callback`
Called after an event is yielded from the runner.

```python
async def on_event_callback(
    self,
    *,
    invocation_context: InvocationContext,
    event: Event,
) -> Optional[Event]:
```

**Returns:** `Event` to replace the event, or `None` to use original

---

### Agent Callbacks

#### `before_agent_callback`
Called before an agent's logic is invoked.

```python
async def before_agent_callback(
    self,
    *,
    agent: BaseAgent,
    callback_context: CallbackContext,
) -> Optional[types.Content]:
```

**Returns:** `Content` to bypass agent execution, or `None` to proceed

---

#### `after_agent_callback`
Called after an agent completes.

```python
async def after_agent_callback(
    self,
    *,
    agent: BaseAgent,
    callback_context: CallbackContext,
) -> Optional[types.Content]:
```

**Returns:** `Content` to use as agent response, or `None`

---

### Model (LLM) Callbacks

#### `before_model_callback`
Called before sending a request to the LLM.

```python
async def before_model_callback(
    self,
    *,
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> Optional[LlmResponse]:
```

**Returns:** `LlmResponse` for caching/early exit, or `None` to proceed

---

#### `after_model_callback`
Called after receiving a response from the LLM.

```python
async def after_model_callback(
    self,
    *,
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> Optional[LlmResponse]:
```

**Returns:** `LlmResponse` to replace original, or `None`

---

#### `on_model_error_callback`
Called when an LLM call errors.

```python
async def on_model_error_callback(
    self,
    *,
    callback_context: CallbackContext,
    llm_request: LlmRequest,
    error: Exception,
) -> Optional[LlmResponse]:
```

**Returns:** `LlmResponse` to recover from error, or `None` to propagate error

---

### Tool Callbacks

#### `before_tool_callback`
Called before a tool is executed.

```python
async def before_tool_callback(
    self,
    *,
    tool: BaseTool,
    tool_args: dict[str, Any],
    tool_context: ToolContext,
) -> Optional[dict]:
```

**Returns:** `dict` to skip tool execution and return immediately, or `None`

---

#### `after_tool_callback`
Called after a tool completes.

```python
async def after_tool_callback(
    self,
    *,
    tool: BaseTool,
    tool_args: dict[str, Any],
    tool_context: ToolContext,
    result: dict,
) -> Optional[dict]:
```

**Returns:** `dict` to replace tool result, or `None`

---

#### `on_tool_error_callback`
Called when a tool call errors.

```python
async def on_tool_error_callback(
    self,
    *,
    tool: BaseTool,
    tool_args: dict[str, Any],
    tool_context: ToolContext,
    error: Exception,
) -> Optional[dict]:
```

**Returns:** `dict` to use as tool response instead of error, or `None`

---

## Context Objects

### InvocationContext

The full context for an invocation (user message → final response).

| Field | Type | Description |
|-------|------|-------------|
| `invocation_id` | `str` | Unique ID for this invocation |
| `branch` | `Optional[str]` | Agent hierarchy branch (e.g., `agent_1.agent_2`) |
| `agent` | `BaseAgent` | Current agent being executed |
| `session` | `Session` | Current session with state and events |
| `user_content` | `Optional[Content]` | Original user message |
| `agent_states` | `dict[str, dict]` | Per-agent state snapshots |
| `end_of_agents` | `dict[str, bool]` | Whether each agent has finished |
| `end_invocation` | `bool` | Set `True` to terminate invocation |

**Computed Properties:**
- `app_name`: `str` - Application name from session
- `user_id`: `str` - User ID from session

---

### CallbackContext

Context for agent/model callbacks. Inherits from `ReadonlyContext`.

| Property | Type | Description |
|----------|------|-------------|
| `invocation_id` | `str` | Current invocation ID |
| `agent_name` | `str` | Name of current agent |
| `state` | `State` | Delta-aware session state (mutable) |
| `session` | `Session` | Current session |
| `user_content` | `Optional[Content]` | Original user message |

**Methods:**
- `load_artifact(filename, version=None)` → `Optional[Part]`
- `save_artifact(filename, artifact)` → `int` (version)
- `list_artifacts()` → `list[str]`

---

### ToolContext

Context for tool callbacks. Extends `CallbackContext`.

| Property | Type | Description |
|----------|------|-------------|
| `function_call_id` | `Optional[str]` | ID of the function call from LLM |
| `actions` | `EventActions` | Actions to include in response event |

**Additional Methods:**
- `request_credential(auth_config)` - Request auth for the tool
- `get_auth_response(auth_config)` → `AuthCredential`
- `request_confirmation(hint=None, payload=None)` - Request user confirmation
- `search_memory(query)` → `SearchMemoryResponse`

---

## Data Objects

### Session

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Session ID |
| `app_name` | `str` | Application name |
| `user_id` | `str` | User identifier |
| `state` | `dict[str, Any]` | Session state (mutable) |
| `events` | `list[Event]` | Conversation history |

---

### Event

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique event ID |
| `invocation_id` | `str` | Parent invocation ID |
| `author` | `str` | `"user"` or agent name |
| `content` | `Optional[Content]` | Message content |
| `actions` | `EventActions` | State delta, transfers, etc. |
| `branch` | `Optional[str]` | Branch for this event |
| `timestamp` | `float` | Unix timestamp |
| `long_running_tool_ids` | `Optional[set[str]]` | IDs of async tools |

**Methods:**
- `is_final_response()` → `bool`
- `get_function_calls()` → `list[FunctionCall]`
- `get_function_responses()` → `list[FunctionResponse]`

---

### EventActions

| Field | Type | Description |
|-------|------|-------------|
| `state_delta` | `dict[str, Any]` | State changes from this event |
| `agent_state` | `Optional[dict]` | Agent-specific state |
| `end_of_agent` | `bool` | Whether agent finished |
| `transfer_to_agent` | `Optional[str]` | Agent to transfer control to |
| `skip_summarization` | `bool` | Skip LLM summarization |
| `artifact_delta` | `dict[str, int]` | Artifact changes |

---

### LlmRequest

| Field | Type | Description |
|-------|------|-------------|
| `model` | `Optional[str]` | Model name |
| `contents` | `list[Content]` | Conversation contents |
| `config` | `Optional[GenerateContentConfig]` | Generation config |
| `tools_dict` | `dict[str, BaseTool]` | Available tools |

---

### LlmResponse

| Field | Type | Description |
|-------|------|-------------|
| `content` | `Optional[Content]` | Response content |
| `error_code` | `Optional[int]` | Error code if failed |
| `error_message` | `Optional[str]` | Error message |
| `usage_metadata` | `Optional[UsageMetadata]` | Token usage |
| `finish_reason` | `Optional[FinishReason]` | Why generation stopped |
| `partial` | `bool` | If streaming partial response |
| `turn_complete` | `Optional[bool]` | If turn is complete |

---

## Execution Order

Plugins execute in registration order, before agent callbacks:

```
Plugin_1.before_model_callback
    ↓
Plugin_2.before_model_callback
    ↓
Agent.before_model_callback
    ↓
[LLM Call]
    ↓
Agent.after_model_callback
    ↓
Plugin_2.after_model_callback
    ↓
Plugin_1.after_model_callback
```

If any callback returns a non-`None` value, it **short-circuits** all remaining callbacks.

---

## Imports

```python
from google.genai import types
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.base_agent import BaseAgent
from google.adk.events.event import Event
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
```
