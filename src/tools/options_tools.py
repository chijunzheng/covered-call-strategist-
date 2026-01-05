"""Tools for fetching and filtering options chain data."""

from datetime import datetime, timedelta
import yfinance as yf


def get_options_chain(ticker: str, min_days: int = 7, max_days: int = 45) -> dict:
    """Fetch the call options chain for a ticker within a date window.

    Args:
        ticker: The stock ticker symbol (e.g., "AAPL", "MSFT").

    Returns:
        A dict with options data including:
        - ticker: The ticker symbol
        - options: List of call options with strike, expiration, bid, ask, open_interest
        - expirations: Available expiration dates in the window
        - error: Error message if failed
    """
    try:
        stock = yf.Ticker(ticker.upper())
        expirations = stock.options

        if not expirations:
            return {
                "ticker": ticker.upper(),
                "options": [],
                "expirations": [],
                "error": f"No options available for '{ticker}'.",
            }

        all_options = []
        today = datetime.now().date()

        filtered_expirations = []
        for exp_date in expirations:
            try:
                exp_datetime = datetime.strptime(exp_date, "%Y-%m-%d").date()
                days_to_expiry = (exp_datetime - today).days

                if days_to_expiry < min_days or days_to_expiry > max_days:
                    continue

                opt_chain = stock.option_chain(exp_date)
                calls = opt_chain.calls
                filtered_expirations.append(exp_date)

                for _, row in calls.iterrows():
                    all_options.append({
                        "strike": float(row["strike"]),
                        "expiration": exp_date,
                        "days_to_expiry": days_to_expiry,
                        "bid": float(row["bid"]) if row["bid"] else 0.0,
                        "ask": float(row["ask"]) if row["ask"] else 0.0,
                        "last_price": float(row["lastPrice"]) if row["lastPrice"] else 0.0,
                        "open_interest": int(row["openInterest"]) if row["openInterest"] else 0,
                        "volume": int(row["volume"]) if row["volume"] and row["volume"] > 0 else 0,
                        "implied_volatility": float(row["impliedVolatility"]) if row["impliedVolatility"] else 0.0,
                    })
            except Exception:
                continue

        return {
            "ticker": ticker.upper(),
            "options": all_options,
            "expirations": filtered_expirations,
            "error": None,
        }

    except Exception as e:
        return {
            "ticker": ticker.upper(),
            "options": [],
            "expirations": [],
            "error": f"Error fetching options for '{ticker}': {str(e)}",
        }


def filter_options(
    options_data: dict,
    min_days: int = 7,
    max_days: int = 45,
    min_open_interest: int = 10,
) -> dict:
    """Filter options by expiration window and liquidity requirements.

    Args:
        options_data: The options data dict from get_options_chain.
        min_days: Minimum days to expiration (default: 7).
        max_days: Maximum days to expiration (default: 45).
        min_open_interest: Minimum open interest required (default: 10).

    Returns:
        A dict with filtered options including:
        - ticker: The ticker symbol
        - filtered_options: List of options meeting criteria
        - total_before_filter: Count before filtering
        - total_after_filter: Count after filtering
        - error: Error message if failed
    """
    try:
        if options_data.get("error"):
            return {
                "ticker": options_data.get("ticker", "UNKNOWN"),
                "filtered_options": [],
                "total_before_filter": 0,
                "total_after_filter": 0,
                "error": options_data["error"],
            }

        options = options_data.get("options", [])
        total_before = len(options)

        filtered = [
            opt for opt in options
            if (
                min_days <= opt["days_to_expiry"] <= max_days
                and opt["open_interest"] >= min_open_interest
                and opt["bid"] > 0
            )
        ]

        return {
            "ticker": options_data.get("ticker", "UNKNOWN"),
            "filtered_options": filtered,
            "total_before_filter": total_before,
            "total_after_filter": len(filtered),
            "error": None,
        }

    except Exception as e:
        return {
            "ticker": options_data.get("ticker", "UNKNOWN"),
            "filtered_options": [],
            "total_before_filter": 0,
            "total_after_filter": 0,
            "error": f"Error filtering options: {str(e)}",
        }
