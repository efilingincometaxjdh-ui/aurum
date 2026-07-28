# ============================================================
# RAHUL AI TEAM
# PERMISSION ENGINE
# ============================================================


class PermissionEngine:

    def evaluate(self, decision):

        state = decision["decision"]
        confidence = decision["confidence"]
        risk = decision["risk"]

        # ---------------------------------------------
        # HARD SAFETY RULES
        # ---------------------------------------------

        if risk == "EXTREME":
            return {
                "permission": "BLOCK_TRADING",
                "reason": "Extreme news risk."
            }

        # ---------------------------------------------
        # DECISION MAPPING
        # ---------------------------------------------

        if state == "STRONG_BULLISH":
            return {
                "permission": "ALLOW_BUYS",
                "reason": "Strong bullish environment."
            }

        if state == "BULLISH":
            return {
                "permission": "ALLOW_BUYS",
                "reason": "Bullish environment."
            }

        if state == "NEUTRAL":
            return {
                "permission": "ALLOW_BOTH",
                "reason": "Neutral market."
            }

        if state == "BEARISH":
            return {
                "permission": "ALLOW_SELLS",
                "reason": "Bearish environment."
            }

        if state == "STRONG_BEARISH":
            return {
                "permission": "ALLOW_SELLS",
                "reason": "Strong bearish environment."
            }

        return {
            "permission": "CAUTION",
            "reason": "Unknown market state."
        }
