# ============================================================
# RAHUL AI TEAM
# AGENT 02 — XAUUSD MARKET INTELLIGENCE
# Stage 1: Market Data Collector
# ============================================================

import os
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from market.indicators import calculate_indicators
from market.structure import analyze_structure


# ============================================================
# 1. CONFIGURATION
# ============================================================

API_KEY = os.getenv("TWELVE_DATA_API_KEY")

BASE_URL = "https://api.twelvedata.com/time_series"

SYMBOL = "XAU/USD"

TIMEFRAMES = {
    "M5": "5min",
    "M15": "15min",
    "H1": "1h",
    "H4": "4h",
}

OUTPUT_SIZE = 100
REQUEST_TIMEOUT = 15


# ============================================================
# 2. FETCH MARKET DATA
# ============================================================

def fetch_candles(label, interval):

    if not API_KEY:
        raise RuntimeError(
            "TWELVE_DATA_API_KEY environment variable is missing."
        )

    params = {
        "symbol": SYMBOL,
        "interval": interval,
        "outputsize": OUTPUT_SIZE,
        "apikey": API_KEY,
        "format": "JSON",
    }

    url = BASE_URL + "?" + urllib.parse.urlencode(params)

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Rahul-AI-Team-Agent02/1.0"
        }
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=REQUEST_TIMEOUT
        ) as response:

            raw_data = response.read().decode("utf-8")
            data = json.loads(raw_data)

    except Exception as error:
        print(f"❌ {label}: Request failed: {error}")
        return None

    # Twelve Data may return API errors as JSON.
    if data.get("status") == "error":
        print(
            f"❌ {label}: Twelve Data error: "
            f"{data.get('message', 'Unknown error')}"
        )
        return None

    values = data.get("values")

    if not values:
        print(f"❌ {label}: No candle data received.")
        return None

    candles = []

    for item in values:

        try:
            candle = {
                "datetime": item["datetime"],
                "open": float(item["open"]),
                "high": float(item["high"]),
                "low": float(item["low"]),
                "close": float(item["close"]),
            }

            candles.append(candle)

        except (KeyError, TypeError, ValueError):
            continue

    if not candles:
        print(f"❌ {label}: No valid candles after validation.")
        return None

    # Twelve Data normally returns newest candle first.
    # Store oldest -> newest for future indicator calculations.
    candles.reverse()

    return candles


# ============================================================
# 3. COLLECT XAUUSD TIMEFRAMES
# ============================================================

def collect_market_data():

    market_data = {}

    for label, interval in TIMEFRAMES.items():

        print(f"Fetching XAUUSD {label}...")

        candles = fetch_candles(label, interval)

        if candles is None:
            market_data[label] = None
            continue

        latest = candles[-1]

        market_data[label] = candles

        print(
            f"✅ {label}: "
            f"{len(candles)} candles | "
            f"Latest close: {latest['close']:.2f} | "
            f"Time: {latest['datetime']}"
        )

    return market_data


# ============================================================
# 4. VALIDATE DATA QUALITY
# ============================================================

def validate_market_data(market_data):

    available = [
        timeframe
        for timeframe, candles in market_data.items()
        if candles
    ]

    missing = [
        timeframe
        for timeframe, candles in market_data.items()
        if not candles
    ]

    return available, missing


# ============================================================
# 5. MAIN
# ============================================================

def main():

    print()
    print("🤖 RAHUL AI TEAM")
    print("=" * 60)
    print("AGENT 02 — XAUUSD MARKET INTELLIGENCE")
    print("Stage 1: Market Data Collector")
    print("=" * 60)
    print()

    market_data = collect_market_data()

    available, missing = validate_market_data(market_data)
    indicator_results = {}

    for timeframe in available:
        try:
            indicator_results[timeframe] = calculate_indicators(
                market_data[timeframe]
            )
        except Exception as error:
            print(
                f"⚠️ {timeframe}: "
                f"Indicator calculation failed: {error}"
            )
            indicator_results[timeframe] = None

    structure_results = {}

    for timeframe in available:
        try:
            structure_results[timeframe] = analyze_structure(
                market_data[timeframe]
            )
        except Exception as error:
            print(
                f"⚠️ {timeframe}: "
                f"Structure analysis failed: {error}"
            )
            structure_results[timeframe] = None
    print()
    print("=" * 60)
    print("MARKET DATA STATUS")
    print("=" * 60)

    print(
        "UTC:",
        datetime.now(timezone.utc).isoformat()
    )

    print(
        "Available:",
        ", ".join(available) if available else "NONE"
    )

    print(
        "Missing:",
        ", ".join(missing) if missing else "NONE"
    )

    if not available:

        print()
        print("❌ Agent 02 has no usable XAUUSD market data.")

        raise SystemExit(1)

    print()

    for timeframe in available:

        candles = market_data[timeframe]
        latest = candles[-1]

        print(
            f"{timeframe:<4} | "
            f"O {latest['open']:.2f} | "
            f"H {latest['high']:.2f} | "
            f"L {latest['low']:.2f} | "
            f"C {latest['close']:.2f}"
        )

        print()
    print("=" * 60)
    print("TECHNICAL MARKET STATE")
    print("=" * 60)

    for timeframe in available:

        indicators = indicator_results.get(timeframe)

        if not indicators:
            print(f"{timeframe}: indicators unavailable")
            continue

        print()
        print(f"{timeframe}")
        print(f"  EMA20 : {indicators['ema20']:.2f}")
        print(f"  EMA50 : {indicators['ema50']:.2f}")
        print(f"  RSI14 : {indicators['rsi14']:.2f}")
        print(f"  ADX14 : {indicators['adx14']:.2f}")
        print(f"  ATR14 : {indicators['atr14']:.2f}")
    print()

    print("=" * 60)
    print("MARKET STRUCTURE")
    print("=" * 60)
    
    for timeframe in available:
    
        structure = structure_results.get(timeframe)
    
        if not structure:
            print(f"{timeframe}: structure unavailable")
            continue
    
        print()
        print(timeframe)
        print(f"  Trend      : {structure['trend']}")
        print(f"  Support    : {structure['support']:.2f}")
        print(f"  Resistance : {structure['resistance']:.2f}")
        print(f"  Swing High : {structure['swing_high']:.2f}")
        print(f"  Swing Low  : {structure['swing_low']:.2f}")
    
    print()
    print("✅ Agent 02 Stage 3 market structure analysis complete.")


if __name__ == "__main__":
    main()
