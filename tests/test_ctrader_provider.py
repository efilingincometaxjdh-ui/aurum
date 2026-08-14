import os
import unittest
from types import SimpleNamespace

from market.ctrader_provider import CTraderProvider
from market.provider import get_default_provider


class TestCTraderProviderConfig(unittest.TestCase):
    def setUp(self):
        self._orig = dict(os.environ)
        for key in (
            "CTRADER_CLIENT_ID",
            "CTRADER_CLIENT_SECRET",
            "CTRADER_ACCESS_TOKEN",
            "CTRADER_ACCOUNT_ID",
            "CTRADER_ENV",
            "MARKET_PROVIDER",
        ):
            os.environ.pop(key, None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig)

    def test_missing_credentials_raise(self):
        with self.assertRaises(RuntimeError):
            CTraderProvider()

    def test_preprovisioned_token_selects_ctrader(self):
        os.environ["CTRADER_CLIENT_ID"] = "id"
        os.environ["CTRADER_CLIENT_SECRET"] = "secret"
        os.environ["CTRADER_ACCESS_TOKEN"] = "token"

        provider = get_default_provider()
        self.assertIsInstance(provider, CTraderProvider)
        self.assertEqual(provider.environment, "demo")

    def test_invalid_environment_raises(self):
        with self.assertRaises(RuntimeError):
            CTraderProvider(
                client_id="id",
                client_secret="secret",
                access_token="token",
                environment="paper",
            )

    def test_symbol_matching_ignores_separator_style(self):
        self.assertTrue(CTraderProvider._matches_symbol("XAU/USD", "XAUUSD"))
        self.assertTrue(CTraderProvider._matches_symbol("XAU-USD", "XAU/USD"))
        self.assertFalse(CTraderProvider._matches_symbol("XAU/USD", "XAG/USD"))

    def test_trendbar_normalization_uses_relative_prices_and_utc_minutes(self):
        trendbar = SimpleNamespace(
            low=200123456,
            deltaOpen=120000,
            deltaHigh=340000,
            deltaClose=180000,
            utcTimestampInMinutes=29700000,
        )
        normalized = CTraderProvider.normalize_trendbar(trendbar, digits=5)
        self.assertEqual(normalized["low"], 2001.23456)
        self.assertEqual(normalized["open"], 2002.43456)
        self.assertEqual(normalized["high"], 2004.63456)
        self.assertEqual(normalized["close"], 2003.03456)
        self.assertTrue(normalized["datetime"].endswith("+00:00"))

    def test_trendbar_normalization_rounds_to_non_default_symbol_precision(self):
        trendbar = SimpleNamespace(
            low=200123456,
            deltaOpen=120000,
            deltaHigh=340000,
            deltaClose=180000,
            utcTimestampInMinutes=29700000,
        )
        normalized = CTraderProvider.normalize_trendbar(trendbar, digits=2)
        self.assertEqual(normalized["low"], 2001.23)
        self.assertEqual(normalized["open"], 2002.43)
        self.assertEqual(normalized["high"], 2004.63)
        self.assertEqual(normalized["close"], 2003.03)
        self.assertTrue(normalized["datetime"].endswith("+00:00"))

    def test_invalid_relative_price_and_digits_are_rejected(self):
        with self.assertRaises(ValueError):
            CTraderProvider._price_from_relative(200123456, -1)
        with self.assertRaises(ValueError):
            CTraderProvider._price_from_relative(200123456, True)
        with self.assertRaises(ValueError):
            CTraderProvider._price_from_relative(200123456.0, 5)

    def test_trendbar_missing_required_fields_are_rejected(self):
        with self.assertRaises(ValueError):
            CTraderProvider.normalize_trendbar(SimpleNamespace(utcTimestampInMinutes=1), digits=5)
        with self.assertRaises(ValueError):
            CTraderProvider.normalize_trendbar(SimpleNamespace(low=1), digits=5)


if __name__ == "__main__":
    unittest.main()
