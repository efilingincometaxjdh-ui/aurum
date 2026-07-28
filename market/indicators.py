# ============================================================
# RAHUL AI TEAM
# AGENT 02 — MARKET INDICATORS
# ============================================================

from math import isfinite


def _validate_candles(candles):
    if not candles:
        raise ValueError("No candle data supplied.")

    required = {"open", "high", "low", "close"}

    for candle in candles:
        if not required.issubset(candle):
            raise ValueError("Candle is missing OHLC fields.")


# ============================================================
# EMA
# ============================================================

def ema(values, period):
    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)

    # Start with SMA
    current_ema = sum(values[:period]) / period

    for value in values[period:]:
        current_ema = (
            (value - current_ema) * multiplier
            + current_ema
        )

    return current_ema


# ============================================================
# RSI — Wilder Method
# ============================================================

def rsi(values, period=14):
    if len(values) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(1, len(values)):
        change = values[i] - values[i - 1]

        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (
            (avg_gain * (period - 1)) + gains[i]
        ) / period

        avg_loss = (
            (avg_loss * (period - 1)) + losses[i]
        ) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


# ============================================================
# ATR — Wilder Method
# ============================================================

def atr(candles, period=14):
    _validate_candles(candles)

    if len(candles) < period + 1:
        return None

    true_ranges = []

    for i in range(1, len(candles)):
        high = candles[i]["high"]
        low = candles[i]["low"]
        previous_close = candles[i - 1]["close"]

        true_range = max(
            high - low,
            abs(high - previous_close),
            abs(low - previous_close),
        )

        true_ranges.append(true_range)

    current_atr = sum(true_ranges[:period]) / period

    for value in true_ranges[period:]:
        current_atr = (
            (current_atr * (period - 1)) + value
        ) / period

    return current_atr


# ============================================================
# ADX — Wilder Method
# ============================================================

def adx(candles, period=14):
    _validate_candles(candles)

    if len(candles) < (period * 2) + 1:
        return None

    trs = []
    plus_dm = []
    minus_dm = []

    for i in range(1, len(candles)):
        current = candles[i]
        previous = candles[i - 1]

        up_move = current["high"] - previous["high"]
        down_move = previous["low"] - current["low"]

        plus_dm.append(
            up_move
            if up_move > down_move and up_move > 0
            else 0.0
        )

        minus_dm.append(
            down_move
            if down_move > up_move and down_move > 0
            else 0.0
        )

        trs.append(
            max(
                current["high"] - current["low"],
                abs(current["high"] - previous["close"]),
                abs(current["low"] - previous["close"]),
            )
        )

    smoothed_tr = sum(trs[:period])
    smoothed_plus_dm = sum(plus_dm[:period])
    smoothed_minus_dm = sum(minus_dm[:period])

    dx_values = []

    for i in range(period, len(trs)):
        smoothed_tr = (
            smoothed_tr
            - (smoothed_tr / period)
            + trs[i]
        )

        smoothed_plus_dm = (
            smoothed_plus_dm
            - (smoothed_plus_dm / period)
            + plus_dm[i]
        )

        smoothed_minus_dm = (
            smoothed_minus_dm
            - (smoothed_minus_dm / period)
            + minus_dm[i]
        )

        if smoothed_tr == 0:
            continue

        plus_di = 100 * (
            smoothed_plus_dm / smoothed_tr
        )

        minus_di = 100 * (
            smoothed_minus_dm / smoothed_tr
        )

        denominator = plus_di + minus_di

        if denominator == 0:
            dx = 0.0
        else:
            dx = (
                100
                * abs(plus_di - minus_di)
                / denominator
            )

        dx_values.append(dx)

    if len(dx_values) < period:
        return None

    current_adx = sum(dx_values[:period]) / period

    for value in dx_values[period:]:
        current_adx = (
            (current_adx * (period - 1)) + value
        ) / period

    return current_adx


# ============================================================
# COMPLETE TIMEFRAME ANALYSIS
# ============================================================

def calculate_indicators(candles):
    _validate_candles(candles)

    closes = [candle["close"] for candle in candles]

    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    rsi14 = rsi(closes, 14)
    atr14 = atr(candles, 14)
    adx14 = adx(candles, 14)

    values = {
        "ema20": ema20,
        "ema50": ema50,
        "rsi14": rsi14,
        "atr14": atr14,
        "adx14": adx14,
    }

    for name, value in values.items():
        if value is not None and not isfinite(value):
            values[name] = None

    return values
