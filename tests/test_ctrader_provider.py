import os
import unittest

from market.provider import _import_ctrader


class TestCTraderProviderConfig(unittest.TestCase):
    def setUp(self):
        # Ensure environment is clean for tests
        self._orig = dict(os.environ)
        os.environ.pop("CTRADER_CLIENT_ID", None)
        os.environ.pop("CTRADER_CLIENT_SECRET", None)
        os.environ.pop("CTRADER_ACCESS_TOKEN", None)
        os.environ.pop("CTRADER_API_BASE", None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig)

    def test_missing_credentials_raises(self):
        CTrader = _import_ctrader()
        if CTrader is None:
            self.skipTest("CTrader provider not importable")

        # Without access token and without token endpoint, construction should fail
        with self.assertRaises(RuntimeError):
            CTrader()

    def test_requires_access_token_and_api_base(self):
        CTrader = _import_ctrader()
        if CTrader is None:
            self.skipTest("CTrader provider not importable")

        # Provide access token and api base -> should instantiate
        os.environ["CTRADER_CLIENT_ID"] = "id"
        os.environ["CTRADER_CLIENT_SECRET"] = "secret"
        os.environ["CTRADER_ACCESS_TOKEN"] = "tok"
        os.environ["CTRADER_API_BASE"] = "https://api.ctrader.example"
        provider = CTrader()
        self.assertIsNotNone(provider)
