# Tool Authentication Reference

Guide for handling authentication in ADK tools.

## Table of Contents

- [Overview](#overview)
- [ToolContext Auth Methods](#toolcontext-auth-methods)
- [AuthConfig](#authconfig)
- [AuthCredential Types](#authcredential-types)
- [AuthScheme](#authscheme)
- [Request and Response Flow](#request-and-response-flow)
- [Tool Confirmation](#tool-confirmation)

## Overview

ADK tools can request and use authentication through `ToolContext`. The auth flow:

1. Tool requests credential via `tool_context.request_credential(auth_config)`
2. Framework prompts user/system for credentials
3. Tool retrieves credential via `tool_context.get_auth_response(auth_config)`
4. Tool uses credential for authenticated operations

## ToolContext Auth Methods

### request_credential()

Request authentication from the user/system:

```python
from google.adk.auth.auth_tool import AuthConfig
from google.adk.auth.auth_schemes import AuthScheme

async def run_async(self, *, args, tool_context: ToolContext):
    auth_config = AuthConfig(
        auth_scheme=AuthScheme(
            type_="oauth2",
            flows={"authorizationCode": {...}},
        )
    )
    
    # Request credential - triggers auth flow
    tool_context.request_credential(auth_config)
    
    # Return early, will be called again with credential
    return {"status": "awaiting_auth"}
```

### get_auth_response()

Retrieve credential after user has authenticated:

```python
async def run_async(self, *, args, tool_context: ToolContext):
    auth_config = AuthConfig(
        auth_scheme=AuthScheme(type_="http", scheme="bearer")
    )
    
    # Get credential from state
    credential = tool_context.get_auth_response(auth_config)
    
    if credential and credential.http:
        token = credential.http.credentials.token
        # Use token for API calls
```

## AuthConfig

Configuration for authentication requirements.

```python
from google.adk.auth.auth_tool import AuthConfig
from google.adk.auth.auth_schemes import AuthScheme
from google.adk.auth.auth_credential import AuthCredential

auth_config = AuthConfig(
    auth_scheme=AuthScheme(...),           # Required auth scheme
    raw_auth_credential=AuthCredential(...) # Optional pre-configured credential
)
```

## AuthCredential Types

### OAuth2

```python
from google.adk.auth.auth_credential import AuthCredential, OAuth2Auth

credential = AuthCredential(
    oauth2=OAuth2Auth(
        access_token="ya29.access_token_here",
        refresh_token="1//refresh_token",      # Optional
        token_type="Bearer",                    # Optional
        expires_at=datetime(2024, 12, 31),     # Optional
    )
)
```

### HTTP Authentication

```python
from google.adk.auth.auth_credential import AuthCredential, HttpAuth, HttpCredentials

# Bearer token
credential = AuthCredential(
    http=HttpAuth(
        scheme="bearer",
        credentials=HttpCredentials(token="your_token")
    )
)

# Basic auth
credential = AuthCredential(
    http=HttpAuth(
        scheme="basic",
        credentials=HttpCredentials(
            username="user",
            password="pass"
        )
    )
)

# Custom scheme
credential = AuthCredential(
    http=HttpAuth(
        scheme="digest",
        credentials=HttpCredentials(token="digest_token")
    )
)
```

### API Key

```python
credential = AuthCredential(
    api_key="your_api_key_here"
)
```

### Service Account

```python
from google.adk.auth.auth_credential import AuthCredential, ServiceAccount

credential = AuthCredential(
    service_account=ServiceAccount(
        type_="service_account",
        project_id="my-project",
        private_key_id="key-id",
        private_key="-----BEGIN PRIVATE KEY-----\n...",
        client_email="sa@project.iam.gserviceaccount.com",
        client_id="123456789",
        # ... other fields
    )
)
```

## AuthScheme

Defines the authentication scheme type.

### OAuth2

```python
from google.adk.auth.auth_schemes import AuthScheme

auth_scheme = AuthScheme(
    type_="oauth2",
    flows={
        "authorizationCode": {
            "authorizationUrl": "https://accounts.google.com/o/oauth2/auth",
            "tokenUrl": "https://oauth2.googleapis.com/token",
            "scopes": {
                "email": "View email",
                "profile": "View profile",
            }
        }
    }
)
```

### HTTP Schemes

```python
# Bearer token
auth_scheme = AuthScheme(
    type_="http",
    scheme="bearer",
)

# Basic auth
auth_scheme = AuthScheme(
    type_="http",
    scheme="basic",
)
```

### API Key

```python
from fastapi.openapi.models import APIKeyIn

auth_scheme = AuthScheme(
    type_="apiKey",
    in_=APIKeyIn.header,  # header, query, or cookie
    name="X-API-Key",     # Header/query param name
)
```

## Request and Response Flow

### Complete Auth Flow Example

```python
from google.adk.tools.base_tool import BaseTool
from google.adk.auth.auth_tool import AuthConfig
from google.adk.auth.auth_schemes import AuthScheme

class AuthenticatedTool(BaseTool):
    def __init__(self):
        super().__init__(name="secure_api", description="Access secure API")
        self._auth_config = AuthConfig(
            auth_scheme=AuthScheme(
                type_="http",
                scheme="bearer",
            )
        )
    
    async def run_async(self, *, args, tool_context: ToolContext):
        # Try to get existing credential
        credential = tool_context.get_auth_response(self._auth_config)
        
        if not credential or not credential.http:
            # No credential - request one
            tool_context.request_credential(self._auth_config)
            return {"status": "authentication_required"}
        
        # Use credential
        token = credential.http.credentials.token
        headers = {"Authorization": f"Bearer {token}"}
        
        result = await self._call_api(args, headers)
        return result
```

### Pre-configured Credential

Skip auth flow with pre-configured credentials:

```python
auth_config = AuthConfig(
    auth_scheme=AuthScheme(type_="http", scheme="bearer"),
    raw_auth_credential=AuthCredential(
        http=HttpAuth(
            scheme="bearer",
            credentials=HttpCredentials(token="preconfigured_token")
        )
    )
)

# get_auth_response returns raw_auth_credential directly
credential = tool_context.get_auth_response(auth_config)
```

## Tool Confirmation

Request user approval before executing sensitive operations.

### request_confirmation()

```python
async def run_async(self, *, args, tool_context: ToolContext):
    # Check for existing confirmation
    if not tool_context.tool_confirmation:
        # Request confirmation
        tool_context.request_confirmation(
            hint="This will delete the file. Approve?",
            payload={
                "action": "delete",
                "path": args["file_path"],
            }
        )
        return {"status": "confirmation_required"}
    
    # Check if confirmed
    if not tool_context.tool_confirmation.confirmed:
        return {"status": "rejected", "message": "User rejected the action"}
    
    # Confirmed - proceed with operation
    result = await self._delete_file(args["file_path"])
    return result
```

### ToolConfirmation Object

```python
from google.adk.tools.tool_confirmation import ToolConfirmation

# Confirmation response structure
confirmation = ToolConfirmation(
    confirmed=True,           # User's decision
    hint="Original hint",     # Echo of request hint
    payload={"action": "..."}  # Echo of request payload
)
```

### FunctionTool Confirmation

Built-in support in FunctionTool:

```python
# Always require confirmation
tool = FunctionTool(delete_file, require_confirmation=True)

# Conditional confirmation
def needs_approval(path: str, force: bool = False) -> bool:
    return not force and path.startswith("/critical/")

tool = FunctionTool(delete_file, require_confirmation=needs_approval)
```

## Accessing Credential Service

For advanced scenarios, access the credential service directly:

```python
async def run_async(self, *, args, tool_context: ToolContext):
    cred_service = tool_context._invocation_context.credential_service
    
    if cred_service:
        # Custom credential operations
        pass
```

## State-based Credential Storage

Credentials are stored in session state, accessible via:

```python
# Credentials are stored by AuthHandler in state
# Access pattern varies by auth type and config
state = tool_context.state
```

## Best Practices

1. **Always check for credential before requesting**: Avoid redundant auth prompts
2. **Handle credential expiration**: Check `expires_at` for OAuth2 tokens
3. **Use raw_auth_credential for static credentials**: Skip interactive auth flow
4. **Implement credential refresh**: For long-running operations
5. **Log auth failures appropriately**: Don't expose sensitive details
6. **Use confirmation for destructive operations**: Protect against unintended actions
