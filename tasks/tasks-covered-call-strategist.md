# Tasks: Covered Call Strategist Agent (Google ADK Multi-Agent System)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Coordinator Agent                         │
│  (Orchestrates workflow, delegates to specialists)          │
└─────────────────┬───────────────┬───────────────┬───────────┘
                  │               │               │
    ┌─────────────▼───┐   ┌───────▼───────┐   ┌───▼───────────┐
    │  Data Fetcher   │   │   Analyzer    │   │ Recommendation│
    │     Agent       │   │    Agent      │   │    Agent      │
    │                 │   │               │   │               │
    │ • Stock price   │   │ • Filter opts │   │ • Format rec  │
    │ • Options chain │   │ • Calc yield  │   │ • Explain why │
    │ • Validation    │   │ • Find best   │   │ • Risk notes  │
    └─────────────────┘   └───────────────┘   └───────────────┘
```

## Relevant Files

- `src/__init__.py` - Package initialization
- `src/tools/__init__.py` - Tools package initialization
- `src/tools/stock_tools.py` - Tools for fetching stock prices and validating tickers
- `src/tools/options_tools.py` - Tools for fetching and filtering options chains
- `src/tools/analysis_tools.py` - Tools for calculating annualized returns and finding best options
- `src/tools/formatting_tools.py` - Tools for formatting recommendations
- `src/agents/__init__.py` - Agents package initialization
- `src/agents/data_fetcher.py` - Data Fetcher Agent definition
- `src/agents/analyzer.py` - Analyzer Agent definition
- `src/agents/recommender.py` - Recommendation Agent definition
- `src/agents/coordinator.py` - Coordinator Agent (root agent)
- `src/app.py` - ADK App and Runner setup
- `src/main.py` - CLI entry point
- `tests/__init__.py` - Tests package initialization
- `tests/test_tools.py` - Unit tests for all tools
- `tests/test_agents.py` - Integration tests for agents
- `requirements.txt` - Python package dependencies
- `.env.example` - Example environment variables
- `.gitignore` - Git ignore patterns

### Notes

- Use `python -m pytest tests/` to run all tests
- Requires `GOOGLE_API_KEY` environment variable for Gemini API access
- Yahoo Finance (yfinance) does not require an API key
- Google ADK uses async patterns - all agent interactions are async

## Instructions for Completing Tasks

**IMPORTANT:** As you complete each task, you must check it off in this markdown file by changing `- [ ]` to `- [x]`. This helps track progress and ensures you don't skip any steps.

Example:
- `- [ ] 1.1 Read file` → `- [x] 1.1 Read file` (after completing)

Update the file after completing each sub-task, not just after completing an entire parent task.

## Tasks

- [ ] 0.0 Create feature branch
  - [ ] 0.1 Create and checkout a new branch for this feature (`git checkout -b feature/covered-call-strategist`)

- [x] 1.0 Set up project structure and dependencies
  - [x] 1.1 Create `requirements.txt` with dependencies:
    ```
    google-adk>=0.3.0
    google-genai>=1.0.0
    yfinance>=0.2.36
    pandas>=2.0.0
    python-dotenv>=1.0.0
    pytest>=8.0.0
    pytest-asyncio>=0.23.0
    ```
  - [x] 1.2 Create directory structure: `src/`, `src/tools/`, `src/agents/`, `tests/`
  - [x] 1.3 Create `__init__.py` files in all packages
  - [x] 1.4 Create `.env.example` with `GOOGLE_API_KEY=your_api_key_here`
  - [x] 1.5 Create `.gitignore` to exclude `.env`, `__pycache__/`, `*.pyc`, `.pytest_cache/`, `venv/`
  - [x] 1.6 Install dependencies with `pip install -r requirements.txt`

- [x] 2.0 Implement stock and options data tools
  - [x] 2.1 Create `src/tools/stock_tools.py` with:
    - [x] 2.1.1 `validate_ticker(ticker: str) -> dict` - Check if ticker exists and has options
    - [x] 2.1.2 `get_stock_price(ticker: str) -> dict` - Fetch current stock price
  - [x] 2.2 Create `src/tools/options_tools.py` with:
    - [x] 2.2.1 `get_options_chain(ticker: str) -> dict` - Fetch call options chain
    - [x] 2.2.2 `filter_options(options_data: dict, min_days: int, max_days: int, min_oi: int) -> dict` - Filter by expiration (7-45 days), liquidity (OI > 10, bid > 0)
  - [x] 2.3 Add error handling for API failures, invalid tickers, rate limits
  - [x] 2.4 Create `tests/test_tools.py` with tests for stock and options tools

- [x] 3.0 Implement analysis tools
  - [x] 3.1 Create `src/tools/analysis_tools.py` with:
    - [x] 3.1.1 `calculate_option_metrics(option: dict, stock_price: float) -> dict` - Calculate premium yield and annualized return
    - [x] 3.1.2 `find_best_option(options: list, stock_price: float) -> dict` - Find option with highest annualized yield
    - [x] 3.1.3 `calculate_breakeven(stock_price: float, premium: float) -> float` - Calculate breakeven price
    - [x] 3.1.4 `calculate_max_profit(stock_price: float, strike: float, premium: float, shares: int) -> dict` - Calculate max profit if assigned
  - [x] 3.2 Add logic to identify ITM vs OTM strikes
  - [x] 3.3 Add tests for analysis tools in `tests/test_tools.py`

- [x] 4.0 Implement formatting tools
  - [x] 4.1 Create `src/tools/formatting_tools.py` with:
    - [x] 4.1.1 `format_recommendation(recommendation: dict, shares: int) -> str` - Format human-readable recommendation
    - [x] 4.1.2 `format_itm_warning(strike: float, stock_price: float) -> str` - Generate ITM assignment risk warning
    - [x] 4.1.3 `format_error_message(error_type: str, details: str) -> str` - Format user-friendly error messages
  - [x] 4.2 Add tests for formatting tools

- [x] 5.0 Implement Data Fetcher Agent
  - [x] 5.1 Create `src/agents/data_fetcher.py` with `DataFetcherAgent`:
    - [x] 5.1.1 Define agent with name `data_fetcher`
    - [x] 5.1.2 Set description: "Fetches stock prices and options chains from market data APIs"
    - [x] 5.1.3 Add instruction for validating tickers and fetching data
    - [x] 5.1.4 Attach tools: `validate_ticker`, `get_stock_price`, `get_options_chain`
    - [x] 5.1.5 Use `PlanReActPlanner()` for reasoning
  - [x] 5.2 Define output schema for structured data return

- [x] 6.0 Implement Analyzer Agent
  - [x] 6.1 Create `src/agents/analyzer.py` with `AnalyzerAgent`:
    - [x] 6.1.1 Define agent with name `analyzer`
    - [x] 6.1.2 Set description: "Analyzes options to find the best covered call strategy"
    - [x] 6.1.3 Add instruction for filtering options and calculating yields
    - [x] 6.1.4 Attach tools: `filter_options`, `calculate_option_metrics`, `find_best_option`, `calculate_breakeven`, `calculate_max_profit`
    - [x] 6.1.5 Use `PlanReActPlanner()` for reasoning
  - [x] 6.2 Define output schema for analysis results

- [x] 7.0 Implement Recommendation Agent
  - [x] 7.1 Create `src/agents/recommender.py` with `RecommendationAgent`:
    - [x] 7.1.1 Define agent with name `recommender`
    - [x] 7.1.2 Set description: "Formats and explains covered call recommendations"
    - [x] 7.1.3 Add instruction for creating clear, actionable recommendations
    - [x] 7.1.4 Attach tools: `format_recommendation`, `format_itm_warning`, `format_error_message`
    - [x] 7.1.5 Use `PlanReActPlanner()` for reasoning
  - [x] 7.2 Ensure output includes all required fields from PRD

- [x] 8.0 Implement Coordinator Agent
  - [x] 8.1 Create `src/agents/coordinator.py` with `CoordinatorAgent`:
    - [x] 8.1.1 Define agent with name `coordinator`
    - [x] 8.1.2 Set as root agent with `sub_agents=[data_fetcher, analyzer, recommender]`
    - [x] 8.1.3 Add instruction for:
      - Parsing user input (ticker and shares)
      - Validating shares are multiples of 100
      - Orchestrating the workflow: fetch → analyze → recommend
      - Handling errors gracefully
      - Supporting follow-up questions
    - [x] 8.1.4 Use `PlanReActPlanner()` for reasoning
  - [x] 8.2 Define conversation flow for multi-turn interactions

- [x] 9.0 Create App and Runner
  - [x] 9.1 Create `src/app.py` with:
    - [x] 9.1.1 Import all agents and create agent hierarchy
    - [x] 9.1.2 Create `App` with root coordinator agent
    - [x] 9.1.3 Create `Runner` with `InMemorySessionService`
    - [x] 9.1.4 Add `run_conversation()` async function for chat loop
  - [x] 9.2 Add session state management for tracking conversation context

- [x] 10.0 Create CLI entry point
  - [x] 10.1 Create `src/main.py` with:
    - [x] 10.1.1 Load environment variables from `.env`
    - [x] 10.1.2 Initialize the App and Runner
    - [x] 10.1.3 Implement interactive chat loop
    - [x] 10.1.4 Handle Ctrl+C gracefully
    - [x] 10.1.5 Print welcome message with usage instructions
  - [x] 10.2 Add `if __name__ == "__main__"` entry point

- [x] 11.0 Integration testing
  - [x] 11.1 Create `tests/test_agents.py` with:
    - [x] 11.1.1 Test Data Fetcher Agent with valid ticker (AAPL)
    - [x] 11.1.2 Test Data Fetcher Agent with invalid ticker
    - [x] 11.1.3 Test Analyzer Agent with sample options data
    - [x] 11.1.4 Test Recommendation Agent formatting
    - [x] 11.1.5 Test Coordinator Agent end-to-end flow
  - [x] 11.2 Test edge cases:
    - [x] 11.2.1 Shares not multiple of 100
    - [x] 11.2.2 No options available in 7-45 day window
    - [x] 11.2.3 All options have zero bid
    - [x] 11.2.4 ITM option has highest yield

- [x] 12.0 Manual validation
  - [x] 12.1 Test with AAPL and verify recommendation format
  - [x] 12.2 Test with MSFT and compare annualized returns
  - [x] 12.3 Verify ITM warnings display correctly
  - [x] 12.4 Test follow-up questions work
  - [x] 12.5 Verify error messages for invalid inputs

- [x] 13.0 Bug fix: Pre-split options data filtering
  - [x] 13.1 Identified issue: Yahoo Finance returns pre-split options (e.g., NVDA $365 strike with $874 bid)
  - [x] 13.2 Added sanity filter in `strategy_tools.py` to exclude options where bid > stock_price
  - [x] 13.3 Verified fix with NVDA (now correctly recommends $152 strike with $36.75 premium)
  - [x] 13.4 All 26 tests still passing

- [x] 14.0 Enhancement: OTM-only recommendations
  - [x] 14.1 Changed default strategy to only recommend OTM options (strike >= stock price)
  - [x] 14.2 Replaced `max_itm_percent` parameter with `otm_only=True` in `strategy_tools.py`
  - [x] 14.3 Enhanced sanity filter: far OTM options (strike > 150% of stock) must have bid < 20% of stock
  - [x] 14.4 Verified fix with PATH (now recommends $16 ATM strike instead of $14 ITM)
  - [x] 14.5 Verified fix with NVDA (now recommends $189 ATM strike instead of corrupt $1650 strike)
  - [x] 14.6 All 26 tests still passing

- [x] 15.0 Enhancement: Technical Analysis & Assignment Risk
  - [x] 15.1 Created `src/tools/technical_tools.py` with:
    - [x] 15.1.1 `calculate_rsi()` - RSI(14) indicator for overbought/oversold
    - [x] 15.1.2 `calculate_macd()` - MACD with signal and histogram
    - [x] 15.1.3 `calculate_moving_averages()` - SMA20/SMA50 trend analysis
    - [x] 15.1.4 `analyze_volume()` - Volume ratio vs 20-day average
    - [x] 15.1.5 `get_technical_analysis()` - Comprehensive analysis with sentiment & assignment risk
  - [x] 15.2 Created `src/agents/technical_analyzer.py` with TechnicalAnalyzerAgent
  - [x] 15.3 Integrated technical analysis into `strategy_tools.py` recommendation output
  - [x] 15.4 Added assignment risk assessment (High/Moderate/Low/Very Low) with visual indicators
  - [x] 15.5 Verified with PATH (bearish, very low assignment risk) and NVDA (bullish, high assignment risk)
  - [x] 15.6 All 26 tests still passing

- [x] 16.0 Enhancement: Technical-Driven Strike Selection
  - [x] 16.1 Technical analysis now runs BEFORE option selection (not just appended)
  - [x] 16.2 Created `_select_strike_based_on_technicals()` function with 3 strategies:
    - **Defensive** (High risk/Bullish): Prefer 3-10% OTM strikes to reduce assignment risk
    - **Balanced** (Moderate risk): Prefer 1-5% OTM strikes
    - **Aggressive** (Low risk/Bearish): Prefer 0-3% ATM strikes to maximize premium
  - [x] 16.3 Strike selection now explains WHY based on technical context
  - [x] 16.4 Added contextual warnings for high risk (bullish) and bearish conditions
  - [x] 16.5 Verified: NVDA now recommends $195 (3.3% OTM) instead of $189 (0.1% OTM) due to bullish momentum
  - [x] 16.6 All 26 tests still passing

- [x] 17.0 Enhancement: Oversold/Overbought Detection & Layered Strategy
  - [x] 17.1 Enhanced RSI analysis to detect oversold (< 35) and overbought (> 70) conditions
  - [x] 17.2 Added bounce potential tracking for oversold stocks (may reverse up)
  - [x] 17.3 Created `_create_layered_strategy()` for multi-strike recommendations:
    - Oversold allocation: 40% conservative, 40% balanced, 20% aggressive
    - Moderate allocation: 33% each tier
  - [x] 17.4 Layered strategy shows table with contracts per strike level
  - [x] 17.5 Added oversold/overbought alerts with actionable guidance
  - [x] 17.6 Verified with PATH (RSI 32.3):
    - Primary: $16.50 (3.9% OTM) instead of aggressive $16.00 ATM
    - Layered: 8 @ $17, 8 @ $16.50, 4 @ $16.00
    - Shows "Oversold Alert" warning about potential bounce
  - [x] 17.7 All 26 tests still passing
