"""Tools for fetching stock data from Yahoo Finance."""

import yfinance as yf


def validate_ticker(ticker: str) -> dict:
    """Validate that a stock ticker exists and has options available.

    Args:
        ticker: The stock ticker symbol (e.g., "AAPL", "MSFT").

    Returns:
        A dict with validation results including:
        - valid: Whether the ticker is valid
        - has_options: Whether options are available
        - name: Company name if valid
        - error: Error message if invalid
    """
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        if not info or info.get("regularMarketPrice") is None:
            return {
                "valid": False,
                "has_options": False,
                "name": None,
                "error": f"Ticker '{ticker}' not found or has no market data.",
            }

        options_dates = stock.options
        has_options = len(options_dates) > 0 if options_dates else False

        if not has_options:
            return {
                "valid": True,
                "has_options": False,
                "name": info.get("shortName", ticker),
                "error": f"Ticker '{ticker}' exists but has no options available.",
            }

        return {
            "valid": True,
            "has_options": True,
            "name": info.get("shortName", ticker),
            "error": None,
        }

    except Exception as e:
        return {
            "valid": False,
            "has_options": False,
            "name": None,
            "error": f"Error validating ticker '{ticker}': {str(e)}",
        }


def get_stock_price(ticker: str) -> dict:
    """Fetch the current stock price for a ticker.

    Args:
        ticker: The stock ticker symbol (e.g., "AAPL", "MSFT").

    Returns:
        A dict with price data including:
        - ticker: The ticker symbol
        - price: Current stock price
        - currency: Currency of the price
        - error: Error message if failed
    """
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        price = info.get("regularMarketPrice") or info.get("currentPrice")

        if price is None:
            return {
                "ticker": ticker.upper(),
                "price": None,
                "currency": None,
                "error": f"Could not fetch price for '{ticker}'.",
            }

        return {
            "ticker": ticker.upper(),
            "price": float(price),
            "currency": info.get("currency", "USD"),
            "error": None,
        }

    except Exception as e:
        return {
            "ticker": ticker.upper(),
            "price": None,
            "currency": None,
            "error": f"Error fetching price for '{ticker}': {str(e)}",
        }
