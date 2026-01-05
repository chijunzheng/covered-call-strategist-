---
name: google-adk-memory
description: Implement and configure memory services for Google ADK agents. Use when working with agent memory, long-term context storage, or when users need to (1) add memory capabilities to an ADK agent, (2) choose between InMemoryMemoryService, VertexAiMemoryBankService, or VertexAiRagMemoryService, (3) store/retrieve conversation history across sessions, (4) implement custom memory services, or (5) debug memory-related issues in ADK agents.
---

# Google ADK Memory

## Overview

ADK Memory Services enable agents to store and recall information across sessions, providing long-term context and personalization. This skill covers configuration, implementation, and troubleshooting of ADK memory.

## When to Use This Skill

Use this skill when:
- Adding memory/long-term context capabilities to an ADK agent
- Choosing between `InMemoryMemoryService`, `VertexAiMemoryBankService`, or `VertexAiRagMemoryService`
- Configuring Vertex AI Memory Bank or RAG corpus for production
- Implementing a custom memory service by extending `BaseMemoryService`
- Storing or retrieving conversation history across user sessions
- Debugging memory-related issues (memories not being stored/retrieved)
- Understanding how memory integrates with the agent execution flow

## Quick Start

### Development Setup (InMemoryMemoryService)

```python
from google.adk.agents import LlmAgent
from google.adk.memory import InMemoryMemoryService

agent = LlmAgent(
    name="assistant",
    model="gemini-2.0-flash",
    memory_service=InMemoryMemoryService(),
    instruction="You are a helpful assistant with memory."
)
```

### Production Setup (VertexAiMemoryBankService)

```python
from google.adk.memory import VertexAiMemoryBankService

memory_service = VertexAiMemoryBankService(
    project="my-project",
    location="us-central1",
    agent_engine_id="123"  # Your reasoning engine ID
)
```

## Choosing a Memory Service

| Need | Use |
|------|-----|
| Local development/testing | `InMemoryMemoryService` |
| Production with fact extraction | `VertexAiMemoryBankService` |
| Production with RAG corpus | `VertexAiRagMemoryService` |

**Decision factors:**
- **InMemory**: No setup, keyword search, data lost on restart
- **MemoryBank**: Requires Vertex AI agent engine, semantic search, extracts facts automatically
- **RAG**: Requires RAG corpus, vector search, stores full conversations

## Memory Flow in Agents

1. User sends message
2. Agent calls `search_memory(app_name, user_id, query)`
3. Relevant memories added to LLM context
4. LLM generates response with memory context
5. Session ends: `add_session_to_memory(session)` stores new information

## Common Tasks

### Add Memory to Existing Agent

```python
from google.adk.memory import InMemoryMemoryService

# Add to agent constructor
agent = LlmAgent(
    name="existing_agent",
    model="gemini-2.0-flash",
    memory_service=InMemoryMemoryService(),  # Add this
    # ... other existing config
)
```

### Configure VertexAiMemoryBankService

```python
memory_service = VertexAiMemoryBankService(
    project="my-gcp-project",        # GCP project ID
    location="us-central1",           # GCP region
    agent_engine_id="456"             # From reasoningEngines/456
)
```

The `agent_engine_id` is the numeric ID from your Vertex AI reasoning engine resource name.

### Configure VertexAiRagMemoryService

```python
from google.adk.memory import VertexAiRagMemoryService

memory_service = VertexAiRagMemoryService(
    rag_corpus="projects/proj/locations/us-central1/ragCorpora/123",
    similarity_top_k=10,              # Results to return
    vector_distance_threshold=10.0    # Max distance threshold
)
```

### Implement Custom Memory Service

```python
from google.adk.memory import BaseMemoryService
from google.adk.memory.base_memory_service import SearchMemoryResponse
from google.adk.memory import MemoryEntry

class CustomMemoryService(BaseMemoryService):
    async def add_session_to_memory(self, session):
        # Extract and store relevant events
        for event in session.events:
            if event.content and event.content.parts:
                # Store in your backend
                pass

    async def search_memory(self, *, app_name: str, user_id: str, query: str):
        # Query your backend
        memories = []  # Fetch from your storage
        return SearchMemoryResponse(memories=memories)
```

## Troubleshooting

### Memory Not Being Retrieved

1. Verify `app_name` and `user_id` match between storage and retrieval
2. Check that sessions are being added to memory (call `add_session_to_memory`)
3. For keyword search (InMemory), ensure query words appear in stored content

### VertexAiMemoryBankService Errors

- **"Agent Engine ID is required"**: Pass `agent_engine_id` to constructor
- **Permission errors**: Check GCP IAM permissions for Vertex AI
- **No memories returned**: Memory generation is async; wait for processing

### VertexAiRagMemoryService Errors

- **"Rag resources must be set"**: Provide valid `rag_corpus`
- **No results**: Adjust `vector_distance_threshold` (higher = more results)

## Resources

For detailed API documentation, see [references/memory_services_api.md](references/memory_services_api.md).
