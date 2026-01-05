# OpenTelemetry Telemetry Setup API Reference

## Quick Start

### GCP Cloud Exports (Recommended for Production)

```python
from google.adk.telemetry import maybe_set_otel_providers
from google.adk.telemetry.google_cloud import get_gcp_exporters, get_gcp_resource

# Call ONCE at application startup, BEFORE creating Runner
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

### OTLP Exports (Generic)

```python
from google.adk.telemetry.setup import maybe_set_otel_providers, OTelHooks
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

hooks = OTelHooks(
    span_processors=[BatchSpanProcessor(OTLPSpanExporter())],
)
maybe_set_otel_providers(otel_hooks_to_setup=[hooks])
```

---

## Core Functions

### `maybe_set_otel_providers`

Sets up OpenTelemetry providers for tracing, metrics, and logging.

```python
def maybe_set_otel_providers(
    otel_hooks_to_setup: list[OTelHooks] = None,
    otel_resource: Optional[Resource] = None,
) -> None:
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `otel_hooks_to_setup` | `list[OTelHooks]` | List of hooks containing exporters/processors |
| `otel_resource` | `Optional[Resource]` | OTel resource with attributes (service name, project, etc.) |

**Behavior:**
- Automatically adds OTLP exporters based on environment variables
- Only sets up providers for telemetry types that have hooks configured
- Skips setup if a provider was already set externally (logs warning)

**Note:** This function is marked `@experimental`.

---

### `get_gcp_exporters`

Returns OTel hooks configured for Google Cloud Platform.

```python
def get_gcp_exporters(
    enable_cloud_tracing: bool = False,
    enable_cloud_metrics: bool = False,
    enable_cloud_logging: bool = False,
    google_auth: Optional[tuple[Credentials, str]] = None,
) -> OTelHooks:
```

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_cloud_tracing` | `bool` | `False` | Export spans to Cloud Trace |
| `enable_cloud_metrics` | `bool` | `False` | Export metrics to Cloud Monitoring |
| `enable_cloud_logging` | `bool` | `False` | Export logs to Cloud Logging |
| `google_auth` | `Optional[tuple[Credentials, str]]` | `None` | Custom credentials and project_id. Uses `google.auth.default()` if omitted |

**Returns:** `OTelHooks` with configured processors/readers

**GCP Endpoints:**
- Tracing: `https://telemetry.googleapis.com/v1/traces`
- Metrics: Cloud Monitoring API
- Logging: Cloud Logging API

---

### `get_gcp_resource`

Creates an OTel Resource with GCP-specific attributes.

```python
def get_gcp_resource(project_id: Optional[str] = None) -> Resource:
```

**Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `project_id` | `Optional[str]` | GCP project ID for `gcp.project_id` attribute |

**Behavior:**
1. Sets `gcp.project_id` if provided
2. Merges with `OTELResourceDetector` (reads `OTEL_SERVICE_NAME`, `OTEL_RESOURCE_ATTRIBUTES`)
3. Merges with `GoogleCloudResourceDetector` for GCE/GKE/Cloud Run platform attributes

---

## Data Classes

### `OTelHooks`

Container for OpenTelemetry processors and readers.

```python
@dataclass
class OTelHooks:
    span_processors: list[SpanProcessor] = field(default_factory=list)
    metric_readers: list[MetricReader] = field(default_factory=list)
    log_record_processors: list[LogRecordProcessor] = field(default_factory=list)
```

---

## Environment Variables

### Auto-Detected OTLP Endpoints

| Variable | Description |
|----------|-------------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Base endpoint for all OTLP exports |
| `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` | Traces-specific endpoint |
| `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT` | Metrics-specific endpoint |
| `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` | Logs-specific endpoint |

If any endpoint is set, ADK automatically adds the corresponding OTLP exporter.

### Resource Attributes

| Variable | Description |
|----------|-------------|
| `OTEL_SERVICE_NAME` | Service name for traces/logs |
| `OTEL_RESOURCE_ATTRIBUTES` | Comma-separated key=value pairs (e.g., `deployment=prod,version=1.0`) |

### ADK-Specific

| Variable | Default | Description |
|----------|---------|-------------|
| `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS` | `true` | Include LLM request/response content in spans |
| `GOOGLE_CLOUD_DEFAULT_LOG_NAME` | `adk-otel` | Default log name for Cloud Logging |

---

## Tracing Functions

### `trace_call_llm`

Records LLM request/response details on the current span.

```python
def trace_call_llm(
    invocation_context: InvocationContext,
    event_id: str,
    llm_request: LlmRequest,
    llm_response: LlmResponse,
) -> None:
```

**Span Attributes Set:**
- `gen_ai.system`: `"gcp.vertex.agent"`
- `gen_ai.request.model`: Model name
- `gen_ai.request.top_p`: Top-p parameter (if set)
- `gen_ai.request.max_tokens`: Max output tokens (if set)
- `gen_ai.usage.input_tokens`: Input token count
- `gen_ai.usage.output_tokens`: Output token count
- `gen_ai.response.finish_reasons`: Finish reason list
- `gcp.vertex.agent.invocation_id`: Invocation ID
- `gcp.vertex.agent.session_id`: Session ID
- `gcp.vertex.agent.event_id`: Event ID
- `gcp.vertex.agent.llm_request`: JSON of request (if content capture enabled)
- `gcp.vertex.agent.llm_response`: JSON of response (if content capture enabled)

---

### `trace_tool_call`

Records tool execution details on the current span.

```python
def trace_tool_call(
    tool: BaseTool,
    args: dict[str, Any],
    function_response_event: Event,
) -> None:
```

**Span Attributes Set:**
- `gen_ai.operation.name`: `"execute_tool"`
- `gen_ai.tool.name`: Tool name
- `gen_ai.tool.description`: Tool description
- `gen_ai.tool.type`: Tool class name (e.g., `FunctionTool`)
- `gen_ai.tool.call.id`: Function call ID
- `gcp.vertex.agent.event_id`: Response event ID
- `gcp.vertex.agent.tool_call_args`: JSON of arguments (if content capture enabled)
- `gcp.vertex.agent.tool_response`: JSON of response (if content capture enabled)

---

### `trace_agent_invocation`

Records agent invocation details on a span.

```python
def trace_agent_invocation(
    span: trace.Span,
    agent: BaseAgent,
    ctx: InvocationContext,
) -> None:
```

**Span Attributes Set:**
- `gen_ai.operation.name`: `"invoke_agent"`
- `gen_ai.agent.name`: Agent name
- `gen_ai.agent.description`: Agent description
- `gen_ai.conversation.id`: Session ID

---

### `trace_send_data`

Records data sent to the agent.

```python
def trace_send_data(
    invocation_context: InvocationContext,
    event_id: str,
    data: list[types.Content],
) -> None:
```

---

### `trace_merged_tool_calls`

Records merged tool call events (for parallel tool execution).

```python
def trace_merged_tool_calls(
    response_event_id: str,
    function_response_event: Event,
) -> None:
```

---

## Span Attribute Reference

### Semantic Conventions (gen_ai.*)

| Attribute | Description | Set By |
|-----------|-------------|--------|
| `gen_ai.system` | `"gcp.vertex.agent"` | `trace_call_llm` |
| `gen_ai.agent.name` | Agent name | `trace_agent_invocation` |
| `gen_ai.agent.description` | Agent description | `trace_agent_invocation` |
| `gen_ai.conversation.id` | Session ID | `trace_agent_invocation` |
| `gen_ai.operation.name` | `"invoke_agent"` or `"execute_tool"` | Various |
| `gen_ai.tool.name` | Tool name | `trace_tool_call` |
| `gen_ai.tool.description` | Tool description | `trace_tool_call` |
| `gen_ai.tool.type` | Tool class name | `trace_tool_call` |
| `gen_ai.tool.call.id` | Function call ID | `trace_tool_call` |
| `gen_ai.request.model` | LLM model name | `trace_call_llm` |
| `gen_ai.request.top_p` | Top-p parameter | `trace_call_llm` |
| `gen_ai.request.max_tokens` | Max output tokens | `trace_call_llm` |
| `gen_ai.usage.input_tokens` | Input token count | `trace_call_llm` |
| `gen_ai.usage.output_tokens` | Output token count | `trace_call_llm` |
| `gen_ai.response.finish_reasons` | Finish reason list | `trace_call_llm` |

### ADK-Specific (gcp.vertex.agent.*)

| Attribute | Description |
|-----------|-------------|
| `gcp.vertex.agent.invocation_id` | Invocation ID |
| `gcp.vertex.agent.session_id` | Session ID |
| `gcp.vertex.agent.event_id` | Event ID |
| `gcp.vertex.agent.llm_request` | JSON of LLM request |
| `gcp.vertex.agent.llm_response` | JSON of LLM response |
| `gcp.vertex.agent.tool_call_args` | JSON of tool arguments |
| `gcp.vertex.agent.tool_response` | JSON of tool response |
| `gcp.vertex.agent.data` | JSON of sent data |

---

## Imports

```python
# Setup
from google.adk.telemetry import maybe_set_otel_providers
from google.adk.telemetry.setup import OTelHooks
from google.adk.telemetry.google_cloud import get_gcp_exporters, get_gcp_resource

# Tracing helpers
from google.adk.telemetry.tracing import (
    trace_call_llm,
    trace_tool_call,
    trace_agent_invocation,
    trace_send_data,
    trace_merged_tool_calls,
)

# OpenTelemetry SDK
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
```

---

## IAM Permissions Required (GCP)

For GCP exports, the service account needs:
- **Cloud Trace**: `roles/cloudtrace.agent` or `cloudtrace.traces.patch`
- **Cloud Logging**: `roles/logging.logWriter` or `logging.logEntries.create`
- **Cloud Monitoring**: `roles/monitoring.metricWriter` or `monitoring.timeSeries.create`
