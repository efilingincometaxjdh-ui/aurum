import os
import unittest

from market.provider import _import_ctrader


class TestCTraderProviderConfig(unittest.TestCase):
    def setUp(self):
        # Ensure environment is clean for tests
        self._orig = dict(os.environ)
        os.environ.pop("CTRADER_CLIENT_ID", None)
        os.environ.pop("CTRADER_CLIENT_SECRET", None)
        os.environ.pop("CTRADER_TOKEN_URL", None)
        os.environ.pop("CTRADER_CANDLES_URL", None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig)

    def test_missing_credentials_raises(self):
        CTrader = _import_ctrader()
        if CTrader is None:
            # If provider failed to import (requests missing), skip
            self.skipTest("CTrader provider not importable")

        with self.assertRaises(RuntimeError):
            CTrader()

    def test_requires_token_and_candles_url(self):
        CTrader = _import_ctrader()
        if CTrader is None:
            self.skipTest("CTrader provider not importable")

        os.environ["CTRADER_CLIENT_ID"] = "id"
        os.environ["CTRADER_CLIENT_SECRET"] = "secret"
        # missing token/candles url should raise
        with self.assertRaises(RuntimeError):
            CTrader()

