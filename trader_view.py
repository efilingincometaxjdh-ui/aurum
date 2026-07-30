# RAHUL AI TEAM — TRADER-READABLE VIEW

from utils.json_reader import read_state
from utils.json_writer import write_state


def build_trader_view(alert_state, decision_state=None, macro_state=None):
    """Build a human-readable, read-only trading intelligence snapshot.

    This layer never grants permission and never enables execution. Agent 05/06
    remain authoritative for permission and fail-closed behavior.
    """
    alert_data = alert_state.get("data", {}) if isinstance(alert_state, dict) else {}
    decision_data = decision_state.get("data", {}) if isinstance(decision_state, dict) else {}
    decision_meta = decision_state.get("metadata", {}) if isinstance(decision_state, dict) else {}
    macro_data = macro_state.get("data", {}) if isinstance(macro_state, dict) else {}

    permission = str(alert_data.get("permission", "BLOCK_TRADING")).upper()
    execution_enabled = bool(alert_data.get("execution_enabled", False))
    if execution_enabled:
        # The trader view is incapable of propagating execution authority.
        permission = "BLOCK_TRADING"
        execution_enabled = False

    fusion = decision_meta.get("technical_fusion", {})
    votes = fusion.get("trend_votes", {})
    bullish = int(votes.get("bullish", 0) or 0)
    bearish = int(votes.get("bearish", 0) or 0)
    total = bullish + bearish
    conflict_ratio = (min(bullish, bearish) / total) if total else 0.0
    if conflict_ratio >= 0.40:
        conflict = "HIGH"
    elif conflict_ratio >= 0.20:
        conflict = "MEDIUM"
    else:
        conflict = "LOW"

    return {
        "symbol": "XAUUSD",
        "decision": decision_data.get("decision", "NO_TRADE"),
        "permission": permission,
        "confidence": decision_data.get("confidence", 0),
        "risk": decision_data.get("risk", "EXTREME"),
        "macro_bias": macro_data.get("gold_bias", "NEUTRAL"),
        "news_risk": macro_data.get("news_risk", "HIGH"),
        "timeframes": fusion.get("usable_timeframes", []),
        "trend_votes": votes,
        "timeframe_conflict": conflict,
        "reasons": decision_data.get("reasons", []) + [alert_data.get("reason", "No safe permission available.")],
        "fresh": bool(alert_data.get("fresh", False)),
        "execution_enabled": execution_enabled,
        "mode": "READ_ONLY",
    }


def main():
    alert_state = read_state("alert.json")
    decision_state = read_state("decision.json")
    macro_state = read_state("agent03.json")
    view = build_trader_view(alert_state, decision_state, macro_state)
    status = "SUCCESS" if view["fresh"] and view["permission"] not in {"BLOCK_TRADING", "CAUTION"} else "DEGRADED"
    write_state(
        agent="TraderView",
        version="0.1",
        filename="trader_view.json",
        data=view,
        status=status,
        errors=[],
        metadata={"mode": "read-only", "execution_enabled": False, "source": "Agent06"},
    )
    print(
        f"XAUUSD | {view['decision']} | {view['permission']} | "
        f"Confidence {view['confidence']}% | Conflict {view['timeframe_conflict']} | Execution DISABLED"
    )


if __name__ == "__main__":
    main()
