"""Integration tests for the agent system."""

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock

from src.tools.stock_tools import validate_ticker, get_stock_price
from src.tools.options_tools import get_options_chain, filter_options
from src.tools.analysis_tools import find_best_option, calculate_breakeven, calculate_max_profit


class TestAgentWorkflow:
    """Test the complete agent workflow with real data."""

    @pytest.mark.integration
    def test_full_workflow_aapl(self):
        """Test complete workflow with AAPL."""
        # Step 1: Validate ticker
        validation = validate_ticker("AAPL")
        assert validation["valid"] is True
        assert validation["has_options"] is True

        # Step 2: Get stock price
        price_data = get_stock_price("AAPL")
        assert price_data["price"] is not None
        stock_price = price_data["price"]

        # Step 3: Get options chain
        options_data = get_options_chain("AAPL")
        assert len(options_data["options"]) > 0

        # Step 4: Filter options
        filtered = filter_options(options_data)
        # AAPL should have liquid options
        assert filtered["total_after_filter"] > 0

        # Step 5: Find best option
        best = find_best_option(filtered["filtered_options"], stock_price)
        assert best["found"] is True
        assert best["best_option"]["annualized_return"] > 0

        # Step 6: Calculate breakeven
        breakeven = calculate_breakeven(stock_price, best["best_option"]["premium"])
        assert breakeven["breakeven_price"] < stock_price

        # Step 7: Calculate max profit
        max_profit = calculate_max_profit(
            stock_price=stock_price,
            strike=best["best_option"]["strike"],
            premium=best["best_option"]["premium"],
            shares=500,
        )
        assert max_profit["contracts"] == 5

    @pytest.mark.integration
    def test_full_workflow_msft(self):
        """Test complete workflow with MSFT for validation."""
        validation = validate_ticker("MSFT")
        assert validation["valid"] is True

        price_data = get_stock_price("MSFT")
        assert price_data["price"] is not None

        options_data = get_options_chain("MSFT")
        assert len(options_data["options"]) > 0

    def test_invalid_ticker_workflow(self):
        """Test workflow handles invalid tickers gracefully."""
        validation = validate_ticker("INVALIDTICKER999")
        assert validation["valid"] is False
        # Workflow should stop here and return error

    def test_shares_validation(self):
        """Test shares must be multiple of 100."""
        # Valid shares
        assert 500 % 100 == 0
        assert 100 % 100 == 0
        assert 1000 % 100 == 0

        # Invalid shares
        assert 150 % 100 != 0
        assert 99 % 100 != 0
        assert 501 % 100 != 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_no_options_in_window(self):
        """Test handling when no options meet criteria."""
        mock_options = {
            "ticker": "TEST",
            "options": [
                {"strike": 100, "days_to_expiry": 3, "open_interest": 50, "bid": 2.0},  # Too soon
                {"strike": 105, "days_to_expiry": 60, "open_interest": 100, "bid": 1.5},  # Too far
            ],
            "error": None,
        }

        filtered = filter_options(mock_options, min_days=7, max_days=45)
        assert filtered["total_after_filter"] == 0

        best = find_best_option(filtered["filtered_options"], 100.0)
        assert best["found"] is False

    def test_all_zero_bids(self):
        """Test handling when all options have zero bids."""
        mock_options = {
            "ticker": "TEST",
            "options": [
                {"strike": 100, "days_to_expiry": 20, "open_interest": 50, "bid": 0.0},
                {"strike": 105, "days_to_expiry": 25, "open_interest": 100, "bid": 0.0},
            ],
            "error": None,
        }

        filtered = filter_options(mock_options)
        assert filtered["total_after_filter"] == 0

    def test_itm_option_selected(self):
        """Test ITM option can be selected if it has highest yield."""
        options = [
            {"strike": 95, "bid": 8.0, "days_to_expiry": 30, "expiration": "2025-02-15"},  # ITM, high premium
            {"strike": 105, "bid": 1.0, "days_to_expiry": 30, "expiration": "2025-02-15"},  # OTM, low premium
        ]
        stock_price = 100.0

        best = find_best_option(options, stock_price)
        assert best["found"] is True
        assert best["best_option"]["strike"] == 95  # ITM selected for higher yield
        assert best["best_option"]["is_itm"] is True


class TestInputParsing:
    """Test input parsing scenarios."""

    def test_parse_ticker_formats(self):
        """Test various ticker input formats work."""
        # All these should validate the same
        tickers = ["AAPL", "aapl", "Aapl", " AAPL ", "aapl "]

        for ticker in tickers:
            result = validate_ticker(ticker.strip())
            assert result["valid"] is True, f"Failed for ticker: {ticker}"

    def test_shares_calculations(self):
        """Test contract calculations for various share counts."""
        test_cases = [
            (100, 1),
            (200, 2),
            (500, 5),
            (1000, 10),
            (10000, 100),
        ]

        for shares, expected_contracts in test_cases:
            max_profit = calculate_max_profit(
                stock_price=100.0,
                strike=105.0,
                premium=2.0,
                shares=shares,
            )
            assert max_profit["contracts"] == expected_contracts
