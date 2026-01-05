# MCP Integration Reference

Detailed guide for integrating MCP (Model Context Protocol) servers with ADK.

## Table of Contents

- [Overview](#overview)
- [McpToolset](#mcptoolset)
- [McpTool](#mcptool)
- [Connection Parameters](#connection-parameters)
- [Session Management](#session-management)
- [Authentication](#authentication)
- [Schema Conversion](#schema-conversion)
- [Configuration](#configuration)

## Overview

ADK provides MCP integration through:
- `McpToolset`: Connects to MCP servers and exposes tools to agents
- `McpTool`: Wraps individual MCP tools as ADK tools
- `MCPSessionManager`: Manages MCP client sessions with pooling

**Requirements**: Python 3.10+, `mcp` package installed.

## McpToolset

Primary class for MCP server integration.

### Constructor

```python
McpToolset(
    connection_params: StdioConnectionParams | SseConnectionParams | StreamableHTTPConnectionParams,
    tool_filter: list[str] | ToolPredicate | None = None,
    tool_name_prefix: str | None = None,
    errlog: TextIO = sys.stderr,
    auth_scheme: AuthScheme | None = None,
    auth_credential: AuthCredential | None = None,
    require_confirmation: bool | Callable[..., bool] = False,
    header_provider: Callable[[ReadonlyContext], dict[str, str]] | None = None,
)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `connection_params` | `StdioConnectionParams`, `SseConnectionParams`, `StreamableHTTPConnectionParams` | Connection settings for MCP server |
| `tool_filter` | `list[str]` or `ToolPredicate` | Filter tools by name list or predicate function |
| `tool_name_prefix` | `str` | Prefix added to all tool names (e.g., `fs_` → `fs_read_file`) |
| `errlog` | `TextIO` | Error output stream for stdio connections |
| `auth_scheme` | `AuthScheme` | Authentication scheme for tool calls |
| `auth_credential` | `AuthCredential` | Authentication credentials |
| `require_confirmation` | `bool` or `Callable` | Require user confirmation for all tools |
| `header_provider` | `Callable` | Dynamic header generator based on context |

### Methods

```python
async def get_tools(readonly_context: ReadonlyContext | None = None) -> list[BaseTool]:
    """Return all tools from MCP server, filtered by tool_filter."""

async def close() -> None:
    """Close connection and cleanup resources."""
```

### Example: Filesystem Server

```python
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command='npx',
            args=["-y", "@modelcontextprotocol/server-filesystem", "/home/user"],
        ),
        timeout=10.0,
    ),
    tool_filter=['read_file', 'write_file', 'list_directory'],
    tool_name_prefix='fs',
)

# Tools available: fs_read_file, fs_write_file, fs_list_directory
```

### Example: Remote SSE Server

```python
from google.adk.tools.mcp_tool import McpToolset, SseConnectionParams

toolset = McpToolset(
    connection_params=SseConnectionParams(
        url="https://mcp-server.example.com/sse",
        headers={"Authorization": "Bearer YOUR_TOKEN"},
        timeout=10.0,
        sse_read_timeout=300.0,
    ),
)
```

## McpTool

Individual MCP tool wrapper. Usually created internally by McpToolset.

### Constructor

```python
McpTool(
    mcp_tool: McpBaseTool,
    mcp_session_manager: MCPSessionManager,
    auth_scheme: AuthScheme | None = None,
    auth_credential: AuthCredential | None = None,
    require_confirmation: bool | Callable[..., bool] = False,
    header_provider: Callable[[ReadonlyContext], dict[str, str]] | None = None,
)
```

### Properties

```python
@property
def raw_mcp_tool(self) -> McpBaseTool:
    """Access the underlying MCP tool definition."""
```

### Authentication Support

McpTool supports multiple authentication methods:
- **OAuth2**: Bearer token in Authorization header
- **HTTP Basic**: Base64-encoded credentials
- **HTTP Bearer**: Token-based authentication
- **API Key**: Header-based API keys only (not query/cookie)

## Connection Parameters

### StdioConnectionParams

For local MCP servers running as subprocesses.

```python
from google.adk.tools.mcp_tool import StdioConnectionParams
from mcp import StdioServerParameters

params = StdioConnectionParams(
    server_params=StdioServerParameters(
        command='python',
        args=['-m', 'my_mcp_server'],
        env={'API_KEY': 'secret'},
    ),
    timeout=5.0,  # Connection timeout in seconds
)
```

### SseConnectionParams

For SSE (Server-Sent Events) connections.

```python
from google.adk.tools.mcp_tool import SseConnectionParams

params = SseConnectionParams(
    url='http://localhost:8080/sse',
    headers={'Authorization': 'Bearer token'},
    timeout=5.0,              # Connection timeout
    sse_read_timeout=300.0,   # Read timeout (5 minutes default)
)
```

### StreamableHTTPConnectionParams

For Streamable HTTP connections.

```python
from google.adk.tools.mcp_tool import StreamableHTTPConnectionParams

params = StreamableHTTPConnectionParams(
    url='http://localhost:8080/mcp',
    headers={'X-API-Key': 'key'},
    timeout=5.0,
    sse_read_timeout=300.0,
    terminate_on_close=True,  # Send terminate on connection close
)
```

## Session Management

`MCPSessionManager` handles session lifecycle with pooling.

### Features

- **Session Pooling**: Reuses sessions based on headers
- **Auto-Reconnect**: `@retry_on_closed_resource` decorator handles disconnects
- **Thread Safety**: Async lock prevents race conditions

### Manual Session Management

```python
from google.adk.tools.mcp_tool.mcp_session_manager import MCPSessionManager

manager = MCPSessionManager(connection_params)

# Get or create session
session = await manager.create_session(headers={'X-User': 'user123'})

# Call MCP tool directly
result = await session.call_tool('tool_name', arguments={'key': 'value'})

# List available tools
tools = await session.list_tools()

# Cleanup
await manager.close()
```

## Authentication

### OAuth2

```python
from google.adk.auth.auth_credential import AuthCredential, OAuth2Auth

credential = AuthCredential(
    oauth2=OAuth2Auth(access_token="your_access_token")
)

toolset = McpToolset(
    connection_params=params,
    auth_credential=credential,
)
```

### HTTP Bearer

```python
from google.adk.auth.auth_credential import AuthCredential, HttpAuth, HttpCredentials

credential = AuthCredential(
    http=HttpAuth(
        scheme="bearer",
        credentials=HttpCredentials(token="your_token")
    )
)
```

### HTTP Basic

```python
credential = AuthCredential(
    http=HttpAuth(
        scheme="basic",
        credentials=HttpCredentials(
            username="user",
            password="pass"
        )
    )
)
```

### API Key (Header Only)

```python
from google.adk.auth.auth_schemes import AuthScheme

auth_scheme = AuthScheme(
    type_="apiKey",
    in_="header",
    name="X-API-Key",
)

credential = AuthCredential(api_key="your_api_key")

toolset = McpToolset(
    connection_params=params,
    auth_scheme=auth_scheme,
    auth_credential=credential,
)
```

### Dynamic Headers

Provide headers based on request context:

```python
def provide_headers(readonly_context: ReadonlyContext) -> dict[str, str]:
    user_id = readonly_context.user_id
    return {
        'X-User-ID': user_id,
        'X-Request-ID': str(uuid.uuid4()),
    }

toolset = McpToolset(
    connection_params=params,
    header_provider=provide_headers,
)
```

## Schema Conversion

ADK converts between Gemini Schema and JSON Schema for MCP compatibility.

### ADK to MCP

```python
from google.adk.tools.mcp_tool.conversion_utils import adk_to_mcp_tool_type

mcp_tool = adk_to_mcp_tool_type(adk_tool)
```

### Gemini to JSON Schema

```python
from google.adk.tools.mcp_tool.conversion_utils import gemini_to_json_schema
from google.genai.types import Schema, Type

gemini_schema = Schema(
    type=Type.OBJECT,
    properties={
        'name': Schema(type=Type.STRING),
        'count': Schema(type=Type.INTEGER),
    },
    required=['name'],
)

json_schema = gemini_to_json_schema(gemini_schema)
# {'type': 'object', 'properties': {'name': {'type': 'string'}, 'count': {'type': 'integer'}}, 'required': ['name']}
```

## Configuration

### YAML Configuration

```yaml
# In agent.yaml
tools:
  - name: McpToolset
    args:
      stdio_connection_params:
        server_params:
          command: npx
          args: ["-y", "@modelcontextprotocol/server-filesystem", "/data"]
        timeout: 5.0
      tool_filter: ["read_file", "write_file"]
      tool_name_prefix: "fs"

  - name: McpToolset
    args:
      sse_connection_params:
        url: "https://api.example.com/mcp/sse"
        timeout: 10.0
        sse_read_timeout: 300.0
      auth_credential:
        oauth2:
          access_token: "${MCP_TOKEN}"
```

### McpToolsetConfig

Pydantic model for configuration validation:

```python
from google.adk.tools.mcp_tool import McpToolsetConfig

config = McpToolsetConfig(
    stdio_connection_params=StdioConnectionParams(...),
    tool_filter=['tool1', 'tool2'],
    tool_name_prefix='prefix',
)
# Validates: exactly one of stdio/sse/http params must be set
```

## Error Handling

```python
try:
    toolset = McpToolset(connection_params=params)
    tools = await toolset.get_tools()
except ImportError:
    # MCP package not installed or Python < 3.10
    pass
except anyio.ClosedResourceError:
    # Connection lost - automatic retry handles this
    pass
except Exception as e:
    # Connection or initialization error
    await toolset.close()
```

## Deprecated Names

- `MCPTool` → Use `McpTool`
- `MCPToolset` → Use `McpToolset`
- `SseServerParams` → Use `SseConnectionParams`
- `StreamableHTTPServerParams` → Use `StreamableHTTPConnectionParams`
