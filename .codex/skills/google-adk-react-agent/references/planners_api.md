# Planners API Reference

Planners enable agents to generate and execute plans before taking actions.

## Available Planners

```python
from google.adk.planners import (
    BasePlanner,       # Abstract base class
    BuiltInPlanner,    # Uses model's native thinking (requires thinking_config)
    PlanReActPlanner,  # Plan-ReAct pattern with structured tags
)
```

## PlanReActPlanner

The recommended planner for ReAct agents. Implements the Plan-Re-Act pattern without requiring model-specific thinking features.

```python
from google.adk.agents import LlmAgent
from google.adk.planners import PlanReActPlanner

agent = LlmAgent(
    name="react_agent",
    model="gemini-1.5-pro",
    instruction="You are a research assistant.",
    tools=[search_tool, calculator_tool],
    planner=PlanReActPlanner(),
)
```

### How PlanReActPlanner Works

The planner injects instructions that guide the model to:

1. **Plan first** (`/*PLANNING*/`): Create a numbered plan before any action
2. **Execute with reasoning** (`/*ACTION*/` + `/*REASONING*/`): Interleave tool calls with reasoning
3. **Replan if needed** (`/*REPLANNING*/`): Revise the plan based on observations
4. **Final answer** (`/*FINAL_ANSWER*/`): Provide the final response

### Response Tags

| Tag | Purpose |
|-----|---------|
| `/*PLANNING*/` | Initial plan before any action |
| `/*REPLANNING*/` | Revised plan after failed/unexpected results |
| `/*REASONING*/` | Summary of current state and next step |
| `/*ACTION*/` | Tool calls to execute |
| `/*FINAL_ANSWER*/` | Final response to user |

### Example Agent Output Flow

```
/*PLANNING*/
1. Search for information about X
2. Extract relevant data points
3. Calculate the summary statistics
4. Present findings to user

/*ACTION*/
[search_tool call]

/*REASONING*/
Found 5 relevant results. Key data points are A, B, C.
Next step: calculate statistics from these values.

/*ACTION*/
[calculator call]

/*REASONING*/
Calculations complete. Average is 42, median is 38.
All information gathered, ready to present final answer.

/*FINAL_ANSWER*/
Based on my research, here are the findings...
```

## BuiltInPlanner

Uses the model's native thinking/reasoning capabilities (e.g., Gemini's thinking mode).

```python
from google.genai import types
from google.adk.planners import BuiltInPlanner

# Configure thinking
thinking_config = types.ThinkingConfig(
    thinking_budget_tokens=1024,  # Token budget for thinking
)

planner = BuiltInPlanner(thinking_config=thinking_config)

agent = LlmAgent(
    name="thinking_agent",
    model="gemini-2.0-flash",
    instruction="Solve complex problems step by step.",
    planner=planner,
)
```

**Note**: BuiltInPlanner requires model support for thinking features.

## Custom Planner

Create your own planner by extending BasePlanner:

```python
from google.adk.planners import BasePlanner
from google.adk.agents import ReadonlyContext, CallbackContext
from google.adk.models import LlmRequest
from google.genai import types
from typing import List, Optional

class CustomPlanner(BasePlanner):
    """Custom planner with domain-specific planning."""

    def build_planning_instruction(
        self,
        readonly_context: ReadonlyContext,
        llm_request: LlmRequest,
    ) -> Optional[str]:
        """Build system instruction for planning.

        Args:
            readonly_context: Read-only context with session state
            llm_request: The LLM request (read-only)

        Returns:
            Planning instruction string, or None for no instruction
        """
        return """
        Before responding, create a plan:
        1. List the steps needed to answer
        2. Identify which tools to use
        3. Execute the plan systematically
        """

    def process_planning_response(
        self,
        callback_context: CallbackContext,
        response_parts: List[types.Part],
    ) -> Optional[List[types.Part]]:
        """Process the LLM response.

        Args:
            callback_context: Context for callbacks
            response_parts: LLM response parts (read-only)

        Returns:
            Processed parts, or None for no processing
        """
        # Example: Mark planning text as "thought" (hidden from user)
        processed = []
        for part in response_parts:
            if part.text and part.text.startswith("[PLAN]"):
                part.thought = True
            processed.append(part)
        return processed
```

## When to Use Planners

| Scenario | Recommended Planner |
|----------|-------------------|
| Complex multi-step tasks | `PlanReActPlanner` |
| Research and analysis | `PlanReActPlanner` |
| Model supports native thinking | `BuiltInPlanner` |
| Simple Q&A | No planner needed |
| Domain-specific reasoning | Custom planner |

## Planner + Agent Patterns

### Research Agent

```python
research_agent = LlmAgent(
    name="researcher",
    model="gemini-1.5-pro",
    instruction="""
    You are a research assistant. When given a question:
    1. Plan your research approach
    2. Search for relevant information
    3. Synthesize findings
    4. Provide a comprehensive answer with sources
    """,
    tools=[web_search, document_reader],
    planner=PlanReActPlanner(),
)
```

### Problem-Solving Agent

```python
solver_agent = LlmAgent(
    name="solver",
    model="gemini-1.5-pro",
    instruction="""
    You are a problem-solving assistant. For each problem:
    1. Understand the problem fully
    2. Break it into subproblems
    3. Solve each subproblem
    4. Combine solutions
    5. Verify the final answer
    """,
    tools=[calculator, code_executor],
    planner=PlanReActPlanner(),
)
```

### Data Analysis Agent

```python
analyst_agent = LlmAgent(
    name="analyst",
    model="gemini-1.5-pro",
    instruction="""
    You analyze data systematically:
    1. Understand the data and question
    2. Plan the analysis approach
    3. Execute queries and calculations
    4. Interpret results
    5. Present insights clearly
    """,
    tools=[sql_tool, chart_tool],
    planner=PlanReActPlanner(),
)
```

## Best Practices

1. **Use PlanReActPlanner** for most ReAct scenarios - it's model-agnostic
2. **Pair with clear instructions** - tell the agent what steps to follow
3. **Provide appropriate tools** - the planner works best with relevant tools
4. **Consider max_iterations** with LoopAgent for bounded execution
5. **Test with various queries** - ensure planning works for your use cases
