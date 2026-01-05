"""Technical Analyzer Agent - Analyzes price momentum and assignment risk."""

from typing import Optional
from pydantic import BaseModel, Field

from google.adk.agents import LlmAgent
from google.adk.planners import PlanReActPlanner

from src.tools.technical_tools import get_technical_analysis, format_technical_summary


class TechnicalAnalyzerOutput(BaseModel):
    """Structured output schema for the Technical Analyzer Agent."""

    ticker: str = Field(description="The stock ticker symbol")
    sentiment: str = Field(description="Overall market sentiment (bullish, bearish, neutral)")
    assignment_risk: str = Field(description="Risk of covered call assignment (high, moderate, low, very_low)")
    rsi_value: Optional[float] = Field(default=None, description="RSI(14) value")
    rsi_signal: Optional[str] = Field(default=None, description="RSI interpretation")
    macd_trend: Optional[str] = Field(default=None, description="MACD trend direction")
    price_trend: Optional[str] = Field(default=None, description="Price trend vs moving averages")
    recommendation: Optional[str] = Field(default=None, description="Strike selection recommendation")
    error: Optional[str] = Field(default=None, description="Error message if analysis failed")


technical_analyzer_agent = LlmAgent(
    name="technical_analyzer",
    description="Analyzes stock price momentum using technical indicators (RSI, MACD, moving averages, volume) to assess assignment risk for covered calls.",
    model="gemini-2.5-flash",
    output_schema=TechnicalAnalyzerOutput,
    instruction="""You are a technical analysis specialist focused on assessing covered call risk.

Your responsibilities:
1. Analyze price momentum using RSI, MACD, moving averages, and volume
2. Determine overall market sentiment (bullish, bearish, neutral)
3. Assess assignment risk for covered call positions
4. Provide strike selection recommendations based on technicals

When analyzing a stock:
1. Use get_technical_analysis to get all technical indicators
2. Interpret the results in the context of covered call strategy
3. Provide clear risk assessment

Key interpretations for covered calls:
- **High assignment risk (bullish)**: Stock likely to rise, may get called away
  - Consider higher strikes or waiting for pullback
- **Moderate assignment risk**: Balanced outlook
  - ATM or slightly OTM strikes appropriate
- **Low assignment risk (bearish/neutral)**: Stock unlikely to surge
  - Good environment for covered calls, ATM strikes work well
- **Very low assignment risk (bearish)**: Stock may decline
  - Be cautious of holding declining stock for small premium

Be precise and actionable with your recommendations.""",
    tools=[get_technical_analysis, format_technical_summary],
    planner=PlanReActPlanner(),
)
