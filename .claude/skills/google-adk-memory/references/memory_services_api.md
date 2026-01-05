# ADK Memory Services API Reference

## Overview

ADK provides memory services to store and retrieve conversation context across sessions. Memory enables agents to recall past interactions and provide personalized, context-aware responses.

## Core Classes

### MemoryEntry

Represents a single memory entry.

```python
from google.adk.memory import MemoryEntry
from google.genai import types

entry = MemoryEntry(
    content=types.Content(parts=[types.Part(text="User prefers dark mode")]),
    author="user",  # Optional
    timestamp="2025-01-02T10:30:00"  # Optional, ISO 8601 format
)
```

**Attributes:**
- `content: types.Content` - The main content of the memory
- `author: Optional[str]` - The author of the memory (e.g., "user", "model")
- `timestamp: Optional[str]` - When the content was created (ISO 8601 format)

### SearchMemoryResponse

Response from a memory search operation.

```python
from google.adk.memory.base_memory_service import SearchMemoryResponse

response = SearchMemoryResponse(memories=[entry1, entry2])
```

**Attributes:**
- `memories: list[MemoryEntry]` - List of memory entries matching the search query

## Memory Service Implementations

### BaseMemoryService (Abstract)

Abstract base class defining the memory service interface.

```python
from google.adk.memory import BaseMemoryService

class CustomMemoryService(BaseMemoryService):
    async def add_session_to_memory(self, session: Session):
        # Store session events in memory
        pass

    async def search_memory(
        self, *, app_name: str, user_id: str, query: str
    ) -> SearchMemoryResponse:
        # Search for relevant memories
        pass
```

**Methods:**
- `add_session_to_memory(session)` - Stores session events into memory
- `search_memory(app_name, user_id, query)` - Searches for memories matching a query

---

### InMemoryMemoryService

Simple in-memory implementation using keyword matching. **For prototyping only.**

```python
from google.adk.memory import InMemoryMemoryService

memory_service = InMemoryMemoryService()
```

**Characteristics:**
- Thread-safe (uses threading.Lock)
- Keyword-based matching (not semantic search)
- Data lost on restart
- No external dependencies

**How it works:**
1. `add_session_to_memory()`: Stores events keyed by `{app_name}/{user_id}`
2. `search_memory()`: Finds events where query words appear in event text

---

### VertexAiMemoryBankService

Production-ready memory service using Vertex AI Memory Bank.

```python
from google.adk.memory import VertexAiMemoryBankService

memory_service = VertexAiMemoryBankService(
    project="my-gcp-project",
    location="us-central1",
    agent_engine_id="456"  # From reasoningEngines/456
)
```

**Constructor Parameters:**
- `project: Optional[str]` - GCP project ID
- `location: Optional[str]` - GCP location (e.g., "us-central1")
- `agent_engine_id: Optional[str]` - The reasoning engine ID (e.g., "456" from `projects/my-project/locations/us-central1/reasoningEngines/456`)

**Characteristics:**
- Uses Vertex AI Memory Bank for persistent storage
- Semantic similarity search
- Extracts facts from conversations automatically
- Requires agent_engine_id for all operations

**How it works:**
1. `add_session_to_memory()`:
   - Converts session events to content dictionaries
   - Calls `client.agent_engines.memories.generate()` with session scope
   - Memory generation is async (`wait_for_completion=False`)

2. `search_memory()`:
   - Calls `client.agent_engines.memories.retrieve()` with similarity search
   - Returns extracted facts as MemoryEntry objects

---

### VertexAiRagMemoryService

Memory service using Vertex AI RAG (Retrieval Augmented Generation).

```python
from google.adk.memory import VertexAiRagMemoryService

memory_service = VertexAiRagMemoryService(
    rag_corpus="projects/my-project/locations/us-central1/ragCorpora/123",
    similarity_top_k=10,
    vector_distance_threshold=10.0
)
```

**Constructor Parameters:**
- `rag_corpus: Optional[str]` - RAG corpus name. Format: `projects/{project}/locations/{location}/ragCorpora/{id}` or just `{id}`
- `similarity_top_k: Optional[int]` - Number of contexts to retrieve
- `vector_distance_threshold: float` - Maximum vector distance for results (default: 10)

**Characteristics:**
- Uses Vertex AI RAG for vector-based retrieval
- Stores conversations as text files in RAG corpus
- Semantic search via vector embeddings
- Requires existing RAG corpus

**How it works:**
1. `add_session_to_memory()`:
   - Writes session events to a temp file as JSON lines
   - Uploads to RAG corpus via `rag.upload_file()`
   - Uses `display_name` format: `{app_name}.{user_id}.{session_id}`

2. `search_memory()`:
   - Calls `rag.retrieval_query()` for vector search
   - Filters results by `{app_name}.{user_id}` prefix
   - Merges overlapping event lists from same session

## Integration with Agent

### Configuring Memory on an Agent

```python
from google.adk.agents import LlmAgent
from google.adk.memory import InMemoryMemoryService

memory_service = InMemoryMemoryService()

agent = LlmAgent(
    name="my_agent",
    model="gemini-2.0-flash",
    memory_service=memory_service,
    # ... other config
)
```

### How Memory Works in Agent Flow

1. **Before LLM call**: Agent calls `search_memory()` with user's query
2. **During LLM call**: Relevant memories are included in context
3. **After session ends**: Agent calls `add_session_to_memory()` to store new information

## Choosing a Memory Service

| Service | Use Case | Persistence | Search Type |
|---------|----------|-------------|-------------|
| `InMemoryMemoryService` | Development/testing | None | Keyword |
| `VertexAiMemoryBankService` | Production | Vertex AI | Semantic |
| `VertexAiRagMemoryService` | Production with RAG | Vertex AI RAG | Vector |

## Example: Complete Setup

```python
from google.adk.agents import LlmAgent
from google.adk.memory import VertexAiMemoryBankService
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner

# Configure memory
memory_service = VertexAiMemoryBankService(
    project="my-project",
    location="us-central1",
    agent_engine_id="123"
)

# Configure session
session_service = InMemorySessionService()

# Create agent with memory
agent = LlmAgent(
    name="assistant",
    model="gemini-2.0-flash",
    memory_service=memory_service,
    instruction="You are a helpful assistant with long-term memory."
)

# Create runner
runner = Runner(
    agent=agent,
    session_service=session_service,
    app_name="my_app"
)

# Run with user
async for event in runner.run(user_id="user123", new_message="Hello!"):
    print(event)
```
