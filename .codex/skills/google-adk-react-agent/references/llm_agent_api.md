# LlmAgent API Reference

## Class: LlmAgent

The main agent class for building LLM-based agents in Google ADK.

```python
from google.adk.agents import LlmAgent, Agent  # Agent is alias for LlmAgent
```

## Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Agent name (must be valid Python identifier, cannot be "user") |
| `description` | `str` | `''` | One-line description of agent's capability for delegation decisions |
| `model` | `str \| BaseLlm` | `''` | Model to use (inherits from ancestor if not set) |
| `instruction` | `str \| InstructionProvider` | `''` | Dynamic instructions with `{variable}` placeholders |
| `static_instruction` | `ContentUnion` | `None` | Static instruction for context caching optimization |
| `tools` | `list[ToolUnion]` | `[]` | Tools available to this agent |
| `sub_agents` | `list[BaseAgent]` | `[]` | Sub-agents for agent transfer |
| `planner` | `BasePlanner` | `None` | Planner for step-by-step execution (e.g., PlanReActPlanner) |
| `output_schema` | `type[BaseModel]` | `None` | Pydantic model for structured output |
| `output_key` | `str` | `None` | Key in session state to store agent output |

## Transfer Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `disallow_transfer_to_parent` | `bool` | `False` | Prevent transfer back to parent agent |
| `disallow_transfer_to_peers` | `bool` | `False` | Prevent transfer to sibling agents |

## Content Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_contents` | `'default' \| 'none'` | `'default'` | `'none'` = agent receives no prior history |
| `input_schema` | `type[BaseModel]` | `None` | Input schema when agent is used as a tool |
| `generate_content_config` | `GenerateContentConfig` | `None` | Additional generation config (temperature, safety, etc.) |

## Callbacks

| Parameter | Type | Description |
|-----------|------|-------------|
| `before_model_callback` | `BeforeModelCallback` | Called before LLM call; can modify request or return response to skip model |
| `after_model_callback` | `AfterModelCallback` | Called after LLM call; can modify or replace response |
| `before_tool_callback` | `BeforeToolCallback` | Called before tool execution; can skip tool and return result |
| `after_tool_callback` | `AfterToolCallback` | Called after tool execution; can modify tool result |
| `before_agent_callback` | `BeforeAgentCallback` | Called before agent run; can skip agent |
| `after_agent_callback` | `AfterAgentCallback` | Called after agent run; can append content |

## Callback Signatures

```python
# Before/After Model
async def before_model(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    pass

async def after_model(callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
    pass

# Before/After Tool
async def before_tool(tool: BaseTool, args: dict[str, Any], tool_context: ToolContext) -> Optional[dict]:
    pass

async def after_tool(tool: BaseTool, args: dict[str, Any], tool_context: ToolContext, tool_response: dict) -> Optional[dict]:
    pass

# Before/After Agent
async def before_agent(callback_context: CallbackContext) -> Optional[types.Content]:
    pass

async def after_agent(callback_context: CallbackContext) -> Optional[types.Content]:
    pass
```

## InstructionProvider

Dynamic instruction that depends on runtime context:

```python
from google.adk.agents import ReadonlyContext

def dynamic_instruction(ctx: ReadonlyContext) -> str:
    user_name = ctx.state.get('user_name', 'User')
    return f"You are assisting {user_name}. Be helpful and concise."

# Or async version
async def async_instruction(ctx: ReadonlyContext) -> str:
    return "Your dynamic instruction here"
```

## Model Strings

Common model identifiers:
- `"gemini-2.0-flash"` - Fast model
- `"gemini-1.5-pro"` - Capable model
- `"gemini-1.5-flash"` - Balanced model

## Example: Basic Agent

```python
from google.adk.agents import LlmAgent

agent = LlmAgent(
    name="assistant",
    model="gemini-2.0-flash",
    instruction="You are a helpful assistant.",
    tools=[search_tool, calculator_tool],
)
```

## Example: Agent with Planner

```python
from google.adk.agents import LlmAgent
from google.adk.planners import PlanReActPlanner

agent = LlmAgent(
    name="researcher",
    model="gemini-1.5-pro",
    instruction="Research and answer questions thoroughly.",
    tools=[web_search, document_reader],
    planner=PlanReActPlanner(),
)
```

## Example: Agent with Structured Output

```python
from pydantic import BaseModel
from google.adk.agents import LlmAgent

class AnalysisResult(BaseModel):
    summary: str
    confidence: float
    key_points: list[str]

agent = LlmAgent(
    name="analyzer",
    model="gemini-1.5-pro",
    instruction="Analyze the given data and provide structured results.",
    output_schema=AnalysisResult,
    output_key="analysis_result",  # Stored in session state
    disallow_transfer_to_parent=True,  # Required with output_schema
    disallow_transfer_to_peers=True,   # Required with output_schema
)
```

## Example: Multi-Agent Hierarchy

```python
specialist_1 = LlmAgent(
    name="data_specialist",
    description="Handles data analysis and SQL queries",
    model="gemini-1.5-pro",
    instruction="You specialize in data analysis.",
    tools=[sql_tool],
)

specialist_2 = LlmAgent(
    name="writing_specialist",
    description="Handles content writing and editing",
    model="gemini-1.5-pro",
    instruction="You specialize in writing.",
)

coordinator = LlmAgent(
    name="coordinator",
    model="gemini-1.5-pro",
    instruction="Route requests to the appropriate specialist.",
    sub_agents=[specialist_1, specialist_2],
)
```
