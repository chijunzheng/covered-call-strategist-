---
name: adk-logging-telemetry
description: Implement end-to-end logging and telemetry for Google ADK agents. Use when building agents that need observability including (1) tracking user interactions and agent workflow execution, (2) logging session lifecycle, state changes, and events, (3) setting up OpenTelemetry tracing with Cloud Trace/Logging/Monitoring exports, (4) implementing custom logging plugins for debugging, (5) capturing LLM requests/responses and tool executions, (6) error tracking and monitoring, or (7) creating audit trails of agent behavior.
---

# ADK Logging & Telemetry

## Overview

ADK provides two complementary mechanisms for observability:
1. **LoggingPlugin** - Console logging at callback points for debugging
2. **OpenTelemetry Integration** - Production tracing, metrics, and logs to GCP or OTLP endpoints

## When to Use This Skill

- Adding observability to ADK agents
- Debugging agent execution flow and tool calls
- Setting up production monitoring with Cloud Trace/Logging/Monitoring
- Tracking session lifecycle and state changes
- Implementing custom logging for audit trails
- Monitoring LLM token usage and performance
- Capturing errors in model or tool execution

## Quick Start

### Console Logging (Development)

```python
from google.adk.plugins import LoggingPlugin
from google.adk.runners import Runner

runner = Runner(
    agents=[my_agent],
    plugins=[LoggingPlugin()],  # Logs all lifecycle events to console
    session_service=session_service,
)
```

### OpenTelemetry + GCP (Production)

```python
from google.adk.telemetry import maybe_set_otel_providers
from google.adk.telemetry.google_cloud import get_gcp_exporters, get_gcp_resource

# Setup exporters before runner
maybe_set_otel_providers(
    otel_hooks_to_setup=[
        get_gcp_exporters(
            enable_cloud_tracing=True,
            enable_cloud_logging=True,
            enable_cloud_metrics=True,
        )
    ],
    otel_resource=get_gcp_resource(project_id="my-project"),
)
```

## End-to-End Workflow Logging

The ADK execution flow generates logs/traces at these points:

```
User Message → on_user_message_callback
    ↓
Runner Start → before_run_callback
    ↓
Agent Start → before_agent_callback
    ↓
LLM Request → before_model_callback → trace_call_llm
    ↓
LLM Response → after_model_callback (or on_model_error_callback)
    ↓
Tool Call → before_tool_callback → trace_tool_call
    ↓
Tool Result → after_tool_callback (or on_tool_error_callback)
    ↓
Event Yield → on_event_callback
    ↓
Agent End → after_agent_callback
    ↓
Runner End → after_run_callback
```

## Using LoggingPlugin

LoggingPlugin prints formatted logs for each callback with session, agent, tool, and event details.

```python
from google.adk.plugins import LoggingPlugin

# Default name
plugin = LoggingPlugin()

# Custom name for multiple plugins
plugin = LoggingPlugin(name="my_logger")

runner = Runner(
    agents=[my_agent],
    plugins=[plugin],
    session_service=session_service,
)
```

**Logged Information:**
- Session ID, User ID, App Name, Invocation ID
- Agent names and execution flow
- LLM model, system instruction, available tools, token usage
- Tool names, arguments, results
- Event content, function calls/responses, final response status
- All errors with context

## Custom Logging Plugin

Create custom plugins for specialized logging needs:

```python
from google.adk.plugins import BasePlugin
from google.adk.events import Event
from typing import Optional, Any

class CustomLoggingPlugin(BasePlugin):
    def __init__(self, log_file: str = "agent.log"):
        super().__init__(name="custom_logger")
        self.log_file = log_file

    async def on_user_message_callback(
        self, *, invocation_context, user_message
    ) -> Optional:
        self._log(f"USER: session={invocation_context.session.id}")
        self._log(f"  state={invocation_context.session.state}")
        return None

    async def on_event_callback(
        self, *, invocation_context, event: Event
    ) -> Optional[Event]:
        self._log(f"EVENT: {event.author} - final={event.is_final_response()}")
        if event.actions and event.actions.state_delta:
            self._log(f"  state_delta={event.actions.state_delta}")
        return None

    async def on_model_error_callback(
        self, *, callback_context, llm_request, error
    ) -> Optional:
        self._log(f"ERROR: model={llm_request.model} error={error}")
        return None

    async def on_tool_error_callback(
        self, *, tool, tool_args, tool_context, error
    ) -> Optional[dict]:
        self._log(f"ERROR: tool={tool.name} error={error}")
        return None

    def _log(self, msg: str):
        with open(self.log_file, "a") as f:
            f.write(f"{msg}\n")
```

## OpenTelemetry Setup

### Environment Variables

```bash
# Capture request/response content in spans (default: true)
export ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=true

# Generic OTLP endpoints (auto-detected by ADK)
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://localhost:4317/v1/traces
export OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=http://localhost:4317/v1/metrics
export OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://localhost:4317/v1/logs

# Resource attributes
export OTEL_SERVICE_NAME=my-agent
export OTEL_RESOURCE_ATTRIBUTES=deployment=prod,version=1.0
```

### Manual OTLP Setup

```python
from google.adk.telemetry.setup import maybe_set_otel_providers, OTelHooks
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

hooks = OTelHooks(
    span_processors=[BatchSpanProcessor(OTLPSpanExporter())],
)
maybe_set_otel_providers(otel_hooks_to_setup=[hooks])
```

### GCP Cloud Exports

```python
from google.adk.telemetry.google_cloud import get_gcp_exporters, get_gcp_resource

exporters = get_gcp_exporters(
    enable_cloud_tracing=True,   # Export to Cloud Trace
    enable_cloud_logging=True,   # Export to Cloud Logging
    enable_cloud_metrics=True,   # Export to Cloud Monitoring
    google_auth=None,            # Uses google.auth.default()
)

resource = get_gcp_resource(project_id="my-project")

maybe_set_otel_providers(
    otel_hooks_to_setup=[exporters],
    otel_resource=resource,
)
```

## Trace Attributes

ADK adds these attributes to spans:

| Attribute | Description |
|-----------|-------------|
| `gen_ai.system` | `gcp.vertex.agent` |
| `gen_ai.agent.name` | Agent name |
| `gen_ai.agent.description` | Agent description |
| `gen_ai.conversation.id` | Session ID |
| `gen_ai.operation.name` | `invoke_agent`, `execute_tool` |
| `gen_ai.tool.name` | Tool name |
| `gen_ai.tool.call.id` | Function call ID |
| `gen_ai.request.model` | LLM model name |
| `gen_ai.usage.input_tokens` | Input token count |
| `gen_ai.usage.output_tokens` | Output token count |
| `gcp.vertex.agent.session_id` | Session ID |
| `gcp.vertex.agent.invocation_id` | Invocation ID |
| `gcp.vertex.agent.event_id` | Event ID |
| `gcp.vertex.agent.llm_request` | JSON of LLM request |
| `gcp.vertex.agent.llm_response` | JSON of LLM response |
| `gcp.vertex.agent.tool_call_args` | JSON of tool arguments |
| `gcp.vertex.agent.tool_response` | JSON of tool response |

## Logging Session & State

Track session and state changes through events:

```python
class SessionStateLogger(BasePlugin):
    def __init__(self):
        super().__init__(name="session_state_logger")

    async def on_user_message_callback(self, *, invocation_context, user_message):
        session = invocation_context.session
        print(f"[SESSION] id={session.id} user={session.user_id}")
        print(f"[STATE] {session.state}")
        return None

    async def on_event_callback(self, *, invocation_context, event):
        if event.actions and event.actions.state_delta:
            print(f"[STATE_DELTA] {event.actions.state_delta}")
        if event.actions and event.actions.transfer_to_agent:
            print(f"[TRANSFER] → {event.actions.transfer_to_agent}")
        return None

    async def after_run_callback(self, *, invocation_context):
        session = invocation_context.session
        print(f"[SESSION_END] events={len(session.events)}")
        return None
```

## Error Handling & Monitoring

```python
class ErrorMonitorPlugin(BasePlugin):
    def __init__(self, alert_callback=None):
        super().__init__(name="error_monitor")
        self.alert_callback = alert_callback
        self.errors = []

    async def on_model_error_callback(
        self, *, callback_context, llm_request, error
    ):
        self.errors.append({
            "type": "model",
            "agent": callback_context.agent_name,
            "model": llm_request.model,
            "error": str(error),
        })
        if self.alert_callback:
            self.alert_callback(f"Model error: {error}")
        return None  # Let error propagate

    async def on_tool_error_callback(
        self, *, tool, tool_args, tool_context, error
    ):
        self.errors.append({
            "type": "tool",
            "tool": tool.name,
            "args": tool_args,
            "error": str(error),
        })
        if self.alert_callback:
            self.alert_callback(f"Tool error in {tool.name}: {error}")
        return None  # Let error propagate
```

## Common Patterns

### Combine LoggingPlugin with Custom Plugin

```python
runner = Runner(
    agents=[my_agent],
    plugins=[
        LoggingPlugin(),           # Console debug logging
        ErrorMonitorPlugin(),       # Error tracking
        SessionStateLogger(),       # State change tracking
    ],
    session_service=session_service,
)
```

### Production Setup with Full Observability

```python
from google.adk.telemetry import maybe_set_otel_providers
from google.adk.telemetry.google_cloud import get_gcp_exporters, get_gcp_resource
from google.adk.plugins import LoggingPlugin

# 1. Setup OpenTelemetry before creating runner
maybe_set_otel_providers(
    otel_hooks_to_setup=[
        get_gcp_exporters(
            enable_cloud_tracing=True,
            enable_cloud_logging=True,
            enable_cloud_metrics=True,
        )
    ],
    otel_resource=get_gcp_resource(project_id="my-project"),
)

# 2. Create runner with plugins
runner = Runner(
    agents=[my_agent],
    plugins=[
        ErrorMonitorPlugin(alert_callback=send_alert),
    ],
    session_service=session_service,
)
```

## Troubleshooting

### Logs Not Appearing

1. Verify plugin is added to Runner `plugins` list
2. Check plugin callbacks return `None` (not empty dict or other value)
3. For GCP, verify IAM permissions for Cloud Logging/Trace

### Missing Span Attributes

1. Check `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=true`
2. For GCP exports, verify credentials: `gcloud auth application-default login`

### High Log Volume

1. Create selective logging plugin that filters by agent/tool
2. Use `GetSessionConfig(num_recent_events=N)` to limit event loading

## Resources

- [references/logging_plugin_api.md](references/logging_plugin_api.md) - Complete callback API
- [references/telemetry_setup_api.md](references/telemetry_setup_api.md) - OpenTelemetry configuration
