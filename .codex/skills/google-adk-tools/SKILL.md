---
name: google-adk-tools
description: Guide for implementing and using Google ADK (Agent Development Kit) tools and toolsets. Use when creating custom tools from Python functions, wrapping agents as tools, integrating MCP (Model Context Protocol) servers, handling tool context and authentication, or building toolsets for agents. Covers BaseTool, FunctionTool, AgentTool, McpTool, McpToolset, ToolContext, and tool configuration patterns.
---

# Google ADK Tools

Comprehensive guide for building and using tools in Google's Agent Development Kit (ADK).

## When to Use

Use this skill when you need to:

- **Create tools from Python functions** → Use `FunctionTool` to wrap any callable
- **Delegate to sub-agents** → Use `AgentTool` to call one agent from another
- **Transfer between agents** → Use `transfer_to_agent` for multi-agent routing
- **Connect to MCP servers** → Use `McpToolset` for filesystem, database, or API tools
- **Build custom tools** → Extend `BaseTool` for full control over declarations and execution
- **Create tool collections** → Extend `BaseToolset` for dynamic, context-aware tool sets
- **Handle tool authentication** → Use `ToolContext` methods for OAuth, API keys, etc.
- **Access session state in tools** → Use `tool_context.state` for persistence
- **Require user confirmation** → Use `require_confirmation` or `request_confirmation()`
- **Configure tools via YAML** → Define tools in agent configuration files

**Not covered here**: Agent creation (see google-adk-react-agent skill), memory services (see google-adk-memory skill), session management (see adk-session-management skill).

## Tool Hierarchy Overview

```
BaseTool (abstract base)
├── FunctionTool         - Wraps Python functions
├── AgentTool            - Wraps agents as tools
├── LoadMemoryTool       - Built-in memory search
└── McpTool              - MCP protocol integration

BaseToolset (abstract base)
└── McpToolset           - Collection of MCP tools
```

## Quick Start

### Creating a Simple Function Tool

The most common pattern—wrap any Python function:

```python
from google.adk.tools import FunctionTool

def search_database(query: str, limit: int = 10) -> list[dict]:
    """Search the database for matching records.
    
    Args:
        query: Search query string
        limit: Maximum results to return
    """
    # Implementation here
    return results

# Create tool from function
search_tool = FunctionTool(search_database)
```

### Using Tools with an Agent

```python
from google.adk.agents import LlmAgent

agent = LlmAgent(
    model='gemini-2.0-flash',
    name='assistant',
    instruction='Help users search data',
    tools=[search_tool],  # Single tool or list
)
```

## FunctionTool

Wraps Python functions with automatic parameter extraction from type hints and docstrings.

### Basic Usage

```python
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext

# Simple function
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    return f"Weather in {city}: Sunny, 72°F"

weather_tool = FunctionTool(get_weather)

# Function with tool context access
async def save_note(content: str, tool_context: ToolContext) -> str:
    """Save a note. The tool_context parameter is injected automatically."""
    user_id = tool_context._invocation_context.user_id
    # Save note for user...
    return "Note saved"

note_tool = FunctionTool(save_note)
```

### Tool Confirmation

Require user approval before execution:

```python
# Always require confirmation
FunctionTool(delete_file, require_confirmation=True)

# Conditional confirmation based on args
def needs_confirmation(path: str) -> bool:
    return path.startswith('/critical/')

FunctionTool(delete_file, require_confirmation=needs_confirmation)
```

### Pydantic Model Support

Function parameters can be Pydantic models—automatically converted from JSON:

```python
from pydantic import BaseModel

class SearchQuery(BaseModel):
    text: str
    filters: list[str] = []
    
def search(query: SearchQuery) -> list[dict]:
    """Search with structured query."""
    # query is already a SearchQuery instance
    return results
```

## AgentTool

Wrap an agent to be called as a tool by another agent (agent delegation pattern).

```python
from google.adk.tools import AgentTool
from google.adk.agents import LlmAgent

# Create specialist agent
research_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='researcher',
    description='Research specialist for finding information',
    instruction='You are a research assistant...',
)

# Wrap as tool
research_tool = AgentTool(
    agent=research_agent,
    skip_summarization=False,  # Set True to return raw output
)

# Use in orchestrator agent
orchestrator = LlmAgent(
    model='gemini-2.0-flash',
    name='orchestrator',
    tools=[research_tool],
)
```

### Input/Output Schemas

Define structured I/O for AgentTool:

```python
from pydantic import BaseModel

class ResearchInput(BaseModel):
    topic: str
    depth: str = "standard"

class ResearchOutput(BaseModel):
    findings: list[str]
    sources: list[str]

research_agent = LlmAgent(
    name='researcher',
    input_schema=ResearchInput,
    output_schema=ResearchOutput,
    # ...
)
```

## Agent Transfer

Transfer control between agents in a multi-agent system:

```python
from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
from google.adk.tools.tool_context import ToolContext

def route_to_specialist(category: str, tool_context: ToolContext) -> None:
    """Route query to appropriate specialist agent."""
    if category == "technical":
        transfer_to_agent("tech_support", tool_context)
    elif category == "billing":
        transfer_to_agent("billing_agent", tool_context)
```

The `transfer_to_agent` function sets `tool_context.actions.transfer_to_agent` to trigger handoff.

## ToolContext

Context object providing access to invocation state, memory, artifacts, and actions.

### Key Properties and Methods

```python
async def my_tool(query: str, tool_context: ToolContext) -> str:
    # Access event actions
    actions = tool_context.actions
    
    # Search user's memory
    memory_results = await tool_context.search_memory("previous conversations")
    
    # Request authentication
    tool_context.request_credential(auth_config)
    
    # Get auth response
    credential = tool_context.get_auth_response(auth_config)
    
    # Request user confirmation
    tool_context.request_confirmation(
        hint="Approve this action?",
        payload={"action": "delete", "target": "file.txt"}
    )
    
    # Access session state
    state = tool_context.state
    state["key"] = "value"  # Persists to session
    
    # Transfer to another agent
    tool_context.actions.transfer_to_agent = "other_agent"
    
    # Skip LLM summarization of result
    tool_context.actions.skip_summarization = True
```

## MCP Integration

Connect to MCP (Model Context Protocol) servers. See [references/mcp_integration.md](references/mcp_integration.md) for detailed setup.

### McpToolset (Recommended)

```python
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

# Local MCP server via stdio
toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='npx',
            args=["-y", "@modelcontextprotocol/server-filesystem", "/path"],
        ),
        timeout=5.0,
    ),
    tool_filter=['read_file', 'list_directory'],  # Optional filter
)

# Use with agent
agent = LlmAgent(
    model='gemini-2.0-flash',
    name='file_agent',
    tools=[toolset],
)

# Cleanup (handled automatically by agent framework)
await toolset.close()
```

### Connection Types

```python
from google.adk.tools.mcp_tool import (
    StdioConnectionParams,
    SseConnectionParams,
    StreamableHTTPConnectionParams,
)

# SSE connection
sse_params = SseConnectionParams(
    url="http://localhost:8080/sse",
    headers={"Authorization": "Bearer token"},
    timeout=5.0,
)

# Streamable HTTP connection
http_params = StreamableHTTPConnectionParams(
    url="http://localhost:8080/mcp",
    timeout=5.0,
)
```

## Tool Configuration (YAML)

Define tools in agent configuration files:

```yaml
# agent.yaml
tools:
  # Built-in tool by name
  - name: google_search
  
  # Function tool from module
  - name: my_package.tools.search_database
  
  # AgentTool with config
  - name: AgentTool
    args:
      agent: ./specialist_agent.yaml
      skip_summarization: true
  
  # McpToolset
  - name: McpToolset
    args:
      stdio_connection_params:
        server_params:
          command: npx
          args: ["-y", "@modelcontextprotocol/server-filesystem"]
        timeout: 5.0
      tool_filter: ["read_file", "write_file"]
```

## Custom Tool Implementation

Extend `BaseTool` for advanced customization. See [references/custom_tools.md](references/custom_tools.md).

```python
from google.adk.tools.base_tool import BaseTool
from google.genai import types

class MyCustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="Custom tool description",
            is_long_running=False,
        )
    
    def _get_declaration(self) -> types.FunctionDeclaration:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "param": types.Schema(type=types.Type.STRING)
                },
                required=["param"],
            ),
        )
    
    async def run_async(self, *, args: dict, tool_context: ToolContext) -> Any:
        # Tool implementation
        return {"result": args["param"]}
```

## Custom Toolset

Create toolsets for dynamic tool collections:

```python
from google.adk.tools.base_toolset import BaseToolset, ToolPredicate

class MyToolset(BaseToolset):
    def __init__(self, tool_filter=None):
        super().__init__(tool_filter=tool_filter)
        self._tools = []  # Initialize your tools
    
    async def get_tools(self, readonly_context=None) -> list[BaseTool]:
        # Return tools, applying filter
        return [t for t in self._tools if self._is_tool_selected(t, readonly_context)]
    
    async def close(self) -> None:
        # Cleanup resources
        pass
```

## Built-in Tools

### LoadMemoryTool

Search user's memory:

```python
from google.adk.tools.load_memory_tool import load_memory_tool

agent = LlmAgent(
    tools=[load_memory_tool],  # Pre-configured instance
)
```

Automatically adds instruction: "You have memory. You can use it to answer questions..."

## Resources

- **MCP Integration Details**: See [references/mcp_integration.md](references/mcp_integration.md)
- **Custom Tool API**: See [references/custom_tools.md](references/custom_tools.md)
- **Authentication**: See [references/tool_auth.md](references/tool_auth.md)
