# ============================================================
# RAHUL AI TEAM
# AGENT 02 — XAUUSD MARKET INTELLIGENCE
# ============================================================

import os
from datetime import datetime, timezone

from market.provider import get_default_provider
from market.indicators import calculate_indicators
from market.structure import analyze_structure
from utils.json_writer import write_state

SYMBOL = "XAU/USD"
TIMEFRAMES = {"M5": "5min", "M15": "15min", "H1": "1h", "H4": "4h"}


def fetch_candles(label, interval):
    """Backward-compatible wrapper around the market provider implementation.

    This preserves the previous behaviour while using the configurable
    provider factory. If no provider is supplied via dependency injection,
    the runtime default provider (get_default_provider) is used.
    """
    provider = get_default_provider()
    return provider.fetch_candles(label, interval)


def collect_market_data(provider=None):
    """Collect market data for all configured timeframes.

    If no provider is supplied, the repository default provider is constructed
    via get_default_provider(), which selects the configured provider (cTrader
    when configured) or falls back to TwelveDataProvider for backwards
    compatibility.
    """
    if provider is None:
        provider = get_default_provider()

    market_data = {}
    for label, interval in TIMEFRAMES.items():
        print(f"Fetching XAUUSD {label}...")
        candles = provider.fetch_candles(label, interval)
        market_data[label] = candles
        if candles:
            latest = candles[-1]
            print(f"✅ {label}: {len(candles)} candles | Latest close: {latest['close']:.2f} | Time: {latest['datetime']}")
    return market_data


def validate_market_data(market_data):
    available = [timeframe for timeframe, candles in market_data.items() if candles]
    missing = [timeframe for timeframe, candles in market_data.items() if not candles]
    return available, missing


def build_market_state(market_data):
    available, missing = validate_market_data(market_data)
    market_state = {}
    errors = []

    for timeframe in available:
        try:
            indicators = calculate_indicators(market_data[timeframe])
            structure = analyze_structure(market_data[timeframe])
            market_state[timeframe] = {
                "ema20": indicators["ema20"],
                "ema50": indicators["ema50"],
                "rsi": indicators["rsi14"],
                "adx": indicators["adx14"],
                "atr": indicators["atr14"],
                "trend": structure["trend"],
                "support": structure["support"],
                "resistance": structure["resistance"],
                "swing_high": structure["swing_high"],
                "swing_low": structure["swing_low"],
            }
        except Exception as error:
            errors.append(f"{timeframe}: analysis failed: {error}")

    for timeframe in missing:
        errors.append(f"{timeframe}: market data unavailable")

    if not market_state:
        status = "FAILED"
    elif errors:
        status = "DEGRADED"
    else:
        status = "SUCCESS"

    metadata = {
        "symbol": SYMBOL,
        "requested_timeframes": list(TIMEFRAMES.keys()),
        "available_timeframes": available,
        "missing_timeframes": missing,
    }
    return market_state, status, errors, metadata


def main():
    print("\n🤖 RAHUL AI TEAM")
    print("=" * 60)
    print("AGENT 02 — XAUUSD MARKET INTELLIGENCE")
    print("=" * 60)

    try:
        market_data = collect_market_data()
    except RuntimeError as error:
        write_state(
            agent="Agent02",
            version="0.4",
            filename="agent02.json",
            data={},
            status="FAILED",
            errors=[str(error)],
            metadata={"symbol": SYMBOL},
        )
        print(f"❌ {error}")
        raise SystemExit(1)

    market_state, status, errors, metadata = build_market_state(market_data)
    write_state(
        agent="Agent02",
        version="0.4",
        filename="agent02.json",
        data=market_state,
        status=status,
        errors=errors,
        metadata=metadata,
    )

    print(f"UTC: {datetime.now(timezone.utc).isoformat()}")
    print(f"Agent02 health: {status}")
    print(f"Usable timeframes: {', '.join(market_state) if market_state else 'NONE'}")
    if errors:
        for error in errors:
            print(f"⚠️ {error}")

    if status == "FAILED":
        raise SystemExit(1)

    print("✅ Agent02 state written to data/current/agent02.json")


if __name__ == "__main__":
    main()
