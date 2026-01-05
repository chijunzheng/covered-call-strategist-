"""Unit tests for the tools modules."""

import pytest
from src.tools.stock_tools import validate_ticker, get_stock_price
from src.tools.options_tools import get_options_chain, filter_options
from src.tools.analysis_tools import (
    calculate_option_metrics,
    find_best_option,
    calculate_breakeven,
    calculate_max_profit,
)
from src.tools.formatting_tools import (
    format_recommendation,
    format_itm_warning,
    format_error_message,
)


class TestStockTools:
    """Tests for stock_tools module."""

    def test_validate_ticker_valid(self):
        """Test validation of a known valid ticker."""
        result = validate_ticker("AAPL")
        assert result["valid"] is True
        assert result["has_options"] is True
        assert result["error"] is None

    def test_validate_ticker_invalid(self):
        """Test validation of an invalid ticker."""
        result = validate_ticker("INVALIDTICKER123")
        assert result["valid"] is False

    def test_get_stock_price_valid(self):
        """Test fetching price for a valid ticker."""
        result = get_stock_price("AAPL")
        assert result["ticker"] == "AAPL"
        assert result["price"] is not None
        assert result["price"] > 0
        assert result["error"] is None

    def test_get_stock_price_invalid(self):
        """Test fetching price for an invalid ticker."""
        result = get_stock_price("INVALIDTICKER123")
        assert result["price"] is None


class TestOptionsTools:
    """Tests for options_tools module."""

    def test_get_options_chain_valid(self):
        """Test fetching options chain for a valid ticker."""
        result = get_options_chain("AAPL")
        assert result["ticker"] == "AAPL"
        assert len(result["options"]) > 0
        assert len(result["expirations"]) > 0
        assert result["error"] is None

    def test_get_options_chain_invalid(self):
        """Test fetching options for an invalid ticker."""
        result = get_options_chain("INVALIDTICKER123")
        assert result["error"] is not None

    def test_filter_options(self):
        """Test filtering options by criteria."""
        mock_options_data = {
            "ticker": "TEST",
            "options": [
                {"strike": 100, "days_to_expiry": 10, "open_interest": 50, "bid": 2.0},
                {"strike": 105, "days_to_expiry": 5, "open_interest": 100, "bid": 1.5},  # Too soon
                {"strike": 110, "days_to_expiry": 20, "open_interest": 5, "bid": 1.0},  # Low OI
                {"strike": 115, "days_to_expiry": 30, "open_interest": 75, "bid": 0.0},  # No bid
                {"strike": 120, "days_to_expiry": 50, "open_interest": 200, "bid": 3.0},  # Too far
            ],
            "error": None,
        }

        result = filter_options(mock_options_data, min_days=7, max_days=45, min_open_interest=10)
        assert result["total_before_filter"] == 5
        assert result["total_after_filter"] == 1
        assert result["filtered_options"][0]["strike"] == 100


class TestAnalysisTools:
    """Tests for analysis_tools module."""

    def test_calculate_option_metrics(self):
        """Test calculation of option metrics."""
        option = {
            "strike": 150.0,
            "expiration": "2025-02-15",
            "bid": 3.0,
            "days_to_expiry": 30,
            "open_interest": 100,
            "implied_volatility": 0.25,
        }
        stock_price = 145.0

        result = calculate_option_metrics(option, stock_price)

        assert result["strike"] == 150.0
        assert result["premium"] == 3.0
        assert result["is_itm"] is False  # 150 > 145
        assert result["annualized_return"] > 0
        assert "premium_yield" in result

    def test_calculate_option_metrics_itm(self):
        """Test metrics for ITM option."""
        option = {
            "strike": 140.0,
            "expiration": "2025-02-15",
            "bid": 8.0,
            "days_to_expiry": 30,
        }
        stock_price = 145.0

        result = calculate_option_metrics(option, stock_price)
        assert result["is_itm"] is True

    def test_find_best_option(self):
        """Test finding the best option by annualized return."""
        options = [
            {"strike": 150, "bid": 2.0, "days_to_expiry": 30, "expiration": "2025-02-15"},
            {"strike": 155, "bid": 3.5, "days_to_expiry": 30, "expiration": "2025-02-15"},
            {"strike": 160, "bid": 1.0, "days_to_expiry": 30, "expiration": "2025-02-15"},
        ]
        stock_price = 148.0

        result = find_best_option(options, stock_price)

        assert result["found"] is True
        assert result["best_option"]["strike"] == 155  # Highest yield

    def test_find_best_option_empty(self):
        """Test with no options."""
        result = find_best_option([], 100.0)
        assert result["found"] is False

    def test_calculate_breakeven(self):
        """Test breakeven calculation."""
        result = calculate_breakeven(stock_price=150.0, premium=3.0)

        assert result["breakeven_price"] == 147.0
        assert result["downside_protection_percent"] == 2.0

    def test_calculate_max_profit(self):
        """Test max profit calculation."""
        result = calculate_max_profit(
            stock_price=145.0,
            strike=150.0,
            premium=3.0,
            shares=500,
        )

        assert result["contracts"] == 5
        assert result["shares"] == 500
        assert result["capital_gain_per_share"] == 5.0
        assert result["total_capital_gain"] == 2500.0
        assert result["total_premium"] == 1500.0
        assert result["total_max_profit"] == 4000.0


class TestFormattingTools:
    """Tests for formatting_tools module."""

    def test_format_recommendation(self):
        """Test formatting a complete recommendation."""
        result = format_recommendation(
            ticker="AAPL",
            stock_price=150.0,
            best_option={
                "strike": 155.0,
                "expiration": "2025-02-15",
                "premium": 3.0,
                "annualized_return": 24.3,
                "days_to_expiry": 30,
                "moneyness": 3.33,
                "is_itm": False,
            },
            shares=500,
            breakeven={"breakeven_price": 147.0, "downside_protection_percent": 2.0},
            max_profit={
                "total_capital_gain": 2500.0,
                "total_premium": 1500.0,
                "total_max_profit": 4000.0,
                "max_return_percent": 5.33,
            },
        )

        assert result["error"] is None
        assert "AAPL" in result["formatted_text"]
        assert "$155.00" in result["formatted_text"]
        assert "24.3%" in result["formatted_text"]

    def test_format_itm_warning(self):
        """Test ITM warning generation."""
        result = format_itm_warning(strike=145.0, stock_price=150.0)

        assert result["is_itm"] is True
        assert result["warning"] is not None
        assert "ITM Warning" in result["warning"]

    def test_format_itm_warning_otm(self):
        """Test no warning for OTM option."""
        result = format_itm_warning(strike=155.0, stock_price=150.0)

        assert result["is_itm"] is False
        assert result["warning"] is None

    def test_format_error_message(self):
        """Test error message formatting."""
        result = format_error_message("invalid_ticker", "Symbol 'XYZ' not found.")

        assert result["error_type"] == "invalid_ticker"
        assert "XYZ" in result["message"]
        assert "check the symbol" in result["message"].lower()
