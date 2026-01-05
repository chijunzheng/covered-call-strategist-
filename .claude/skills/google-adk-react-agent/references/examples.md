# ReAct Agent Examples

Complete working examples for various ReAct agent patterns.

## Basic ReAct Agent

```python
from google.adk.agents import LlmAgent
from google.adk.planners import PlanReActPlanner
from google.adk.apps import App
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Define tools
def search_web(query: str) -> dict:
    """Search the web for information.

    Args:
        query: The search query.

    Returns:
        Search results with titles and snippets.
    """
    # Simulated search results
    return {
        "results": [
            {"title": "Result 1", "snippet": "Information about " + query},
            {"title": "Result 2", "snippet": "More details on " + query},
        ]
    }

def calculate(expression: str) -> dict:
    """Evaluate a mathematical expression.

    Args:
        expression: Math expression to evaluate (e.g., "2 + 2").

    Returns:
        The calculated result.
    """
    try:
        result = eval(expression)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

# Create the ReAct agent
react_agent = LlmAgent(
    name="react_assistant",
    model="gemini-2.0-flash",
    instruction="""You are a helpful research assistant.
    Use the available tools to find information and perform calculations.
    Always explain your reasoning.""",
    tools=[search_web, calculate],
    planner=PlanReActPlanner(),
)

# Create the app
app = App(name="react_app", root_agent=react_agent)

# Run the agent
async def main():
    session_service = InMemorySessionService()
    runner = Runner(app=app, session_service=session_service)

    session = await session_service.create_session(
        app_name="react_app",
        user_id="user_123"
    )

    async for event in runner.run_async(
        session_id=session.id,
        user_id="user_123",
        new_message="What is 15% of 250?"
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text and not part.thought:
                    print(part.text)

import asyncio
asyncio.run(main())
```

## Multi-Tool Research Agent

```python
from google.adk.agents import LlmAgent
from google.adk.planners import PlanReActPlanner
from google.adk.tools import ToolContext

def search_documents(query: str, tool_context: ToolContext) -> dict:
    """Search internal documents.

    Args:
        query: Search query for documents.

    Returns:
        Matching documents with relevance scores.
    """
    # Track search in state
    searches = tool_context.state.get("searches", [])
    searches.append(query)
    tool_context.state["searches"] = searches

    return {
        "documents": [
            {"title": "Policy Doc", "content": "...", "score": 0.95},
            {"title": "Procedure", "content": "...", "score": 0.87},
        ]
    }

def fetch_url(url: str) -> dict:
    """Fetch content from a URL.

    Args:
        url: The URL to fetch.

    Returns:
        Page content and metadata.
    """
    return {"content": f"Content from {url}", "status": 200}

def summarize_text(text: str, max_length: int = 100) -> dict:
    """Summarize text to specified length.

    Args:
        text: Text to summarize.
        max_length: Maximum summary length in words.

    Returns:
        Summarized text.
    """
    words = text.split()[:max_length]
    return {"summary": " ".join(words)}

research_agent = LlmAgent(
    name="researcher",
    model="gemini-1.5-pro",
    instruction="""You are a research assistant that gathers and synthesizes information.

    Your process:
    1. Search internal documents first
    2. Fetch external sources if needed
    3. Summarize key findings
    4. Present a comprehensive answer

    Always cite your sources.""",
    tools=[search_documents, fetch_url, summarize_text],
    planner=PlanReActPlanner(),
)
```

## Agent with Structured Output

```python
from pydantic import BaseModel, Field
from typing import List
from google.adk.agents import LlmAgent
from google.adk.planners import PlanReActPlanner

class ResearchReport(BaseModel):
    """Structured research report."""
    question: str = Field(description="The original question")
    summary: str = Field(description="Executive summary of findings")
    sources: List[str] = Field(description="List of sources consulted")
    confidence: float = Field(description="Confidence score 0-1")
    key_findings: List[str] = Field(description="Main findings")

def search(query: str) -> dict:
    """Search for information."""
    return {"results": ["Finding 1", "Finding 2"]}

structured_agent = LlmAgent(
    name="structured_researcher",
    model="gemini-1.5-pro",
    instruction="""Research the question and provide a structured report.
    Be thorough and cite all sources.""",
    tools=[search],
    planner=PlanReActPlanner(),
    output_schema=ResearchReport,
    output_key="report",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
```

## Multi-Agent System with Coordinator

```python
from google.adk.agents import LlmAgent
from google.adk.planners import PlanReActPlanner

# Specialist: Data Analyst
def query_database(sql: str) -> dict:
    """Execute SQL query."""
    return {"rows": [{"id": 1, "value": 100}], "count": 1}

data_analyst = LlmAgent(
    name="data_analyst",
    description="Analyzes data using SQL queries and statistics",
    model="gemini-1.5-pro",
    instruction="You are a data analyst. Write and execute SQL queries to answer questions.",
    tools=[query_database],
    planner=PlanReActPlanner(),
)

# Specialist: Writer
def format_document(content: str, format: str = "markdown") -> dict:
    """Format content into a document."""
    return {"document": content, "format": format}

writer = LlmAgent(
    name="writer",
    description="Creates well-written reports and documents",
    model="gemini-1.5-pro",
    instruction="You are a writer. Create clear, well-structured documents.",
    tools=[format_document],
)

# Coordinator
coordinator = LlmAgent(
    name="coordinator",
    model="gemini-1.5-pro",
    instruction="""You are a project coordinator.
    Analyze requests and delegate to the appropriate specialist:
    - data_analyst: for data queries and analysis
    - writer: for creating documents and reports

    Synthesize their work into a final deliverable.""",
    sub_agents=[data_analyst, writer],
    planner=PlanReActPlanner(),
)
```

## LoopAgent for Iterative Tasks

```python
from google.adk.agents import LlmAgent, LoopAgent
from google.adk.planners import PlanReActPlanner
from google.adk.tools import ExitLoopTool, ToolContext

def process_item(item_id: int, tool_context: ToolContext) -> dict:
    """Process a single item from the queue.

    Args:
        item_id: ID of item to process.

    Returns:
        Processing result.
    """
    processed = tool_context.state.get("processed", [])
    processed.append(item_id)
    tool_context.state["processed"] = processed

    return {"item_id": item_id, "status": "completed"}

def check_queue(tool_context: ToolContext) -> dict:
    """Check remaining items in queue.

    Returns:
        Queue status and remaining items.
    """
    processed = tool_context.state.get("processed", [])
    all_items = [1, 2, 3, 4, 5]
    remaining = [i for i in all_items if i not in processed]

    return {"remaining": remaining, "count": len(remaining)}

worker = LlmAgent(
    name="worker",
    model="gemini-2.0-flash",
    instruction="""Process items from the queue one at a time.
    1. Check what items remain
    2. Process the next item
    3. If no items remain, use exit_loop to finish""",
    tools=[process_item, check_queue, ExitLoopTool()],
    planner=PlanReActPlanner(),
)

iterative_processor = LoopAgent(
    name="processor",
    sub_agents=[worker],
    max_iterations=10,  # Safety limit
)
```

## Agent with Callbacks

```python
from google.adk.agents import LlmAgent, CallbackContext
from google.adk.planners import PlanReActPlanner
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools import BaseTool, ToolContext
from typing import Any, Optional

async def log_before_model(
    callback_context: CallbackContext,
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Log before each model call."""
    print(f"[LOG] Model call with {len(llm_request.contents)} messages")
    # Modify request if needed
    # Return LlmResponse to skip model call
    return None

async def log_after_model(
    callback_context: CallbackContext,
    llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Log after each model call."""
    print(f"[LOG] Model responded with {len(llm_response.content.parts)} parts")
    return None

async def log_before_tool(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext
) -> Optional[dict]:
    """Log before each tool call."""
    print(f"[LOG] Calling tool: {tool.name} with args: {args}")
    return None  # Return dict to skip tool execution

async def log_after_tool(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: dict
) -> Optional[dict]:
    """Log after each tool call."""
    print(f"[LOG] Tool {tool.name} returned: {tool_response}")
    return None  # Return dict to override response

def my_tool(query: str) -> dict:
    """Example tool."""
    return {"result": query}

logged_agent = LlmAgent(
    name="logged_agent",
    model="gemini-2.0-flash",
    instruction="You are a helpful assistant.",
    tools=[my_tool],
    planner=PlanReActPlanner(),
    before_model_callback=log_before_model,
    after_model_callback=log_after_model,
    before_tool_callback=log_before_tool,
    after_tool_callback=log_after_tool,
)
```

## Complete App Setup

```python
from google.adk.agents import LlmAgent
from google.adk.planners import PlanReActPlanner
from google.adk.apps import App
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory import InMemoryMemoryService

# Tools
def search(query: str) -> dict:
    """Search for information."""
    return {"results": [f"Result for: {query}"]}

# Agent
agent = LlmAgent(
    name="assistant",
    model="gemini-2.0-flash",
    instruction="You are a helpful assistant.",
    tools=[search],
    planner=PlanReActPlanner(),
)

# App
app = App(name="my_app", root_agent=agent)

# Services
session_service = InMemorySessionService()
artifact_service = InMemoryArtifactService()
memory_service = InMemoryMemoryService()

# Runner
runner = Runner(
    app=app,
    session_service=session_service,
    artifact_service=artifact_service,
    memory_service=memory_service,
)

# Run
async def chat(message: str, user_id: str = "user_1"):
    session = await session_service.create_session(
        app_name="my_app",
        user_id=user_id
    )

    response_text = ""
    async for event in runner.run_async(
        session_id=session.id,
        user_id=user_id,
        new_message=message
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text and not part.thought:
                    response_text += part.text

    return response_text
```
