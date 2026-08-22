import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from integrations.ctrader_cbot.receiver import validate_bar


class CTraderCbotReceiverTests(unittest.TestCase):
    def setUp(self):
        self.payload = {
            "schemaVersion": 1,
            "provider": "ctrader_cbot",
            "symbol": "XAUUSD",
            "timeframe": "M5",
            "timestamp": "2026-08-21T10:35:00+00:00",
            "open": 4375.96,
            "high": 4376.63,
            "low": 4375.19,
            "close": 4376.58,
            "tickVolume": 1234,
            "digits": 2,
        }

    def test_valid_bar_is_normalized_to_utc(self):
        payload = dict(self.payload)
        payload["timestamp"] = "2026-08-21T16:05:00+05:30"
        result = validate_bar(payload)
        self.assertEqual(result["timestamp"], "2026-08-21T10:35:00+00:00")
        self.assertEqual(result["provider"], "ctrader_cbot")

    def test_missing_required_field_rejected(self):
        payload = dict(self.payload)
        del payload["close"]
        with self.assertRaises(ValueError):
            validate_bar(payload)

    def test_non_finite_price_rejected(self):
        payload = dict(self.payload)
        payload["close"] = float("nan")
        with self.assertRaises(ValueError):
            validate_bar(payload)

    def test_invalid_ohlc_relationship_rejected(self):
        payload = dict(self.payload)
        payload["high"] = 4375.00
        with self.assertRaises(ValueError):
            validate_bar(payload)

    def test_negative_volume_rejected(self):
        payload = dict(self.payload)
        payload["tickVolume"] = -1
        with self.assertRaises(ValueError):
            validate_bar(payload)

    def test_wrong_provider_rejected(self):
        payload = dict(self.payload)
        payload["provider"] = "simulation"
        with self.assertRaises(ValueError):
            validate_bar(payload)


if __name__ == "__main__":
    unittest.main()
