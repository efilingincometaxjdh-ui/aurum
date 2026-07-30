import unittest

from trader_view import build_trader_view


class TraderViewTests(unittest.TestCase):
    def test_read_only_view_exposes_decision_and_permission(self):
        alert = {"data": {"permission": "ALLOW_BUYS", "reason": "Safe buy permission", "fresh": True, "execution_enabled": False}}
        decision = {
            "data": {"decision": "BUY", "confidence": 82, "risk": "LOW", "reasons": ["Technical and macro aligned"]},
            "metadata": {"technical_fusion": {"usable_timeframes": ["H4", "H1", "M15", "M5"], "trend_votes": {"bullish": 9, "bearish": 1}}},
        }
        macro = {"data": {"gold_bias": "BULLISH", "news_risk": "LOW"}}
        view = build_trader_view(alert, decision, macro)
        self.assertEqual(view["decision"], "BUY")
        self.assertEqual(view["permission"], "ALLOW_BUYS")
        self.assertEqual(view["timeframe_conflict"], "LOW")
        self.assertFalse(view["execution_enabled"])

    def test_high_timeframe_disagreement_is_visible(self):
        alert = {"data": {"permission": "CAUTION", "reason": "Conflict", "fresh": True, "execution_enabled": False}}
        decision = {"data": {"decision": "NO_TRADE", "confidence": 45, "risk": "HIGH", "reasons": []}, "metadata": {"technical_fusion": {"trend_votes": {"bullish": 5, "bearish": 5}}}}
        view = build_trader_view(alert, decision, {})
        self.assertEqual(view["timeframe_conflict"], "HIGH")
        self.assertEqual(view["permission"], "CAUTION")

    def test_view_strips_any_execution_authority(self):
        alert = {"data": {"permission": "ALLOW_BOTH", "reason": "Unexpected", "fresh": True, "execution_enabled": True}}
        view = build_trader_view(alert, {}, {})
        self.assertEqual(view["permission"], "BLOCK_TRADING")
        self.assertFalse(view["execution_enabled"])

    def test_missing_inputs_fail_safe(self):
        view = build_trader_view(None, None, None)
        self.assertEqual(view["decision"], "NO_TRADE")
        self.assertEqual(view["permission"], "BLOCK_TRADING")
        self.assertEqual(view["risk"], "EXTREME")
        self.assertFalse(view["execution_enabled"])


if __name__ == "__main__":
    unittest.main()
