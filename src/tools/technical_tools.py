"""Tools for technical analysis of stock price movements."""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    """Calculate the Relative Strength Index (RSI).

    Args:
        prices: Series of closing prices.
        period: RSI period (default 14).

    Returns:
        RSI value between 0 and 100.
    """
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0


def calculate_macd(prices: pd.Series) -> dict:
    """Calculate MACD (Moving Average Convergence Divergence).

    Args:
        prices: Series of closing prices.

    Returns:
        Dict with macd, signal, histogram, and trend direction.
    """
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal

    current_macd = float(macd.iloc[-1])
    current_signal = float(signal.iloc[-1])
    current_hist = float(histogram.iloc[-1])
    prev_hist = float(histogram.iloc[-2]) if len(histogram) > 1 else 0

    # Determine trend
    if current_macd > current_signal and current_hist > prev_hist:
        trend = "bullish"
    elif current_macd < current_signal and current_hist < prev_hist:
        trend = "bearish"
    else:
        trend = "neutral"

    return {
        "macd": round(current_macd, 4),
        "signal": round(current_signal, 4),
        "histogram": round(current_hist, 4),
        "trend": trend,
    }


def calculate_moving_averages(prices: pd.Series) -> dict:
    """Calculate simple moving averages and trend.

    Args:
        prices: Series of closing prices.

    Returns:
        Dict with SMA values and trend analysis.
    """
    current_price = float(prices.iloc[-1])
    sma20 = float(prices.rolling(window=20).mean().iloc[-1])
    sma50 = float(prices.rolling(window=50).mean().iloc[-1])

    # Price position relative to MAs
    above_sma20 = current_price > sma20
    above_sma50 = current_price > sma50
    sma20_above_sma50 = sma20 > sma50

    if above_sma20 and above_sma50 and sma20_above_sma50:
        trend = "strong_bullish"
    elif above_sma20 and above_sma50:
        trend = "bullish"
    elif not above_sma20 and not above_sma50 and not sma20_above_sma50:
        trend = "strong_bearish"
    elif not above_sma20 and not above_sma50:
        trend = "bearish"
    else:
        trend = "neutral"

    return {
        "current_price": round(current_price, 2),
        "sma20": round(sma20, 2),
        "sma50": round(sma50, 2),
        "above_sma20": above_sma20,
        "above_sma50": above_sma50,
        "trend": trend,
    }


def analyze_volume(ticker_data: pd.DataFrame) -> dict:
    """Analyze volume patterns.

    Args:
        ticker_data: DataFrame with OHLCV data.

    Returns:
        Dict with volume analysis.
    """
    volume = ticker_data["Volume"]
    current_volume = float(volume.iloc[-1])
    avg_volume_20 = float(volume.rolling(window=20).mean().iloc[-1])

    volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1.0

    # Check if recent price move is supported by volume
    price_change = float(ticker_data["Close"].iloc[-1] - ticker_data["Close"].iloc[-5])

    if volume_ratio > 1.5 and price_change > 0:
        signal = "bullish_volume"
    elif volume_ratio > 1.5 and price_change < 0:
        signal = "bearish_volume"
    elif volume_ratio < 0.5:
        signal = "low_volume"
    else:
        signal = "normal"

    return {
        "current_volume": int(current_volume),
        "avg_volume_20": int(avg_volume_20),
        "volume_ratio": round(volume_ratio, 2),
        "signal": signal,
    }


def get_technical_analysis(ticker: str) -> dict:
    """Get comprehensive technical analysis for a stock.

    Args:
        ticker: Stock ticker symbol.

    Returns:
        Dict with all technical indicators and overall assessment.
    """
    try:
        stock = yf.Ticker(ticker.upper())

        # Get 3 months of daily data for indicator calculations
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        hist = stock.history(start=start_date, end=end_date)

        if hist.empty or len(hist) < 50:
            return {
                "ticker": ticker.upper(),
                "error": f"Insufficient price history for {ticker}",
                "assignment_risk": "unknown",
            }

        prices = hist["Close"]

        # Calculate all indicators
        rsi = calculate_rsi(prices)
        macd = calculate_macd(prices)
        mas = calculate_moving_averages(prices)
        volume = analyze_volume(hist)

        # Determine overall sentiment and assignment risk
        bullish_signals = 0
        bearish_signals = 0
        bounce_potential = None  # Track oversold/overbought bounce potential

        # RSI analysis - with bounce potential detection
        # Use 35/65 thresholds for near-oversold/overbought to catch early warnings
        if rsi > 70:
            rsi_signal = "overbought"
            bearish_signals += 0.5  # Overbought = potential pullback
            bounce_potential = "overbought_pullback"  # May pull back
        elif rsi < 35:
            rsi_signal = "oversold"
            bullish_signals += 0.5  # Oversold = potential bounce
            bounce_potential = "oversold_bounce"  # May bounce up
        elif rsi > 65:
            rsi_signal = "near_overbought"
            # Not quite overbought, but elevated
            bearish_signals += 0.3
        elif rsi > 55:
            rsi_signal = "bullish"
            bullish_signals += 1
        elif rsi < 45:
            rsi_signal = "bearish"
            bearish_signals += 1
        else:
            rsi_signal = "neutral"

        # MACD analysis
        if macd["trend"] == "bullish":
            bullish_signals += 1
        elif macd["trend"] == "bearish":
            bearish_signals += 1

        # Moving average analysis
        if mas["trend"] in ["strong_bullish", "bullish"]:
            bullish_signals += 1
        elif mas["trend"] in ["strong_bearish", "bearish"]:
            bearish_signals += 1

        # Volume analysis
        if volume["signal"] == "bullish_volume":
            bullish_signals += 1
        elif volume["signal"] == "bearish_volume":
            bearish_signals += 1

        # Calculate assignment risk for covered calls
        # Higher bullish signals = higher risk of stock rising above strike
        total_signals = bullish_signals + bearish_signals
        if total_signals > 0:
            bullish_ratio = bullish_signals / total_signals
        else:
            bullish_ratio = 0.5

        # Adjust for bounce potential - oversold stocks may bounce!
        if bounce_potential == "oversold_bounce":
            # Even if bearish, oversold means bounce risk
            if bullish_ratio < 0.4:
                assignment_risk = "moderate"  # Upgrade from low/very_low
                sentiment = "oversold_bounce_risk"
                recommendation = "Stock is oversold - potential bounce. Consider layered strikes or wait for confirmation."
            else:
                assignment_risk = "moderate"
                sentiment = "oversold_with_bullish"
                recommendation = "Oversold with bullish signals - high bounce probability. Use defensive strikes."
        elif bounce_potential == "overbought_pullback":
            # Even if bullish, overbought means pullback risk
            if bullish_ratio > 0.6:
                assignment_risk = "moderate"  # Downgrade from high
                sentiment = "overbought_pullback_risk"
                recommendation = "Stock is overbought - potential pullback. ATM strikes may be safe."
            else:
                assignment_risk = "low"
                sentiment = "overbought_with_bearish"
                recommendation = "Overbought with bearish signals - pullback likely. Good for covered calls."
        elif bullish_ratio >= 0.7:
            assignment_risk = "high"
            sentiment = "bullish"
            recommendation = "Consider higher strike or wait for pullback"
        elif bullish_ratio >= 0.5:
            assignment_risk = "moderate"
            sentiment = "slightly_bullish"
            recommendation = "ATM or slightly OTM strike appropriate"
        elif bullish_ratio >= 0.3:
            assignment_risk = "low"
            sentiment = "neutral"
            recommendation = "Good environment for covered calls"
        else:
            assignment_risk = "very_low"
            sentiment = "bearish"
            recommendation = "Caution: stock may decline, reducing call premium value"

        return {
            "ticker": ticker.upper(),
            "current_price": mas["current_price"],
            "rsi": {
                "value": round(rsi, 1),
                "signal": rsi_signal,
            },
            "macd": macd,
            "moving_averages": mas,
            "volume": volume,
            "sentiment": sentiment,
            "assignment_risk": assignment_risk,
            "recommendation": recommendation,
            "bullish_signals": bullish_signals,
            "bearish_signals": bearish_signals,
            "bounce_potential": bounce_potential,
            "error": None,
        }

    except Exception as e:
        return {
            "ticker": ticker.upper(),
            "error": f"Error analyzing {ticker}: {str(e)}",
            "assignment_risk": "unknown",
        }


def format_technical_summary(analysis: dict) -> str:
    """Format technical analysis into a readable summary.

    Args:
        analysis: Dict from get_technical_analysis.

    Returns:
        Formatted string summary.
    """
    if analysis.get("error"):
        return f"Technical analysis unavailable: {analysis['error']}"

    rsi = analysis["rsi"]
    macd = analysis["macd"]
    mas = analysis["moving_averages"]
    volume = analysis["volume"]

    lines = [
        f"**Technical Analysis for {analysis['ticker']}**",
        "",
        f"**Overall Sentiment:** {analysis['sentiment'].replace('_', ' ').title()}",
        f"**Assignment Risk:** {analysis['assignment_risk'].replace('_', ' ').title()}",
        "",
        "**Indicators:**",
        f"- RSI(14): {rsi['value']} ({rsi['signal']})",
        f"- MACD: {macd['trend'].title()} (histogram: {macd['histogram']:+.4f})",
        f"- Price vs SMA20: {'Above' if mas['above_sma20'] else 'Below'} (${mas['sma20']})",
        f"- Price vs SMA50: {'Above' if mas['above_sma50'] else 'Below'} (${mas['sma50']})",
        f"- Volume: {volume['volume_ratio']}x average ({volume['signal'].replace('_', ' ')})",
        "",
        f"**Recommendation:** {analysis['recommendation']}",
    ]

    return "\n".join(lines)
