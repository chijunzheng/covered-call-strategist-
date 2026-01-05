"""Tools for analyzing covered call options and calculating returns."""


def calculate_option_metrics(option: dict, stock_price: float) -> dict:
    """Calculate premium yield and annualized return for an option.

    Args:
        option: Option data dict with strike, bid, days_to_expiry.
        stock_price: Current stock price.

    Returns:
        A dict with calculated metrics including:
        - strike: Strike price
        - expiration: Expiration date
        - premium: Option premium (bid price)
        - premium_yield: Premium as percentage of strike
        - annualized_return: Annualized premium yield
        - is_itm: Whether option is in-the-money
        - moneyness: Percentage difference from stock price
        - days_to_expiry: Days until expiration
    """
    try:
        strike = option["strike"]
        premium = option["bid"]
        days_to_expiry = option["days_to_expiry"]

        premium_yield = (premium / strike) * 100 if strike > 0 else 0
        annualized_return = (premium_yield / days_to_expiry) * 365 if days_to_expiry > 0 else 0

        is_itm = strike < stock_price
        moneyness = ((strike - stock_price) / stock_price) * 100

        return {
            "strike": strike,
            "expiration": option["expiration"],
            "premium": premium,
            "premium_yield": round(premium_yield, 4),
            "annualized_return": round(annualized_return, 2),
            "is_itm": is_itm,
            "moneyness": round(moneyness, 2),
            "days_to_expiry": days_to_expiry,
            "open_interest": option.get("open_interest", 0),
            "implied_volatility": option.get("implied_volatility", 0),
        }

    except Exception as e:
        return {
            "error": f"Error calculating metrics: {str(e)}",
        }


def find_best_option(filtered_options: list[dict], stock_price: float) -> dict:
    """Find the option with the highest annualized return.

    Args:
        filtered_options: List of filtered option dicts.
        stock_price: Current stock price.

    Returns:
        A dict with the best option including all metrics, or error if none found.
    """
    try:
        if not filtered_options:
            return {
                "found": False,
                "best_option": None,
                "error": "No options available after filtering.",
            }

        best_option = None
        best_annualized = -1

        for option in filtered_options:
            metrics = calculate_option_metrics(option, stock_price)
            if "error" in metrics:
                continue

            if metrics["annualized_return"] > best_annualized:
                best_annualized = metrics["annualized_return"]
                best_option = metrics

        if best_option is None:
            return {
                "found": False,
                "best_option": None,
                "error": "Could not calculate metrics for any options.",
            }

        return {
            "found": True,
            "best_option": best_option,
            "error": None,
        }

    except Exception as e:
        return {
            "found": False,
            "best_option": None,
            "error": f"Error finding best option: {str(e)}",
        }


def calculate_breakeven(stock_price: float, premium: float) -> dict:
    """Calculate the breakeven price for a covered call position.

    Args:
        stock_price: Current stock price (cost basis).
        premium: Premium received from selling the call.

    Returns:
        A dict with breakeven calculation.
    """
    try:
        breakeven = stock_price - premium
        downside_protection = (premium / stock_price) * 100

        return {
            "breakeven_price": round(breakeven, 2),
            "downside_protection_percent": round(downside_protection, 2),
            "error": None,
        }

    except Exception as e:
        return {
            "breakeven_price": None,
            "downside_protection_percent": None,
            "error": f"Error calculating breakeven: {str(e)}",
        }


def calculate_max_profit(
    stock_price: float,
    strike: float,
    premium: float,
    shares: int,
) -> dict:
    """Calculate maximum profit if shares are called away.

    Args:
        stock_price: Current stock price (cost basis).
        strike: Strike price of the call option.
        premium: Premium received per share.
        shares: Number of shares owned.

    Returns:
        A dict with max profit calculations.
    """
    try:
        contracts = shares // 100

        capital_gain_per_share = strike - stock_price
        total_capital_gain = capital_gain_per_share * shares

        total_premium = premium * shares

        total_max_profit = total_capital_gain + total_premium

        max_return_percent = (total_max_profit / (stock_price * shares)) * 100

        return {
            "contracts": contracts,
            "shares": shares,
            "capital_gain_per_share": round(capital_gain_per_share, 2),
            "total_capital_gain": round(total_capital_gain, 2),
            "premium_per_share": round(premium, 2),
            "total_premium": round(total_premium, 2),
            "total_max_profit": round(total_max_profit, 2),
            "max_return_percent": round(max_return_percent, 2),
            "error": None,
        }

    except Exception as e:
        return {
            "error": f"Error calculating max profit: {str(e)}",
        }
