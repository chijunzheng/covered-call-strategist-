# Custom Tools Reference

Detailed API reference for implementing custom tools in ADK.

## Table of Contents

- [BaseTool](#basetool)
- [BaseToolset](#basetoolset)
- [FunctionTool Internals](#functiontool-internals)
- [Tool Configuration](#tool-configuration)
- [Advanced Patterns](#advanced-patterns)

## BaseTool

Abstract base class for all ADK tools.

### Class Definition

```python
class BaseTool(ABC):
    name: str                           # Tool name (required)
    description: str                    # Tool description (required)
    is_long_running: bool = False       # For async operations
    custom_metadata: dict[str, Any]     # Optional JSON-serializable metadata
```

### Constructor

```python
def __init__(
    self,
    *,
    name: str,
    description: str,
    is_long_running: bool = False,
    custom_metadata: dict[str, Any] | None = None,
)
```

### Core Methods

#### `_get_declaration()`

Returns the OpenAPI specification as a `FunctionDeclaration`. Required for tools that add function declarations to LLM requests.

```python
from google.genai import types

def _get_declaration(self) -> types.FunctionDeclaration | None:
    return types.FunctionDeclaration(
        name=self.name,
        description=self.description,
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                'param1': types.Schema(
                    type=types.Type.STRING,
                    description='First parameter',
                ),
                'param2': types.Schema(
                    type=types.Type.INTEGER,
                    description='Optional second parameter',
                ),
            },
            required=['param1'],
        ),
    )
```

#### `run_async()`

Execute the tool with LLM-provided arguments.

```python
async def run_async(
    self,
    *,
    args: dict[str, Any],
    tool_context: ToolContext,
) -> Any:
    """
    Args:
        args: Arguments from LLM function call
        tool_context: Execution context
    
    Returns:
        Tool result (any serializable type)
    """
    result = await self._do_work(args)
    return result
```

#### `process_llm_request()`

Customize how the tool is added to LLM requests. Default implementation appends the tool.

```python
async def process_llm_request(
    self,
    *,
    tool_context: ToolContext,
    llm_request: LlmRequest,
) -> None:
    # Default: add this tool to the request
    llm_request.append_tools([self])
    
    # Optional: add instructions
    llm_request.append_instructions([
        "Use this tool when you need to..."
    ])
```

#### `from_config()`

Factory method for creating tools from YAML configuration.

```python
@classmethod
def from_config(
    cls,
    config: ToolArgsConfig,
    config_abs_path: str,
) -> BaseTool:
    # Parse config and create instance
    return cls(**parsed_kwargs)
```

### Complete Example

```python
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

class WeatherTool(BaseTool):
    """Tool for fetching weather data."""
    
    def __init__(self, api_key: str):
        super().__init__(
            name="get_weather",
            description="Get current weather for a location",
            custom_metadata={"provider": "openweathermap"},
        )
        self._api_key = api_key
    
    def _get_declaration(self) -> types.FunctionDeclaration:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'location': types.Schema(
                        type=types.Type.STRING,
                        description='City name or coordinates',
                    ),
                    'units': types.Schema(
                        type=types.Type.STRING,
                        enum=['celsius', 'fahrenheit'],
                        description='Temperature units',
                    ),
                },
                required=['location'],
            ),
        )
    
    async def run_async(
        self,
        *,
        args: dict[str, Any],
        tool_context: ToolContext,
    ) -> dict:
        location = args['location']
        units = args.get('units', 'celsius')
        
        # Fetch weather data
        weather = await self._fetch_weather(location, units)
        
        return {
            'location': location,
            'temperature': weather['temp'],
            'conditions': weather['conditions'],
            'units': units,
        }
    
    @classmethod
    def from_config(cls, config: ToolArgsConfig, config_abs_path: str):
        api_key = config.model_dump().get('api_key')
        if not api_key:
            raise ValueError("api_key is required")
        return cls(api_key=api_key)
```

## BaseToolset

Abstract base class for tool collections.

### Class Definition

```python
class BaseToolset(ABC):
    tool_filter: ToolPredicate | list[str] | None
    tool_name_prefix: str | None
```

### Constructor

```python
def __init__(
    self,
    *,
    tool_filter: ToolPredicate | list[str] | None = None,
    tool_name_prefix: str | None = None,
)
```

### Core Methods

#### `get_tools()`

Return filtered tools based on context.

```python
@abstractmethod
async def get_tools(
    self,
    readonly_context: ReadonlyContext | None = None,
) -> list[BaseTool]:
    """Return tools available in the current context."""
```

#### `get_tools_with_prefix()`

Returns tools with optional name prefix applied. Calls `get_tools()` internally.

```python
@final  # Cannot be overridden
async def get_tools_with_prefix(
    self,
    readonly_context: ReadonlyContext | None = None,
) -> list[BaseTool]:
    """Returns tools with prefixed names if tool_name_prefix is set."""
```

#### `close()`

Cleanup resources.

```python
async def close(self) -> None:
    """Release resources held by the toolset."""
```

#### `process_llm_request()`

Process LLM request at toolset level (before individual tools).

```python
async def process_llm_request(
    self,
    *,
    tool_context: ToolContext,
    llm_request: LlmRequest,
) -> None:
    """Called before each tool processes the request."""
```

### Tool Filtering

#### Filter by Name List

```python
toolset = MyToolset(tool_filter=['tool1', 'tool2'])
```

#### Filter by Predicate

```python
from google.adk.tools.base_toolset import ToolPredicate

class MyPredicate(ToolPredicate):
    def __call__(
        self,
        tool: BaseTool,
        readonly_context: ReadonlyContext | None = None,
    ) -> bool:
        # Only include tools with "search" in name
        return "search" in tool.name

toolset = MyToolset(tool_filter=MyPredicate())
```

### Complete Example

```python
from google.adk.tools.base_toolset import BaseToolset
from google.adk.agents.readonly_context import ReadonlyContext

class DatabaseToolset(BaseToolset):
    """Toolset providing database operations."""
    
    def __init__(
        self,
        connection_string: str,
        tool_filter: list[str] | None = None,
    ):
        super().__init__(tool_filter=tool_filter)
        self._connection_string = connection_string
        self._connection = None
    
    async def get_tools(
        self,
        readonly_context: ReadonlyContext | None = None,
    ) -> list[BaseTool]:
        # Lazy initialize connection
        if not self._connection:
            self._connection = await self._connect()
        
        # Get available tables/operations
        tables = await self._connection.list_tables()
        
        tools = []
        for table in tables:
            tool = QueryTool(table, self._connection)
            if self._is_tool_selected(tool, readonly_context):
                tools.append(tool)
        
        return tools
    
    async def close(self) -> None:
        if self._connection:
            await self._connection.close()
            self._connection = None
```

## FunctionTool Internals

Understanding how `FunctionTool` processes functions.

### Parameter Extraction

FunctionTool uses `inspect` to extract function metadata:

```python
# From function signature
signature = inspect.signature(func)
for param_name, param in signature.parameters.items():
    if param.default == inspect.Parameter.empty:
        # Mandatory parameter
    else:
        # Optional parameter with default
```

### Type Hint Processing

Type hints are converted to Gemini Schema:

```python
# Supported types
str → Type.STRING
int → Type.INTEGER
float → Type.NUMBER
bool → Type.BOOLEAN
list[T] → Type.ARRAY with items
dict → Type.OBJECT
Optional[T] → Nullable type
BaseModel → Type.OBJECT with properties
```

### Docstring Parsing

Docstrings provide descriptions:

```python
def my_tool(param: str) -> str:
    """Tool description goes here.
    
    Args:
        param: Parameter description used in schema
    
    Returns:
        Description of return value
    """
```

### Ignored Parameters

These parameters are automatically injected, not exposed to LLM:

- `tool_context: ToolContext`
- `input_stream` (for streaming tools)

### Pydantic Conversion

JSON arguments are converted to Pydantic models:

```python
def _preprocess_args(self, args: dict) -> dict:
    for param_name, param in signature.parameters.items():
        if issubclass(param.annotation, BaseModel):
            args[param_name] = param.annotation.model_validate(args[param_name])
    return args
```

## Tool Configuration

### ToolConfig

Configuration model for tool definition in YAML:

```python
class ToolConfig(BaseModel):
    name: str           # Tool name or fully qualified path
    args: ToolArgsConfig | None  # Optional arguments
```

### Configuration Patterns

```yaml
# 1. Built-in tool by name
tools:
  - name: google_search

# 2. Tool class with args
tools:
  - name: WeatherTool
    args:
      api_key: "${WEATHER_API_KEY}"

# 3. Function from module
tools:
  - name: my_package.tools.search_database

# 4. Custom tool class
tools:
  - name: my_package.tools.CustomTool
    args:
      param1: value1
      param2: value2

# 5. Tool factory function
tools:
  - name: my_package.tools.create_tool
    args:
      config_path: ./config.yaml
```

### BaseToolConfig

Base for typed tool configurations:

```python
from google.adk.tools.tool_configs import BaseToolConfig

class MyToolConfig(BaseToolConfig):
    api_key: str
    timeout: float = 30.0
    
    # extra="forbid" is inherited - unknown fields raise errors
```

## Advanced Patterns

### Long-Running Tools

For operations that return early with a resource ID:

```python
class AsyncProcessingTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="start_processing",
            description="Start async processing job",
            is_long_running=True,
        )
    
    async def run_async(self, *, args, tool_context):
        job_id = await self._start_job(args)
        return {"job_id": job_id, "status": "processing"}
```

### Tool with Authentication

Extend `BaseAuthenticatedTool` for tools requiring auth:

```python
from google.adk.tools.base_authenticated_tool import BaseAuthenticatedTool

class SecureTool(BaseAuthenticatedTool):
    async def _run_async_impl(
        self,
        *,
        args,
        tool_context: ToolContext,
        credential: AuthCredential,
    ) -> dict:
        # credential is populated from auth config
        headers = {"Authorization": f"Bearer {credential.oauth2.access_token}"}
        return await self._call_api(args, headers)
```

### State Persistence

Use tool_context.state for session persistence:

```python
async def run_async(self, *, args, tool_context):
    # Read from state
    history = tool_context.state.get("search_history", [])
    
    # Perform search
    results = await self._search(args["query"])
    
    # Update state
    history.append(args["query"])
    tool_context.state["search_history"] = history
    
    return results
```

### Event Actions

Control agent behavior through actions:

```python
async def run_async(self, *, args, tool_context):
    # Skip LLM summarization of result
    tool_context.actions.skip_summarization = True
    
    # Transfer to another agent
    tool_context.actions.transfer_to_agent = "specialist_agent"
    
    # Update state
    tool_context.actions.state_delta = {"key": "value"}
    
    return result
```

### Dynamic Function Declaration

Generate declarations at runtime:

```python
def _get_declaration(self) -> types.FunctionDeclaration:
    # Build properties dynamically
    properties = {}
    for field in self._get_available_fields():
        properties[field.name] = types.Schema(
            type=self._map_type(field.type),
            description=field.description,
        )
    
    return types.FunctionDeclaration(
        name=self.name,
        description=self.description,
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties=properties,
            required=self._get_required_fields(),
        ),
    )
```
