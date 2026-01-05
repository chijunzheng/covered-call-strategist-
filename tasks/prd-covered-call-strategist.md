# PRD: Covered Call Strategist Agent

## 1. Introduction/Overview

The Covered Call Strategist is a conversational AI agent that helps intermediate options traders maximize their covered call premium income. Users provide a stock ticker and number of shares they own, and the agent analyzes available options contracts to recommend the single best covered call strategy optimized for maximum annualized premium yield.

**Problem it solves:** Manually analyzing options chains to find the optimal covered call is time-consuming and requires calculating annualized returns across different strikes and expirations. This agent automates that analysis and delivers a clear, actionable recommendation.

## 2. Goals

1. Provide a single, optimal covered call recommendation that maximizes annualized premium yield
2. Deliver recommendations through a natural conversational interface
3. Source real-time options data from free APIs (Yahoo Finance, Alpha Vantage)
4. Explain the recommendation clearly for intermediate traders
5. Complete analysis and respond within seconds

## 3. User Stories

**US-1:** As an intermediate options trader, I want to input a stock ticker and share count so that I can quickly get the best covered call recommendation without manually scanning the options chain.

**US-2:** As a covered call seller, I want to see the annualized return percentage so that I can compare this opportunity against other income strategies.

**US-3:** As a user, I want to interact with the agent conversationally so that I can ask follow-up questions or adjust my inputs naturally.

**US-4:** As a trader, I want to understand why a specific strike and expiration were recommended so that I can make an informed decision.

## 4. Functional Requirements

### Input Handling
1. The agent MUST accept a stock ticker symbol (e.g., "AAPL", "MSFT")
2. The agent MUST accept the number of shares owned (must be in multiples of 100 for standard contracts)
3. The agent MUST validate that the ticker is valid and has options available
4. The agent MUST handle invalid inputs gracefully with helpful error messages

### Data Retrieval
5. The agent MUST fetch current stock price from a free API (Yahoo Finance or Alpha Vantage)
6. The agent MUST fetch the options chain (calls) for the given stock
7. The agent MUST retrieve bid/ask prices, strike prices, expiration dates, and open interest
8. The agent MUST handle API errors gracefully (rate limits, unavailable data)

### Analysis & Calculation
9. The agent MUST calculate the premium yield for each available call option: `(Premium / Strike Price) * 100`
10. The agent MUST calculate the annualized return: `(Premium Yield / Days to Expiration) * 365`
11. The agent MUST filter out options with insufficient liquidity (open interest < 10, or bid = 0)
12. The agent MUST filter options to only include expirations between 7 and 45 days out
13. The agent MUST consider OTM, ATM, and ITM strikes (ITM allowed if yield is higher)
14. The agent MUST identify the single option with the highest annualized premium yield

### Output
15. The agent MUST provide a single best recommendation including:
    - Strike price
    - Expiration date
    - Premium (bid price)
    - Number of contracts to sell (based on shares owned)
    - Total premium income
    - Annualized return percentage
16. The agent MUST explain why this option was selected (highest annualized yield)
17. The agent MUST display the breakeven price (stock price - premium received)
18. The agent MUST note the maximum profit scenario (stock called away at strike)
19. The agent MUST indicate if the recommended strike is ITM and explain the assignment risk

### Conversational Interface
20. The agent MUST respond in natural language
21. The agent MUST prompt for missing information if user provides incomplete input
22. The agent MUST handle follow-up questions about the recommendation
23. The agent MUST support a new analysis when user provides a different stock

## 5. Non-Goals (Out of Scope)

- **Portfolio management:** The agent will not track multiple positions or overall portfolio performance
- **Trade execution:** The agent will not place trades; it only provides recommendations
- **Premium data sources:** No paid API integrations in initial version
- **Advanced Greeks analysis:** No delta, gamma, theta, vega calculations (keep it simple for MVP)
- **Rolling strategies:** No recommendations for rolling existing positions
- **Tax considerations:** No tax optimization or wash sale tracking
- **Alerts/notifications:** No price alerts or monitoring after recommendation
- **Historical backtesting:** No analysis of past performance of similar strategies

## 6. Design Considerations

### Conversational Flow Example

```
User: I have 500 shares of AAPL

Agent: I'll analyze covered call options for AAPL with your 500 shares (5 contracts).

Fetching current data...

**Recommendation: Sell 5 AAPL $195 Calls expiring Feb 21, 2025**

- Current Stock Price: $188.50
- Strike Price: $195.00 (3.4% above current price)
- Premium: $3.20 per share ($320 per contract)
- Total Premium Income: $1,600
- Days to Expiration: 45
- Annualized Return: 13.8%
- Breakeven: $185.30

**Why this option?** This strike offers the highest annualized premium yield among liquid OTM options. If AAPL stays below $195 by expiration, you keep the $1,600 premium. If called away, your total profit would be $4,850 ($3,250 capital gain + $1,600 premium).

Would you like me to analyze a different stock?
```

### UI/UX Notes
- Keep responses concise but informative
- Use formatting (bold, bullet points) for readability
- Always show the annualized return prominently (primary optimization metric)

## 7. Technical Considerations

- **Data Source:** Start with Yahoo Finance (yfinance Python library) - free, no API key required
- **Fallback:** Alpha Vantage as secondary source (requires free API key)
- **Framework:** Consider LangChain or similar for conversational agent structure
- **Rate Limiting:** Implement caching to avoid hitting API rate limits
- **Calculation Precision:** Use decimal arithmetic for financial calculations

### Key Dependencies
- Stock price API (Yahoo Finance)
- Options chain API (Yahoo Finance)
- Conversational AI framework (LangChain, OpenAI, or Claude API)

## 8. Success Metrics

1. **Accuracy:** Recommendations correctly identify the highest annualized yield option 100% of the time
2. **Response Time:** Agent provides recommendation within 5 seconds of receiving valid input
3. **Data Freshness:** Stock and options prices are no more than 15 minutes delayed
4. **Error Rate:** Less than 5% of valid requests result in errors
5. **User Clarity:** Recommendation includes all required fields (strike, expiration, premium, annualized return)

## 9. Open Questions

1. **Multi-leg strategies:** Future consideration for poor man's covered calls or collar strategies?

## 10. Resolved Decisions

| Decision | Resolution |
|----------|------------|
| Minimum expiration filter | 7 days (to avoid gamma risk) |
| Maximum expiration filter | 45 days (standard covered call timeframe) |
| Liquidity threshold | Open interest > 10 is sufficient |
| ITM handling | Yes, recommend ITM calls if annualized yield is higher (with assignment risk warning) |
