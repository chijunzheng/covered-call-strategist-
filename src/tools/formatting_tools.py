"""Tools for formatting recommendations and messages."""


def format_recommendation(
    ticker: str,
    stock_price: float,
    best_option: dict,
    shares: int,
    breakeven: dict,
    max_profit: dict,
) -> dict:
    """Format a complete covered call recommendation.

    Args:
        ticker: Stock ticker symbol.
        stock_price: Current stock price.
        best_option: Best option metrics from find_best_option.
        shares: Number of shares owned.
        breakeven: Breakeven calculation from calculate_breakeven.
        max_profit: Max profit calculation from calculate_max_profit.

    Returns:
        A dict with formatted recommendation text.
    """
    try:
        contracts = shares // 100
        strike = best_option["strike"]
        expiration = best_option["expiration"]
        premium = best_option["premium"]
        annualized_return = best_option["annualized_return"]
        days_to_expiry = best_option["days_to_expiry"]
        moneyness = best_option["moneyness"]
        is_itm = best_option["is_itm"]

        moneyness_label = "ITM" if is_itm else ("ATM" if abs(moneyness) < 1 else "OTM")
        moneyness_desc = f"{abs(moneyness):.1f}% {'below' if is_itm else 'above'} current price"

        total_premium = premium * shares

        recommendation = f"""**Recommendation: Sell {contracts} {ticker} ${strike:.2f} Calls expiring {expiration}**

- **Current Stock Price:** ${stock_price:.2f}
- **Strike Price:** ${strike:.2f} ({moneyness_label}, {moneyness_desc})
- **Premium:** ${premium:.2f} per share (${premium * 100:.2f} per contract)
- **Total Premium Income:** ${total_premium:,.2f}
- **Days to Expiration:** {days_to_expiry}
- **Annualized Return:** {annualized_return:.1f}%
- **Breakeven Price:** ${breakeven['breakeven_price']:.2f} ({breakeven['downside_protection_percent']:.1f}% downside protection)

**If Assigned (Max Profit Scenario):**
- Capital Gain: ${max_profit['total_capital_gain']:,.2f}
- Premium Income: ${max_profit['total_premium']:,.2f}
- Total Profit: ${max_profit['total_max_profit']:,.2f} ({max_profit['max_return_percent']:.1f}% return)

**Why This Option?**
This strike offers the highest annualized premium yield ({annualized_return:.1f}%) among all liquid options in the 7-45 day window. """

        if is_itm:
            recommendation += f"Note: This is an ITM option, which has a higher probability of assignment."
        else:
            recommendation += f"If {ticker} stays below ${strike:.2f} by {expiration}, you keep the full ${total_premium:,.2f} premium."

        return {
            "formatted_text": recommendation,
            "error": None,
        }

    except Exception as e:
        return {
            "formatted_text": None,
            "error": f"Error formatting recommendation: {str(e)}",
        }


def format_itm_warning(strike: float, stock_price: float) -> dict:
    """Generate a warning message for ITM options.

    Args:
        strike: Strike price of the option.
        stock_price: Current stock price.

    Returns:
        A dict with warning message.
    """
    try:
        if strike >= stock_price:
            return {
                "warning": None,
                "is_itm": False,
            }

        itm_amount = stock_price - strike
        itm_percent = (itm_amount / stock_price) * 100

        warning = f"""**ITM Warning:** This option is ${itm_amount:.2f} ({itm_percent:.1f}%) in-the-money.

- **Higher Assignment Risk:** ITM options are more likely to be exercised early, especially near ex-dividend dates.
- **Intrinsic Value:** ${itm_amount:.2f} of the premium is intrinsic value (not time value).
- **Early Assignment:** You may be assigned before expiration, resulting in selling your shares at ${strike:.2f}.

Consider this if you're willing to sell your shares at the strike price."""

        return {
            "warning": warning,
            "is_itm": True,
            "itm_amount": round(itm_amount, 2),
            "itm_percent": round(itm_percent, 2),
        }

    except Exception as e:
        return {
            "warning": None,
            "is_itm": False,
            "error": f"Error generating ITM warning: {str(e)}",
        }


def format_error_message(error_type: str, details: str) -> dict:
    """Format a user-friendly error message.

    Args:
        error_type: Type of error (e.g., "invalid_ticker", "no_options", "invalid_shares").
        details: Specific error details.

    Returns:
        A dict with formatted error message.
    """
    error_messages = {
        "invalid_ticker": f"I couldn't find the stock ticker you provided. {details} Please check the symbol and try again.",
        "no_options": f"No options are available for this stock. {details}",
        "no_liquid_options": f"No liquid options found in the 7-45 day window. {details} Try a more actively traded stock.",
        "invalid_shares": f"Invalid share count. {details} Shares must be a positive multiple of 100 for covered calls.",
        "api_error": f"There was an error fetching market data. {details} Please try again in a moment.",
        "calculation_error": f"There was an error calculating the recommendation. {details}",
    }

    message = error_messages.get(
        error_type,
        f"An unexpected error occurred. {details}",
    )

    return {
        "error_type": error_type,
        "message": message,
    }
