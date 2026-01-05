# Covered Call Strategist - Development Progress

## Project Overview

Building an AI agent system that helps stock traders find the optimal covered call options strategy to maximize premium income. Users provide a stock ticker and number of shares, and the agent analyzes the options chain to recommend the best strike and expiration.

---

## Approach: Google ADK Multi-Agent Architecture

We're using **Google Agent Development Kit (ADK)** to build a multi-agent system where specialized agents collaborate:

```
┌─────────────────────────────────────────────────────────────┐
│                    Coordinator Agent                         │
│  (Orchestrates workflow, delegates to specialists)          │
└─────────────────┬───────────────┬───────────────┬───────────┘
                  │               │               │
    ┌─────────────▼───┐   ┌───────▼───────┐   ┌───▼───────────┐
    │  Data Fetcher   │   │   Analyzer    │   │ Recommendation│
    │     Agent       │   │    Agent      │   │    Agent      │
    └─────────────────┘   └───────────────┘   └───────────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Technical Analyzer   │
                    │       Agent           │
                    └───────────────────────┘
```

### Why This Approach?
- **Separation of concerns**: Each agent has a focused responsibility
- **Reusability**: Agents can be reused or replaced independently
- **Scalability**: Easy to add new specialist agents (e.g., risk analysis, portfolio tracking)
- **Maintainability**: Smaller, focused codebases are easier to debug

### Current Orchestration Approach
- Kept the specialist agents, but moved the coordinator to call a single
  end-to-end tool (`run_covered_call_strategy`) to avoid large inter-agent
  payloads and tool-schema issues in ADK 1.x.
- Technical analysis is integrated directly into the strategy tool for
  performance and to drive strike selection decisions.

---

## Steps Completed

### 1. Repository Setup ✅
- Cloned remote repository from `git@github.com:chijunzheng/covered-call-strategist-.git`
- Initialized local development environment

### 2. Product Requirements Document (PRD) ✅
- Created `tasks/prd-covered-call-strategist.md`
- Defined key requirements:
  - Conversational interface (chatbot)
  - Free data source (Yahoo Finance)
  - Optimization for maximum annualized premium yield
  - Target audience: intermediate traders
  - Output: single best recommendation with explanation

**Key Decisions Made:**
| Decision | Resolution |
|----------|------------|
| Expiration window | 7-45 days |
| Liquidity threshold | Open interest > 10 |
| ITM handling | OTM-only by default (changed from original) |

### 3. Task List Generation ✅
- Created `tasks/tasks-covered-call-strategist.md`
- Broke down implementation into 17 parent tasks with detailed sub-tasks
- Designed multi-agent architecture with Google ADK

### 4. Project Structure Setup ✅
- Created directory structure: `src/`, `src/tools/`, `src/agents/`, `tests/`
- Created configuration files:
  - `requirements.txt` - dependencies (google-adk, yfinance, etc.)
  - `.env.example` - environment variable template
  - `.gitignore` - exclusions for Python/env files
  - `pytest.ini` - test configuration

### 5. Tools Implementation ✅

#### Stock Tools (`src/tools/stock_tools.py`)
- `validate_ticker(ticker)` - Validates ticker exists and has options
- `get_stock_price(ticker)` - Fetches current stock price from Yahoo Finance

#### Options Tools (`src/tools/options_tools.py`)
- `get_options_chain(ticker)` - Fetches complete call options chain
- `filter_options(options_data, min_days, max_days, min_oi)` - Filters by 7-45 day window, liquidity

#### Analysis Tools (`src/tools/analysis_tools.py`)
- `calculate_option_metrics(option, stock_price)` - Calculates annualized return, ITM/OTM status
- `find_best_option(filtered_options, stock_price)` - Finds highest yield option
- `calculate_breakeven(stock_price, premium)` - Calculates breakeven and downside protection
- `calculate_max_profit(stock_price, strike, premium, shares)` - Calculates max profit if assigned

#### Formatting Tools (`src/tools/formatting_tools.py`)
- `format_recommendation(...)` - Formats human-readable recommendation
- `format_itm_warning(strike, stock_price)` - Generates ITM assignment warning
- `format_error_message(error_type, details)` - Formats user-friendly errors

#### Technical Tools (`src/tools/technical_tools.py`) - NEW
- `calculate_rsi(prices, period)` - RSI(14) indicator
- `calculate_macd(prices)` - MACD with signal and histogram
- `calculate_moving_averages(prices)` - SMA20/SMA50 trend analysis
- `analyze_volume(ticker_data)` - Volume ratio vs 20-day average
- `get_technical_analysis(ticker)` - Comprehensive analysis with sentiment & assignment risk
- `format_technical_summary(analysis)` - Formats technical analysis output

#### Strategy Tools (`src/tools/strategy_tools.py`) - ENHANCED
- `run_covered_call_strategy(ticker, shares)` - End-to-end workflow
- `_select_strike_based_on_technicals(...)` - Technical-driven strike selection
- `_create_layered_strategy(...)` - Multi-strike ladder recommendations
- `_format_layered_strategy(...)` - Formats layered strategy output
- `_format_integrated_technical_section(...)` - Formats technical analysis with reasoning

### 6. Agents Implementation ✅

#### Data Fetcher Agent (`src/agents/data_fetcher.py`)
- Validates tickers, fetches stock prices and options chains
- Uses `PlanReActPlanner()` for reasoning
- Tools: `validate_ticker`, `get_stock_price`, `get_options_chain`
- Output schema: `DataFetcherOutput` (Pydantic model)

#### Analyzer Agent (`src/agents/analyzer.py`)
- Filters options, calculates metrics, finds best option
- Uses `PlanReActPlanner()` for reasoning
- Tools: `filter_options`, `calculate_option_metrics`, `find_best_option`, `calculate_breakeven`, `calculate_max_profit`
- Output schema: `AnalyzerOutput` (Pydantic model)

#### Recommender Agent (`src/agents/recommender.py`)
- Formats recommendations with explanations and warnings
- Uses `PlanReActPlanner()` for reasoning
- Tools: `format_recommendation`, `format_itm_warning`, `format_error_message`

#### Technical Analyzer Agent (`src/agents/technical_analyzer.py`) - NEW
- Analyzes stock price momentum using RSI, MACD, moving averages, volume
- Assesses assignment risk for covered calls
- Output schema: `TechnicalAnalyzerOutput` (Pydantic model)

#### Coordinator Agent (`src/agents/coordinator.py`)
- Root agent that orchestrates the workflow
- Parses user input (ticker + shares)
- Validates shares are multiples of 100
- Uses `PlanReActPlanner()` for reasoning
- Sub-agents: `data_fetcher`, `analyzer`, `recommender`, `technical_analyzer`

### 7. App & CLI Implementation ✅

#### App Setup (`src/app.py`)
- Creates ADK `App` with coordinator as root agent
- Creates `Runner` with `InMemorySessionService`
- Provides `run_conversation()` and `send_message()` async functions

#### CLI Entry Point (`src/main.py`)
- Loads environment variables from `.env`
- Validates `GOOGLE_API_KEY` is set
- Runs interactive chat loop
- Handles graceful exit (Ctrl+C)

### 8. Test Suite ✅

#### Unit Tests (`tests/test_tools.py`)
- Tests for all stock, options, analysis, and formatting tools
- Mock data tests for filtering and calculations
- Edge case coverage (invalid tickers, zero bids, ITM options)

#### Integration Tests (`tests/test_agents.py`)
- Full workflow tests with real data (AAPL, MSFT)
- Edge case tests (no options in window, ITM selection)
- Input validation tests

**Current test status: 26 passed**

---

## Current Status

### ✅ Implementation Complete

All code has been written:
- 5 tool modules (17+ functions total)
- 5 agent modules (with Pydantic output schemas)
- App and CLI entry point
- Test suite

### ✅ Manual Testing & Validation

Completed:
- Dependencies installed in a local venv
- API key loaded from `.env`
- Tests run (`python -m pytest tests/ -v`) with all 26 passing
- CLI manual run with AAPL returned a formatted recommendation
- ITM warning displayed correctly
- MSFT analysis verified
- Follow-up questions work (session context maintained across turns)
- Error messages verified for invalid inputs
- Technical analysis integration verified
- Layered strategy verified for oversold conditions

---

## Bug Fixes Applied

### 1. Pre-split Options Data Filter
**Problem:** Yahoo Finance returns corrupt pre-split options data (e.g., NVDA $365 strike with $874 bid when stock is $188).

**Solution:** Added sanity checks in `strategy_tools.py`:
- Excludes options where bid > stock_price
- Excludes far OTM options (strike > 150% of stock) with unrealistic bids (> 20% of stock)

### 2. Deep ITM Recommendations
**Problem:** System was recommending deep ITM options where "premium" was mostly intrinsic value (e.g., PATH $14 strike when stock is $15.88).

**Solution:** Changed default to OTM-only recommendations (strike >= stock price).

---

## Enhancements Applied

### 1. OTM-Only Recommendations
Changed default to only recommend ATM/OTM options (strike >= stock price). This prevents recommending deep ITM options where the "premium" is mostly intrinsic value rather than income.

### 2. Technical Analysis & Assignment Risk
Added comprehensive technical analysis to assess the risk of the stock rising above the strike price:
- RSI(14) for overbought/oversold conditions
- MACD for trend direction and momentum
- SMA20/SMA50 for price trend analysis
- Volume analysis vs 20-day average
- Overall sentiment (bullish/bearish/neutral)
- Assignment risk rating (🔴 High / 🟡 Moderate / 🟢 Low)

### 3. Technical-Driven Strike Selection
Technical analysis now DRIVES the strike selection, not just displayed:

| Condition | Strategy | Strike Range | Example |
|-----------|----------|--------------|---------|
| Bullish (High Risk) | Defensive | 3-10% OTM | NVDA: $195 (3.3% OTM) |
| Mixed (Moderate) | Balanced | 1-5% OTM | Standard approach |
| Bearish (Low Risk) | Aggressive | 0-3% ATM | Maximize premium |
| Oversold (RSI < 35) | Balanced + Layered | 2-6% OTM | Hedge bounce risk |
| Overbought (RSI > 70) | Aggressive | 0-3% ATM | Pullback expected |

### 4. Oversold/Overbought Detection
Enhanced RSI analysis to detect:
- **Oversold (RSI < 35):** Potential bounce - upgrades assignment risk, uses balanced strikes
- **Overbought (RSI > 70):** Potential pullback - can be more aggressive

### 5. Layered/Ladder Strategy
For uncertain conditions (oversold, moderate risk), provides multi-strike recommendations:

**Example for PATH (2000 shares, oversold):**
| Layer | Contracts | Strike | OTM % |
|-------|-----------|--------|-------|
| Conservative | 8 | $17.00 | 7.1% |
| Balanced | 8 | $16.50 | 3.9% |
| Aggressive | 4 | $16.00 | 0.8% |

Allocation varies by sentiment:
- **Oversold:** 40% conservative, 40% balanced, 20% aggressive
- **Moderate:** 33% each tier

---

## Current Failures/Issues

**None.** All features working correctly. 26 tests passing.

### Potential Issues to Watch:
1. **Google ADK version compatibility** - Ensure `google-adk>=0.3.0` is available
2. **Yahoo Finance rate limiting** - May need to add caching/retry logic
3. **Weekend/after-hours data** - Options data may be stale outside market hours

---

## Sample Output

### PATH (Oversold Stock, 2000 shares)
```
**Recommendation: Sell 20 PATH $16.50 Calls expiring 2026-01-16**

- **Current Stock Price:** $15.88
- **Strike Price:** $16.50 (OTM, 3.9% above current price)
- **Premium:** $0.36 per share
- **Total Premium Income:** $720.00
- **Annualized Return:** 61.3%

---

**📊 Alternative: Layered Strategy (Recommended for Uncertainty)**

| Layer        | Contracts | Strike  | Premium/Share | OTM %  |
|--------------|-----------|---------|---------------|--------|
| Conservative | 8         | $17.00  | $0.24         | 7.1%   |
| Balanced     | 8         | $16.50  | $0.36         | 3.9%   |
| Aggressive   | 4         | $16.00  | $0.56         | 0.8%   |

**Total Premium:** $704.00

---

**📊 Technical Analysis & Strike Selection**

**Market Sentiment:** Oversold Bounce Risk | **Assignment Risk:** 🟡 Moderate

| Indicator | Value   | Signal   |
|-----------|---------|----------|
| RSI(14)   | 32.3    | Oversold |
| MACD      | -0.1437 | Bearish  |
| vs SMA20  | $17.11  | Below ✗  |
| vs SMA50  | $15.58  | Above ✓  |

**🎯 Strategy: Balanced** (3.9% OTM)

**Why this strike?** Stock is oversold (RSI < 30) with potential bounce.

⚠️ **Oversold Alert:** Stock may bounce up!
- Consider the layered strategy above to hedge bounce risk
- Or wait for confirmation before selling calls
```

---

## File Structure

```
covered-call-strategist/
├── .env.example
├── .gitignore
├── progress.md              # This file
├── pytest.ini
├── requirements.txt
├── README.md
├── src/
│   ├── __init__.py
│   ├── app.py
│   ├── main.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── coordinator.py
│   │   ├── data_fetcher.py
│   │   ├── analyzer.py
│   │   ├── recommender.py
│   │   └── technical_analyzer.py  # Technical analysis agent
│   └── tools/
│       ├── __init__.py
│       ├── stock_tools.py
│       ├── options_tools.py
│       ├── analysis_tools.py
│       ├── formatting_tools.py
│       ├── strategy_tools.py      # Main workflow + layered strategy
│       └── technical_tools.py     # RSI, MACD, SMA, volume analysis
├── tasks/
│   ├── prd-covered-call-strategist.md
│   └── tasks-covered-call-strategist.md
└── tests/
    ├── __init__.py
    ├── test_tools.py
    └── test_agents.py
```

---

## Next Steps

1. **Install & Configure**
   ```bash
   pip install -r requirements.txt
   cp .env.example .env
   # Add GOOGLE_API_KEY to .env
   ```

2. **Run Tests**
   ```bash
   python -m pytest tests/ -v
   ```

3. **Run the Agent**
   ```bash
   python -m src.main
   ```

4. **Example Usage**
   ```
   You: I have 2000 shares of PATH
   Strategist: [Recommendation with technical analysis + layered strategy]
   ```

---

## Session Summary (Latest)

### What We Did This Session:

1. **Added Pydantic Output Schemas** to Data Fetcher and Analyzer agents for structured output

2. **Fixed Pre-split Options Bug** - NVDA was showing $365 strike with $874 bid (corrupt Yahoo Finance data)

3. **Changed to OTM-Only Recommendations** - Stopped recommending deep ITM options where premium = intrinsic value

4. **Added Technical Analysis Integration:**
   - RSI, MACD, SMA20/SMA50, Volume analysis
   - Assignment risk assessment (High/Moderate/Low)
   - Created Technical Analyzer agent

5. **Implemented Technical-Driven Strike Selection:**
   - Strike selection now based on technical analysis, not just highest yield
   - Defensive strategy for bullish stocks (higher OTM)
   - Aggressive strategy for bearish stocks (ATM)

6. **Added Oversold/Overbought Detection:**
   - RSI < 35 triggers "oversold bounce risk" - upgrades assignment risk
   - RSI > 70 triggers "overbought pullback" - can be more aggressive

7. **Implemented Layered Strategy:**
   - For uncertain conditions, splits contracts across multiple strikes
   - Conservative/Balanced/Aggressive allocation based on sentiment
   - Shows table with contracts per strike level

### Tests Status: 26 passed
