# Tools API Reference

## Creating Tools

### FunctionTool (Automatic Wrapping)

The simplest way to create a tool - just pass a function to the agent's `tools` list:

```python
from google.adk.agents import LlmAgent

def get_weather(city: str, unit: str = "celsius") -> dict:
    """Get the current weather for a city.

    Args:
        city: The city name to get weather for.
        unit: Temperature unit - "celsius" or "fahrenheit".

    Returns:
        Weather data including temperature and conditions.
    """
    # Implementation
    return {"city": city, "temp": 22, "unit": unit, "conditions": "sunny"}

agent = LlmAgent(
    name="weather_agent",
    model="gemini-2.0-flash",
    instruction="Help users check the weather.",
    tools=[get_weather],  # Automatically wrapped as FunctionTool
)
```

### Explicit FunctionTool

```python
from google.adk.tools import FunctionTool

def calculate(expression: str) -> float:
    """Evaluate a mathematical expression."""
    return eval(expression)

calc_tool = FunctionTool(
    func=calculate,
    require_confirmation=True,  # Require user approval before execution
)
```

### Tool with ToolContext

Access runtime context (state, artifacts, memory) in your tool:

```python
from google.adk.tools import ToolContext

def search_with_context(query: str, tool_context: ToolContext) -> dict:
    """Search with access to session state."""
    # Access session state
    user_preferences = tool_context.state.get("preferences", {})

    # Modify session state
    tool_context.state["last_search"] = query

    # Access artifacts
    # artifact = await tool_context.load_artifact("data.json")

    return {"query": query, "results": [...]}
```

### Async Tools

```python
async def async_search(query: str) -> list[dict]:
    """Async tool for web search."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.example.com/search?q={query}") as resp:
            return await resp.json()
```

## ToolContext API

Available in tools when `tool_context` parameter is declared:

| Property/Method | Description |
|-----------------|-------------|
| `tool_context.state` | Read/write session state |
| `tool_context.session` | Current session info |
| `tool_context.user_id` | Current user ID |
| `tool_context.function_call_id` | ID of current tool call |
| `await tool_context.load_artifact(filename)` | Load saved artifact |
| `await tool_context.save_artifact(filename, artifact)` | Save artifact |
| `await tool_context.list_artifacts()` | List artifact filenames |
| `await tool_context.search_memory(query)` | Search agent memory |
| `tool_context.request_confirmation(hint, payload)` | Request user confirmation |

## Built-in Tools

Google ADK provides several built-in tools:

```python
from google.adk.tools import (
    GoogleSearchTool,        # Web search via Google
    VertexAiSearchTool,      # Enterprise search
    ExitLoopTool,            # Exit from LoopAgent
    LoadArtifactsTool,       # Load session artifacts
    LoadMemoryTool,          # Load agent memory
    PreloadMemoryTool,       # Preload memory at start
)
```

### GoogleSearchTool

```python
from google.adk.tools import GoogleSearchTool

search_tool = GoogleSearchTool()

agent = LlmAgent(
    name="researcher",
    model="gemini-2.0-flash",
    tools=[search_tool],
)
```

### ExitLoopTool

For use with LoopAgent to break out of iteration:

```python
from google.adk.tools import ExitLoopTool
from google.adk.agents import LoopAgent, LlmAgent

worker = LlmAgent(
    name="worker",
    instruction="Process items. Use exit_loop when all items are processed.",
    tools=[ExitLoopTool()],
)

loop = LoopAgent(
    name="processor",
    sub_agents=[worker],
    max_iterations=10,
)
```

## Toolsets

Group related tools together:

```python
from google.adk.tools import BaseToolset

class DatabaseToolset(BaseToolset):
    """Collection of database tools."""

    async def get_tools_with_prefix(self, ctx):
        return [
            FunctionTool(self.query),
            FunctionTool(self.insert),
            FunctionTool(self.update),
        ]

    def query(self, sql: str) -> list[dict]:
        """Execute a SELECT query."""
        pass

    def insert(self, table: str, data: dict) -> int:
        """Insert a row."""
        pass

    def update(self, table: str, id: int, data: dict) -> bool:
        """Update a row."""
        pass
```

## Tool Confirmation

Require user approval before sensitive operations:

```python
from google.adk.tools import FunctionTool

def delete_file(path: str) -> bool:
    """Delete a file from the system."""
    import os
    os.remove(path)
    return True

# Always require confirmation
delete_tool = FunctionTool(func=delete_file, require_confirmation=True)

# Conditional confirmation based on arguments
def should_confirm(path: str) -> bool:
    return path.startswith("/important/")

conditional_tool = FunctionTool(func=delete_file, require_confirmation=should_confirm)
```

## Pydantic Models in Tools

Use Pydantic models for complex input types:

```python
from pydantic import BaseModel
from typing import Optional

class SearchFilter(BaseModel):
    category: str
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    in_stock: bool = True

def search_products(query: str, filter: SearchFilter) -> list[dict]:
    """Search products with filters.

    Args:
        query: Search query string.
        filter: Search filters to apply.
    """
    # ADK automatically converts JSON dict to SearchFilter
    return [{"name": "Product", "price": 99.99}]
```

## Error Handling

Return errors as dictionaries:

```python
def risky_operation(data: str) -> dict:
    """Operation that might fail."""
    try:
        result = process(data)
        return {"success": True, "result": result}
    except ValueError as e:
        return {"error": f"Invalid data: {e}"}
    except Exception as e:
        return {"error": f"Operation failed: {e}"}
```

## Tool Best Practices

1. **Clear docstrings**: The docstring becomes the tool description for the LLM
2. **Type hints**: Use type hints for all parameters
3. **Descriptive names**: Function name becomes tool name
4. **Handle errors gracefully**: Return error dict rather than raising exceptions
5. **Use ToolContext sparingly**: Only add when you need state/artifacts/memory
6. **Keep tools focused**: One tool = one action
