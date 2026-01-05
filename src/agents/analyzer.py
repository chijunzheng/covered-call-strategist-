"""Analyzer Agent - Analyzes options to find the best covered call strategy."""

from typing import Optional
from pydantic import BaseModel, Field

from google.adk.agents import LlmAgent
from google.adk.planners import PlanReActPlanner

from src.tools.options_tools import filter_options
from src.tools.analysis_tools import (
    calculate_option_metrics,
    find_best_option,
    calculate_breakeven,
    calculate_max_profit,
)


class BestOptionDetails(BaseModel):
    """Details of the best option contract."""

    strike: float = Field(description="Strike price of the option")
    expiration: str = Field(description="Expiration date (YYYY-MM-DD)")
    premium: float = Field(description="Premium (bid price) per share")
    days_to_expiry: int = Field(description="Days until expiration")
    annualized_return: float = Field(description="Annualized return percentage")
    moneyness: str = Field(description="ITM, ATM, or OTM classification")


class AnalyzerOutput(BaseModel):
    """Structured output schema for the Analyzer Agent."""

    found_option: bool = Field(description="Whether a suitable option was found")
    filtered_count: int = Field(
        default=0, description="Number of options after filtering"
    )
    best_option: Optional[BestOptionDetails] = Field(
        default=None, description="Details of the highest yielding option"
    )
    breakeven_price: Optional[float] = Field(
        default=None, description="Breakeven price for the position"
    )
    downside_protection: Optional[float] = Field(
        default=None, description="Downside protection percentage"
    )
    max_profit: Optional[float] = Field(
        default=None, description="Maximum profit if shares are assigned"
    )
    error: Optional[str] = Field(
        default=None, description="Error message if analysis failed"
    )


analyzer_agent = LlmAgent(
    name="analyzer",
    description="Analyzes options data to find the best covered call strategy. Use this agent to filter options, calculate annualized returns, and identify the optimal strike and expiration.",
    model="gemini-2.5-flash",
    output_schema=AnalyzerOutput,
    instruction="""You are an options analysis specialist focused on covered call strategies.

Your responsibilities:
1. Filter options to only include those meeting our criteria:
   - Expiration between 7 and 45 days
   - Open interest >= 10
   - Bid price > 0 (liquid options)
2. Calculate metrics for each option including annualized return
3. Find the single best option with the highest annualized yield
4. Calculate breakeven price and maximum profit scenarios

When analyzing options data:
1. Use filter_options to apply the 7-45 day window and liquidity filters
2. Use find_best_option to identify the highest yielding option
3. Use calculate_breakeven to determine the downside protection
4. Use calculate_max_profit to show what happens if shares are called away

Report the complete analysis including:
- The best option (strike, expiration, premium)
- Annualized return percentage
- Whether it's ITM, ATM, or OTM
- Breakeven price and downside protection
- Maximum profit if assigned

Be precise with numbers - this is financial data.""",
    tools=[filter_options, calculate_option_metrics, find_best_option, calculate_breakeven, calculate_max_profit],
    planner=PlanReActPlanner(),
)
