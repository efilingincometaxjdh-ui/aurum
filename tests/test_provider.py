import unittest
from datetime import datetime, timezone, timedelta

from market.provider import IMarketDataProvider, TwelveDataProvider
from agent02 import collect_market_data, build_market_state


class FakeProvider(IMarketDataProvider):
    def __init__(self, now=None):
        self.now = now or datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)

    def _iso(self, dt):
        return dt.isoformat()

    def _make_candles(self, count, interval_minutes=5):
        candles = []
        for i in range(count):
            t = self.now + timedelta(minutes=i * interval_minutes)
            base = 2000.0 + (i * 0.5)
            candles.append({
                "datetime": self._iso(t),
                "open": base,
                "high": base + 1.0,
                "low": base - 1.0,
                "close": base + 0.25,
            })
        return candles

    def fetch_candles(self, label: str, interval: str):
        # Return deterministic data per label
        if label == "M5":
            return self._make_candles(50, interval_minutes=5)
        if label == "M15":
            return self._make_candles(60, interval_minutes=15)
        if label == "H1":
            return self._make_candles(48, interval_minutes=60)
        if label == "H4":
            return self._make_candles(30, interval_minutes=240)
        return []


class ProviderIntegrationTests(unittest.TestCase):
    def test_collect_with_fake_provider(self):
        provider = FakeProvider()
        data = collect_market_data(provider=provider)
        # Ensure provider returned candles for each timeframe
        self.assertIn("M5", data)
        self.assertIn("H4", data)
        # Build market state from the data
        state, status, errors, metadata = build_market_state(data)
        self.assertIn("M5", state)
        # Indicators should exist
        self.assertIn("ema20", state["M5"])
        self.assertIn("rsi", state["M5"])
        self.assertEqual(metadata["symbol"], "XAU/USD")

    def test_twelvedata_provider_missing_key_raises(self):
        with self.assertRaises(RuntimeError):
            TwelveDataProvider().fetch_candles("M5", "5min")


if __name__ == "__main__":
    unittest.main()
