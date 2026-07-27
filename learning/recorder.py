"""
Prediction recording for Agent 01 learning archive.

Records each prediction as immutable JSONL for later outcome analysis.
Does NOT evaluate outcomes or modify thresholds.
"""

import os
import json
import uuid
from datetime import datetime, timezone
from config.settings import PREDICTIONS_JSONL_PATH


def record_prediction(state, prediction_id=None):
    """
    Record a prediction to the append-only learning archive.
    
    Each prediction is recorded as one line (JSONL format) with:
    - Metadata (when, which prediction, which agent/version)
    - Input signals (macro analysis from Gemini)
    - Risk engine decision (bot action)
    - Summary and invalidation notes
    - Data sources used
    
    Predicted XAUUSD price is currently null (no market data API yet).
    
    Args:
        state: Dictionary from Agent 01 containing prediction results.
               Expected keys: generated_at_utc, agent, version, symbol,
                             gold_bias, usd_bias, gold_score, usd_score,
                             news_risk, confidence, bot_action, summary,
                             invalidation, sources_used.
        
        prediction_id: Optional UUID string. If None, generates UUID v4.
    
    Returns:
        prediction_id (string): UUID of this prediction record.
    
    Raises:
        ValueError: If required fields are missing from state.
        OSError: If directory creation or file write fails.
    """
    
    # Generate or validate prediction ID
    if prediction_id is None:
        prediction_id = str(uuid.uuid4())
    else:
        # Validate it's a valid UUID string
        try:
            uuid.UUID(prediction_id)
        except (ValueError, AttributeError):
            raise ValueError(
                f"Invalid prediction_id: must be valid UUID string, got {prediction_id}"
            )
    
    # Validate required fields
    required_fields = {
        "generated_at_utc",
        "agent",
        "version",
        "symbol",
        "gold_bias",
        "usd_bias",
        "gold_score",
        "usd_score",
        "news_risk",
        "confidence",
        "bot_action",
        "summary",
        "invalidation",
        "sources_used",
    }
    
    missing = required_fields - set(state.keys())
    if missing:
        raise ValueError(
            f"state missing required fields: {missing}"
        )
    
    # Build prediction record
    record = {
        "prediction_id": prediction_id,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat() + "Z",
        
        # Metadata
        "agent": state["agent"],
        "version": state["version"],
        "symbol": state["symbol"],
        "generated_at_utc": state["generated_at_utc"],
        "generated_at_ist": state.get("generated_at_ist", None),
        
        # Macro signals (input)
        "gold_bias": state["gold_bias"],
        "usd_bias": state["usd_bias"],
        "gold_score": state["gold_score"],
        "usd_score": state["usd_score"],
        
        # Risk assessment
        "news_risk": state["news_risk"],
        "confidence": state["confidence"],
        "major_event_detected": state.get("major_event_detected", False),
        
        # Bot action (output)
        "bot_action": state["bot_action"],
        
        # Analysis
        "summary": state["summary"],
        "invalidation": state["invalidation"],
        
        # Data sources
        "sources_used": state["sources_used"],
        
        # Market data (currently unavailable)
        "xauusd_price_at_prediction": None,
        
        # Outcome (filled later in post-analysis)
        "outcome": None,
        "outcome_recorded_at_utc": None,
    }
    
    # Ensure directory exists
    directory = os.path.dirname(PREDICTIONS_JSONL_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    
    # Append to JSONL file (one record per line)
    with open(PREDICTIONS_JSONL_PATH, "a", encoding="utf-8") as f:
        json.dump(record, f, separators=(",", ":"))
        f.write("\n")
    
    return prediction_id
