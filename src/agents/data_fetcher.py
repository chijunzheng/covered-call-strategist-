"""Data Fetcher Agent - Fetches stock prices and options chains."""

from typing import Optional
from pydantic import BaseModel, Field

from google.adk.agents import LlmAgent
from google.adk.planners import PlanReActPlanner

from src.tools.stock_tools import validate_ticker, get_stock_price
from src.tools.options_tools import get_options_chain


class DataFetcherOutput(BaseModel):
    """Structured output schema for the Data Fetcher Agent."""

    ticker: str = Field(description="The validated stock ticker symbol")
    is_valid: bool = Field(description="Whether the ticker is valid and has options")
    stock_price: Optional[float] = Field(
        default=None, description="Current stock price"
    )
    options_count: int = Field(
        default=0, description="Number of options retrieved in the 7-45 day window"
    )
    options_data: Optional[list] = Field(
        default=None, description="List of option contracts with strike, expiration, bid, ask, open interest"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if data fetching failed"
    )


data_fetcher_agent = LlmAgent(
    name="data_fetcher",
    description="Fetches stock prices and options chains from market data APIs. Use this agent to validate tickers, get current stock prices, and retrieve options chain data.",
    model="gemini-2.5-flash",
    output_schema=DataFetcherOutput,
    instruction="""You are a data fetching specialist for stock and options data.

Your responsibilities:
1. Validate stock ticker symbols to ensure they exist and have options available
2. Fetch current stock prices
3. Retrieve options chain data for call options in the 7-45 day window

When given a ticker:
1. First validate the ticker using validate_ticker
2. If valid and has options, fetch the stock price using get_stock_price
3. Then fetch the options chain using get_options_chain (7-45 day window)

Always report back with:
- Whether the ticker is valid
- The current stock price (if available)
- The options chain data (if available)
- Any errors encountered

Be precise and report the raw data - analysis will be done by the analyzer agent.""",
    tools=[validate_ticker, get_stock_price, get_options_chain],
    planner=PlanReActPlanner(),
)
