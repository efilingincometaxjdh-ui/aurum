"""
Deterministic Risk Engine for Agent 01.

Evaluates macro intelligence signals and produces deterministic bot actions.
Never uses machine learning. Rules-based safety logic prevents dangerous trading.
"""

from config.settings import CONFIDENCE_THRESHOLD, STRONG_SCORE_THRESHOLD


class RiskEngine:
    """
    Deterministic rule-based engine that converts macro signals into bot actions.
    
    Input: Dictionary of macro signals from Gemini analysis.
    Output: (bot_action, rationale) tuple.
    
    Permitted bot_action values:
    - ALLOW_BUYS: Safe to execute buy orders
    - ALLOW_SELLS: Safe to execute sell orders
    - ALLOW_BOTH: Conditions are neutral, both permitted
    - CAUTION: Conflicting/ambiguous signals, request human review
    - BLOCK_TRADING: Critical safety rule triggered, no trading allowed
    """

    VALID_ACTIONS = {
        "ALLOW_BUYS",
        "ALLOW_SELLS",
        "ALLOW_BOTH",
        "CAUTION",
        "BLOCK_TRADING",
    }

    def __init__(self, signals):
        """
        Initialize with macro signals from Agent 01.
        
        Args:
            signals: Dictionary containing:
                - gold_bias: "BULLISH" | "BEARISH" | "NEUTRAL"
                - usd_bias: "BULLISH" | "BEARISH" | "NEUTRAL"
                - gold_score: -100 to +100
                - usd_score: -100 to +100
                - news_risk: "LOW" | "MEDIUM" | "HIGH" | "EXTREME"
                - confidence: 0 to 100
                - major_event_detected: bool
        """
        self.signals = signals
        self.gold_bias = signals.get("gold_bias", "NEUTRAL").upper()
        self.usd_bias = signals.get("usd_bias", "NEUTRAL").upper()
        self.gold_score = int(signals.get("gold_score", 0))
        self.usd_score = int(signals.get("usd_score", 0))
        self.news_risk = signals.get("news_risk", "HIGH").upper()
        self.confidence = int(signals.get("confidence", 0))
        self.major_event_detected = bool(signals.get("major_event_detected", False))

    def evaluate(self):
        """
        Apply deterministic safety rules and produce bot action.
        
        Returns:
            Tuple of (action, rationale) where:
            - action: One of VALID_ACTIONS
            - rationale: String explanation of decision
        """

        # ============================================================
        # RULE 1: CRITICAL SAFETY — EXTREME NEWS RISK
        # ============================================================
        if self.news_risk == "EXTREME":
            return (
                "BLOCK_TRADING",
                "⛔ EXTREME news risk detected. Trading blocked until conditions stabilize.",
            )

        # ============================================================
        # RULE 2: CRITICAL SAFETY — MAJOR EVENT + HIGH RISK
        # ============================================================
        if self.major_event_detected and self.news_risk in {"HIGH", "EXTREME"}:
            return (
                "BLOCK_TRADING",
                "⛔ Major economic event detected during high-risk period. "
                "Trading blocked to prevent whipsaw losses.",
            )

        # ============================================================
        # RULE 3: LOW CONFIDENCE — INSUFFICIENT DATA
        # ============================================================
        if self.confidence < CONFIDENCE_THRESHOLD:
            return (
                "CAUTION",
                f"⚠️  Confidence too low ({self.confidence}% < {CONFIDENCE_THRESHOLD}% threshold). "
                "Insufficient data for directional decision. Request human review.",
            )

        # ============================================================
        # RULE 4: STRONG BULLISH GOLD + BEARISH USD → ALLOW_BUYS
        # ============================================================
        if (
            self.gold_score >= STRONG_SCORE_THRESHOLD
            and self.usd_score <= -STRONG_SCORE_THRESHOLD
            and self.news_risk in {"LOW", "MEDIUM"}
        ):
            return (
                "ALLOW_BUYS",
                f"✅ Strong bullish Gold signal (score: {self.gold_score:+d}) "
                f"with bearish USD (score: {self.usd_score:+d}). "
                f"News risk is {self.news_risk}. Buy orders permitted.",
            )

        # ============================================================
        # RULE 5: STRONG BEARISH GOLD + BULLISH USD → ALLOW_SELLS
        # ============================================================
        if (
            self.gold_score <= -STRONG_SCORE_THRESHOLD
            and self.usd_score >= STRONG_SCORE_THRESHOLD
            and self.news_risk in {"LOW", "MEDIUM"}
        ):
            return (
                "ALLOW_SELLS",
                f"✅ Strong bearish Gold signal (score: {self.gold_score:+d}) "
                f"with bullish USD (score: {self.usd_score:+d}). "
                f"News risk is {self.news_risk}. Sell orders permitted.",
            )

        # ============================================================
        # RULE 6: NEUTRAL CONDITIONS + ADEQUATE DATA → ALLOW_BOTH
        # ============================================================
        if (
            abs(self.gold_score) < STRONG_SCORE_THRESHOLD
            and abs(self.usd_score) < STRONG_SCORE_THRESHOLD
            and self.news_risk == "LOW"
            and self.confidence >= CONFIDENCE_THRESHOLD
        ):
            return (
                "ALLOW_BOTH",
                f"✅ Neutral macro conditions detected "
                f"(Gold: {self.gold_score:+d}, USD: {self.usd_score:+d}, "
                f"Risk: {self.news_risk}, Confidence: {self.confidence}%). "
                f"Both buy and sell orders permitted under conditions.",
            )

        # ============================================================
        # RULE 7: CONFLICTING SIGNALS → CAUTION
        # ============================================================
        # Gold bullish but USD also bullish (conflicting)
        if (
            self.gold_bias == "BULLISH"
            and self.usd_bias == "BULLISH"
        ):
            return (
                "CAUTION",
                "⚠️  Conflicting signals: Both Gold and USD show bullish bias. "
                "This is contradictory in XAUUSD pair. Request human analysis.",
            )

        # Gold bearish but USD also bearish (conflicting)
        if (
            self.gold_bias == "BEARISH"
            and self.usd_bias == "BEARISH"
        ):
            return (
                "CAUTION",
                "⚠️  Conflicting signals: Both Gold and USD show bearish bias. "
                "This is contradictory in XAUUSD pair. Request human analysis.",
            )

        # ============================================================
        # RULE 8: MODERATE SIGNALS + HIGH NEWS RISK → CAUTION
        # ============================================================
        if self.news_risk == "HIGH":
            if abs(self.gold_score) < STRONG_SCORE_THRESHOLD * 1.5:
                return (
                    "CAUTION",
                    f"⚠️  Signals are present but muted (Gold: {self.gold_score:+d}, "
                    f"USD: {self.usd_score:+d}). News risk is {self.news_risk}. "
                    f"Increased uncertainty warrants caution.",
                )

        # ============================================================
        # RULE 9: MEDIUM NEWS RISK + WEAK SIGNALS → CAUTION
        # ============================================================
        if self.news_risk == "MEDIUM":
            if (
                abs(self.gold_score) < STRONG_SCORE_THRESHOLD
                or abs(self.usd_score) < STRONG_SCORE_THRESHOLD
            ):
                return (
                    "CAUTION",
                    f"⚠️  Weak signals (Gold: {self.gold_score:+d}, USD: {self.usd_score:+d}) "
                    f"during {self.news_risk} news risk. Insufficient clarity for directional trades.",
                )

        # ============================================================
        # RULE 10: DEFAULT — CAUTION (NO RULE MATCHED)
        # ============================================================
        return (
            "CAUTION",
            f"⚠️  No clear rule matched. Signal state: "
            f"Gold({self.gold_bias}/{self.gold_score:+d}) "
            f"USD({self.usd_bias}/{self.usd_score:+d}) "
            f"Risk:{self.news_risk} Confidence:{self.confidence}%. "
            f"Request human review.",
        )
