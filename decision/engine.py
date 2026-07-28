# ============================================================
# RAHUL AI TEAM
# DECISION ENGINE
# Version 1.0
# ============================================================


class DecisionEngine:

    def evaluate(self, macro, technical):

        reasons = []
        score = 50

        # ----------------------------------------------------
        # 1. NEWS RISK
        # ----------------------------------------------------

        if macro["news_risk"] == "EXTREME":
            return {
                "decision": "NO_TRADE",
                "confidence": 100,
                "risk": "EXTREME",
                "reasons": [
                    "Extreme macro news risk."
                ]
            }

        # ----------------------------------------------------
        # 2. MACRO
        # ----------------------------------------------------

        if macro["gold_bias"] == "BULLISH":
            score += 15
            reasons.append("Macro supports Gold")

        elif macro["gold_bias"] == "BEARISH":
            score -= 15
            reasons.append("Macro bearish for Gold")

        # ----------------------------------------------------
        # 3. TREND
        # ----------------------------------------------------

        if technical["trend"] == "Bullish":
            score += 15
            reasons.append("Trend is Bullish")

        elif technical["trend"] == "Bearish":
            score -= 15
            reasons.append("Trend is Bearish")

        # ----------------------------------------------------
        # 4. EMA
        # ----------------------------------------------------

        if technical["ema20"] > technical["ema50"]:
            score += 10
            reasons.append("EMA20 above EMA50")

        else:
            score -= 10
            reasons.append("EMA20 below EMA50")

        # ----------------------------------------------------
        # 5. ADX
        # ----------------------------------------------------

        if technical["adx"] >= 25:
            score += 5
            reasons.append("Strong trend confirmed")

        else:
            reasons.append("Weak trend")

        # ----------------------------------------------------
        # 6. RSI
        # ----------------------------------------------------

        if technical["rsi"] > 70:
            score -= 5
            reasons.append("RSI overbought")

        elif technical["rsi"] < 30:
            score += 5
            reasons.append("RSI oversold")

        # ----------------------------------------------------
        # 7. LIMIT SCORE
        # ----------------------------------------------------

        score = max(0, min(score, 100))

        # ----------------------------------------------------
        # 8. FINAL DECISION
        # ----------------------------------------------------

        if score >= 80:
            decision = "STRONG_BULLISH"

        elif score >= 65:
            decision = "BULLISH"

        elif score >= 45:
            decision = "NEUTRAL"

        elif score >= 25:
            decision = "BEARISH"

        else:
            decision = "STRONG_BEARISH"

        return {
            "decision": decision,
            "confidence": score,
            "risk": macro["news_risk"],
            "reasons": reasons,
        }
