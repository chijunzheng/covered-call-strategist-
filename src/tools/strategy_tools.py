"""High-level tools for running covered call analysis end-to-end."""

from src.tools.stock_tools import validate_ticker, get_stock_price
from src.tools.options_tools import get_options_chain, filter_options
from src.tools.analysis_tools import (
    find_best_option,
    calculate_breakeven,
    calculate_max_profit,
)
from src.tools.formatting_tools import (
    format_recommendation,
    format_itm_warning,
    format_error_message,
)
from src.tools.technical_tools import get_technical_analysis


def _select_strike_based_on_technicals(
    filtered_options: list,
    stock_price: float,
    technical_analysis: dict,
) -> dict:
    """Select the best strike based on technical analysis.

    Args:
        filtered_options: List of filtered OTM options.
        stock_price: Current stock price.
        technical_analysis: Dict from get_technical_analysis.

    Returns:
        Dict with selected option and reasoning.
    """
    from src.tools.analysis_tools import calculate_option_metrics

    assignment_risk = technical_analysis.get("assignment_risk", "moderate")
    sentiment = technical_analysis.get("sentiment", "neutral")
    bounce_potential = technical_analysis.get("bounce_potential")

    # Define strike preference based on assignment risk and bounce potential
    if sentiment in ["oversold_bounce_risk", "oversold_with_bullish"]:
        # Oversold = potential bounce, be more conservative
        min_otm_pct = 0.02
        max_otm_pct = 0.06
        strategy = "balanced"
        reason = "Stock is oversold (RSI < 30) with potential bounce. Using balanced strike to hedge bounce risk."
        use_layered = True
    elif sentiment in ["overbought_pullback_risk", "overbought_with_bearish"]:
        # Overbought = potential pullback, can be more aggressive
        min_otm_pct = 0.0
        max_otm_pct = 0.03
        strategy = "aggressive"
        reason = "Stock is overbought with pullback potential. ATM strike is appropriate."
        use_layered = False
    elif assignment_risk == "high":
        # Bullish: prefer higher strikes (3-10% OTM) to reduce assignment risk
        min_otm_pct = 0.03
        max_otm_pct = 0.10
        strategy = "defensive"
        reason = "Due to bullish momentum, recommending a higher strike to reduce assignment risk while still collecting premium."
        use_layered = False
    elif assignment_risk == "moderate":
        # Mixed: prefer slightly OTM (1-5%)
        min_otm_pct = 0.01
        max_otm_pct = 0.05
        strategy = "balanced"
        reason = "With mixed technical signals, recommending a slightly OTM strike for balanced risk/reward."
        use_layered = True  # Moderate uncertainty = layered approach
    else:
        # Bearish/neutral: ATM is fine (0-3% OTM), maximize premium
        min_otm_pct = 0.0
        max_otm_pct = 0.03
        strategy = "aggressive"
        reason = "With low assignment risk, recommending an ATM strike to maximize premium income."
        use_layered = False

    # Filter options by preferred OTM range
    min_strike = stock_price * (1 + min_otm_pct)
    max_strike = stock_price * (1 + max_otm_pct)

    preferred_options = [
        opt for opt in filtered_options
        if min_strike <= opt.get("strike", 0) <= max_strike
    ]

    # If no options in preferred range, expand to all OTM options
    if not preferred_options:
        preferred_options = filtered_options
        reason = f"No options in preferred range ({min_otm_pct*100:.0f}-{max_otm_pct*100:.0f}% OTM). Selecting best available option."

    # Find highest yield within preferred range, with full metrics
    best_option = None
    best_yield = -1

    for opt in preferred_options:
        metrics = calculate_option_metrics(opt, stock_price)
        if "error" in metrics:
            continue
        if metrics.get("annualized_return", 0) > best_yield:
            best_yield = metrics["annualized_return"]
            best_option = metrics  # Use metrics dict which has premium, etc.

    return {
        "option": best_option,
        "strategy": strategy,
        "reason": reason,
        "assignment_risk": assignment_risk,
        "sentiment": sentiment,
        "bounce_potential": bounce_potential,
        "use_layered": use_layered,
    }


def _create_layered_strategy(
    filtered_options: list,
    stock_price: float,
    shares: int,
    technical_analysis: dict,
) -> dict:
    """Create a layered covered call strategy with multiple strikes.

    Args:
        filtered_options: List of filtered OTM options.
        stock_price: Current stock price.
        shares: Total number of shares.
        technical_analysis: Dict from get_technical_analysis.

    Returns:
        Dict with layered strategy details.
    """
    from src.tools.analysis_tools import calculate_option_metrics

    contracts = shares // 100
    if contracts < 3:
        return None  # Not enough contracts for layered strategy

    sentiment = technical_analysis.get("sentiment", "neutral")
    bounce_potential = technical_analysis.get("bounce_potential")

    # Define allocation based on sentiment
    if sentiment in ["oversold_bounce_risk", "oversold_with_bullish"]:
        # Oversold: hedge heavily for bounce
        # 40% conservative (higher OTM), 40% balanced, 20% aggressive (ATM)
        allocations = [
            {"name": "Conservative", "pct": 0.40, "otm_range": (0.04, 0.08)},
            {"name": "Balanced", "pct": 0.40, "otm_range": (0.02, 0.04)},
            {"name": "Aggressive", "pct": 0.20, "otm_range": (0.00, 0.02)},
        ]
    elif sentiment == "moderate" or bounce_potential:
        # Moderate uncertainty: balanced distribution
        allocations = [
            {"name": "Conservative", "pct": 0.33, "otm_range": (0.03, 0.06)},
            {"name": "Balanced", "pct": 0.34, "otm_range": (0.01, 0.03)},
            {"name": "Aggressive", "pct": 0.33, "otm_range": (0.00, 0.01)},
        ]
    else:
        # Default layered
        allocations = [
            {"name": "Conservative", "pct": 0.30, "otm_range": (0.03, 0.06)},
            {"name": "Balanced", "pct": 0.40, "otm_range": (0.01, 0.03)},
            {"name": "Aggressive", "pct": 0.30, "otm_range": (0.00, 0.01)},
        ]

    layers = []
    total_premium = 0

    for alloc in allocations:
        layer_contracts = max(1, int(contracts * alloc["pct"]))
        min_strike = stock_price * (1 + alloc["otm_range"][0])
        max_strike = stock_price * (1 + alloc["otm_range"][1])

        # Find best option in this range
        range_options = [
            opt for opt in filtered_options
            if min_strike <= opt.get("strike", 0) <= max_strike
        ]

        if not range_options:
            # Expand range if no options found
            range_options = filtered_options

        best_in_range = None
        best_yield = -1

        for opt in range_options:
            metrics = calculate_option_metrics(opt, stock_price)
            if "error" in metrics:
                continue
            if metrics.get("annualized_return", 0) > best_yield:
                best_yield = metrics["annualized_return"]
                best_in_range = metrics

        if best_in_range:
            layer_premium = best_in_range["premium"] * layer_contracts * 100
            total_premium += layer_premium
            layers.append({
                "name": alloc["name"],
                "contracts": layer_contracts,
                "option": best_in_range,
                "premium": layer_premium,
            })

    if not layers:
        return None

    return {
        "layers": layers,
        "total_contracts": sum(l["contracts"] for l in layers),
        "total_premium": total_premium,
    }


def run_covered_call_strategy(
    ticker: str,
    shares: int,
    otm_only: bool = True,
) -> dict:
    """Run the covered call workflow and return a formatted recommendation.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL").
        shares: Number of shares owned (must be multiple of 100).
        otm_only: If True, only recommend OTM options (strike >= stock price).
                  This is the recommended setting for most covered call strategies.

    Returns:
        A dict with:
        - formatted_text: Recommendation or error message.
        - error: Error type string if an error occurred, else None.
    """
    clean_ticker = ticker.strip().upper()

    if shares <= 0 or shares % 100 != 0:
        error = format_error_message(
            "invalid_shares",
            f"You provided {shares} shares.",
        )
        return {
            "formatted_text": error["message"],
            "error": error["error_type"],
        }

    validation = validate_ticker(clean_ticker)
    if not validation.get("valid"):
        error = format_error_message(
            "invalid_ticker",
            validation.get("error") or f"Ticker '{clean_ticker}' not found.",
        )
        return {
            "formatted_text": error["message"],
            "error": error["error_type"],
        }

    if not validation.get("has_options"):
        error = format_error_message(
            "no_options",
            validation.get("error") or f"Ticker '{clean_ticker}' has no options.",
        )
        return {
            "formatted_text": error["message"],
            "error": error["error_type"],
        }

    price_data = get_stock_price(clean_ticker)
    stock_price = price_data.get("price")
    if price_data.get("error") or stock_price is None:
        error = format_error_message(
            "api_error",
            price_data.get("error") or f"Could not fetch price for '{clean_ticker}'.",
        )
        return {
            "formatted_text": error["message"],
            "error": error["error_type"],
        }

    options_data = get_options_chain(clean_ticker)
    if options_data.get("error"):
        error = format_error_message(
            "api_error",
            options_data["error"],
        )
        return {
            "formatted_text": error["message"],
            "error": error["error_type"],
        }

    if not options_data.get("options"):
        error = format_error_message(
            "no_options",
            f"No call options returned for '{clean_ticker}'.",
        )
        return {
            "formatted_text": error["message"],
            "error": error["error_type"],
        }

    filtered = filter_options(options_data)
    if filtered.get("error"):
        error = format_error_message(
            "calculation_error",
            filtered["error"],
        )
        return {
            "formatted_text": error["message"],
            "error": error["error_type"],
        }

    if not filtered.get("filtered_options"):
        error = format_error_message(
            "no_liquid_options",
            "No options met the 7-45 day and liquidity criteria.",
        )
        return {
            "formatted_text": error["message"],
            "error": error["error_type"],
        }

    filtered_options = filtered["filtered_options"]

    # Sanity filter: exclude options with unrealistic bids (e.g., pre-split artifacts)
    # 1. Bid should never exceed stock price
    # 2. For far OTM options (strike > 150% of stock), bid should be < 20% of stock price
    #    This catches pre-split artifacts like NVDA $1650 strike with $188 bid
    def is_sane_option(opt):
        bid = opt.get("bid", 0)
        strike = opt.get("strike", 0)
        if bid > stock_price:
            return False
        if strike > stock_price * 1.5 and bid > stock_price * 0.2:
            return False
        return True

    filtered_options = [opt for opt in filtered_options if is_sane_option(opt)]

    # OTM filter: only include options where strike >= stock price
    # This ensures we recommend options that let the user keep their shares
    # while collecting time value premium
    if otm_only:
        filtered_options = [
            opt for opt in filtered_options
            if opt.get("strike", 0) >= stock_price
        ]

    if not filtered_options:
        error = format_error_message(
            "no_liquid_options",
            "No options met the 7-45 day, liquidity, and moneyness criteria.",
        )
        return {
            "formatted_text": error["message"],
            "error": error["error_type"],
        }

    # Get technical analysis FIRST to inform strike selection
    technical = get_technical_analysis(clean_ticker)

    # Select strike based on technical analysis
    layered_strategy = None
    if technical.get("error"):
        # Fallback to simple best yield if technical analysis fails
        best = find_best_option(filtered_options, stock_price)
        if not best.get("found") or not best.get("best_option"):
            error = format_error_message(
                "calculation_error",
                best.get("error") or "No suitable options found.",
            )
            return {
                "formatted_text": error["message"],
                "error": error["error_type"],
            }
        best_option = best["best_option"]
        strike_selection = {
            "strategy": "standard",
            "reason": "Technical analysis unavailable. Selecting highest yield option.",
            "assignment_risk": "unknown",
            "sentiment": "unknown",
            "use_layered": False,
        }
    else:
        # Use technical analysis to select appropriate strike
        strike_selection = _select_strike_based_on_technicals(
            filtered_options, stock_price, technical
        )
        if not strike_selection.get("option"):
            error = format_error_message(
                "calculation_error",
                "No suitable options found for current market conditions.",
            )
            return {
                "formatted_text": error["message"],
                "error": error["error_type"],
            }
        best_option = strike_selection["option"]

        # Create layered strategy if recommended and enough contracts
        if strike_selection.get("use_layered") and shares >= 300:
            layered_strategy = _create_layered_strategy(
                filtered_options, stock_price, shares, technical
            )
    breakeven = calculate_breakeven(stock_price, best_option["premium"])
    if breakeven.get("error"):
        error = format_error_message(
            "calculation_error",
            breakeven["error"],
        )
        return {
            "formatted_text": error["message"],
            "error": error["error_type"],
        }

    max_profit = calculate_max_profit(
        stock_price=stock_price,
        strike=best_option["strike"],
        premium=best_option["premium"],
        shares=shares,
    )
    if max_profit.get("error"):
        error = format_error_message(
            "calculation_error",
            max_profit["error"],
        )
        return {
            "formatted_text": error["message"],
            "error": error["error_type"],
        }

    recommendation = format_recommendation(
        ticker=clean_ticker,
        stock_price=stock_price,
        best_option=best_option,
        shares=shares,
        breakeven=breakeven,
        max_profit=max_profit,
    )
    if recommendation.get("error"):
        error = format_error_message(
            "calculation_error",
            recommendation["error"],
        )
        return {
            "formatted_text": error["message"],
            "error": error["error_type"],
        }

    message = recommendation["formatted_text"]
    itm_warning = format_itm_warning(best_option["strike"], stock_price)
    if itm_warning.get("is_itm") and itm_warning.get("warning"):
        message = f"{message}\n\n{itm_warning['warning']}"

    # Add layered strategy if available
    if layered_strategy and layered_strategy.get("layers"):
        layered_section = _format_layered_strategy(
            layered_strategy, stock_price, clean_ticker
        )
        message = f"{message}\n\n{layered_section}"

    # Add integrated technical analysis section
    if not technical.get("error"):
        tech_section = _format_integrated_technical_section(
            technical, strike_selection, stock_price, best_option
        )
        message = f"{message}\n\n{tech_section}"

    return {
        "formatted_text": message,
        "error": None,
    }


def _format_layered_strategy(layered: dict, stock_price: float, ticker: str) -> str:
    """Format layered strategy into readable output.

    Args:
        layered: Dict from _create_layered_strategy.
        stock_price: Current stock price.
        ticker: Stock ticker symbol.

    Returns:
        Formatted string section.
    """
    lines = [
        "---",
        "",
        "**📊 Alternative: Layered Strategy (Recommended for Uncertainty)**",
        "",
        "Given the market uncertainty, consider splitting your contracts across multiple strikes:",
        "",
        "| Layer | Contracts | Strike | Premium/Share | Total Premium | OTM % |",
        "|-------|-----------|--------|---------------|---------------|-------|",
    ]

    for layer in layered["layers"]:
        opt = layer["option"]
        strike = opt["strike"]
        otm_pct = ((strike - stock_price) / stock_price) * 100
        lines.append(
            f"| {layer['name']} | {layer['contracts']} | ${strike:.2f} | "
            f"${opt['premium']:.2f} | ${layer['premium']:,.2f} | {otm_pct:.1f}% |"
        )

    lines.extend([
        "",
        f"**Total Premium:** ${layered['total_premium']:,.2f} "
        f"({layered['total_contracts']} contracts)",
        "",
        "**Why Layered?**",
        "- Hedges against unpredictable bounces or reversals",
        "- Conservative layer protects upside if stock surges",
        "- Aggressive layer maximizes premium if stock stays flat",
        "- Better risk-adjusted returns in uncertain conditions",
    ])

    return "\n".join(lines)


def _format_integrated_technical_section(
    analysis: dict,
    strike_selection: dict,
    stock_price: float,
    best_option: dict,
) -> str:
    """Format integrated technical analysis that explains the strike selection.

    Args:
        analysis: Dict from get_technical_analysis.
        strike_selection: Dict from _select_strike_based_on_technicals.
        stock_price: Current stock price.
        best_option: The selected option.

    Returns:
        Formatted string section.
    """
    rsi = analysis.get("rsi", {})
    macd = analysis.get("macd", {})
    mas = analysis.get("moving_averages", {})
    volume = analysis.get("volume", {})

    # Build risk indicator
    risk = strike_selection.get("assignment_risk", "unknown")
    risk_emoji = {
        "high": "🔴",
        "moderate": "🟡",
        "low": "🟢",
        "very_low": "🟢",
    }.get(risk, "⚪")

    sentiment = strike_selection.get("sentiment", "unknown").replace("_", " ").title()
    strategy = strike_selection.get("strategy", "standard").title()

    # Calculate OTM percentage
    strike = best_option.get("strike", stock_price)
    otm_pct = ((strike - stock_price) / stock_price) * 100

    lines = [
        "---",
        "",
        "**📊 Technical Analysis & Strike Selection**",
        "",
        f"**Market Sentiment:** {sentiment} | **Assignment Risk:** {risk_emoji} {risk.replace('_', ' ').title()}",
        "",
        "| Indicator | Value | Signal |",
        "|-----------|-------|--------|",
        f"| RSI(14) | {rsi.get('value', 'N/A')} | {rsi.get('signal', 'N/A').replace('_', ' ').title()} |",
        f"| MACD | {macd.get('histogram', 'N/A'):+.4f} | {macd.get('trend', 'N/A').title()} |",
        f"| vs SMA20 | ${mas.get('sma20', 'N/A')} | {'Above ✓' if mas.get('above_sma20') else 'Below ✗'} |",
        f"| vs SMA50 | ${mas.get('sma50', 'N/A')} | {'Above ✓' if mas.get('above_sma50') else 'Below ✗'} |",
        f"| Volume | {volume.get('volume_ratio', 'N/A')}x avg | {volume.get('signal', 'N/A').replace('_', ' ').title()} |",
        "",
        f"**🎯 Strategy: {strategy}** ({otm_pct:.1f}% OTM)",
        "",
        f"**Why this strike?** {strike_selection.get('reason', 'N/A')}",
    ]

    # Add specific warnings based on sentiment
    bounce_potential = strike_selection.get("bounce_potential")

    if bounce_potential == "oversold_bounce":
        lines.extend([
            "",
            "⚠️ **Oversold Alert (RSI < 30):** Stock may bounce up!",
            "- Historically, oversold conditions often precede reversals",
            "- Consider the layered strategy above to hedge bounce risk",
            "- Or wait for confirmation before selling calls",
        ])
    elif bounce_potential == "overbought_pullback":
        lines.extend([
            "",
            "📈 **Overbought Note (RSI > 70):** Pullback possible.",
            "- Stock may consolidate or pull back from overbought levels",
            "- ATM strikes are appropriate as upside may be limited",
        ])
    elif risk == "high":
        lines.extend([
            "",
            "⚠️ **Caution:** Strong bullish momentum detected. Consider:",
            "- Waiting for a pullback before selling calls",
            "- Using an even higher strike if available",
            "- Being prepared for early assignment",
        ])
    elif risk in ["low", "very_low"] and sentiment == "bearish":
        lines.extend([
            "",
            "⚠️ **Note:** Bearish signals detected. While assignment risk is low,",
            "the stock may decline, affecting your unrealized gains on shares.",
        ])

    return "\n".join(lines)
