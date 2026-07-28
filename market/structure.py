# ============================================================
# RAHUL AI TEAM
# MARKET STRUCTURE ANALYZER
# ============================================================

def analyze_structure(candles):
    """
    Basic market structure analysis.
    """

    if len(candles) < 20:
        raise ValueError("Not enough candles for structure analysis.")

    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]

    ema20 = sum(closes[-20:]) / 20

    latest_close = closes[-1]

    if latest_close > ema20:
        trend = "Bullish"
    elif latest_close < ema20:
        trend = "Bearish"
    else:
        trend = "Sideways"

    support = min(lows[-20:])
    resistance = max(highs[-20:])

    swing_high = highs[-2]
    swing_low = lows[-2]

    return {
        "trend": trend,
        "support": support,
        "resistance": resistance,
        "swing_high": swing_high,
        "swing_low": swing_low,
    }
