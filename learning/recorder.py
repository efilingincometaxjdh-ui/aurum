"""
RAHUL AI TEAM — PREDICTION RECORDER

Records Agent 01 predictions to data/learning/predictions.jsonl

DESIGN PRINCIPLES:

1. IMMUTABILITY
   - predictions.jsonl contains ONLY information known at prediction time
   - Once written, predictions are never modified
   - Future market outcomes go to outcomes.jsonl (joined by prediction_id)

2. NO FABRICATION
   - xauusd_price_at_prediction is reserved but remains null
   - Never fabricate market prices
   - Reliable price data source required before populating

3. SAFETY
   - Learning system never modifies source code, risk_engine.py, prompts
   - No autonomous rule changes; human approval required
   - Persists predictions for audit trail and future analysis
"""

import uuid
import json
from pathlib import Path
from datetime import datetime, timezone


# ============================================================
# PREDICTION SCHEMA
# ============================================================

PREDICTION_SCHEMA = {
    "prediction_id": "str (uuid-v4)",
    "generated_at_utc": "str (ISO 8601)",
    "generated_at_ist": "str (ISO 8601)",
    "symbol": "str (XAUUSD)",
    
    "gold_bias": "str (BULLISH|BEARISH|NEUTRAL)",
    "usd_bias": "str (BULLISH|BEARISH|NEUTRAL)",
    "gold_score": "int (-100 to +100)",
    "usd_score": "int (-100 to +100)",
    
    "news_risk": "str (LOW|MEDIUM|HIGH|EXTREME)",
    "confidence": "int (0-100)",
    "bot_action": "str (action from RiskEngine)",
    
    "summary": "str (Gemini reasoning)",
    "invalidation": "str (what would invalidate this assessment)",
    
    "sources_used": "list of source objects",
    
    "xauusd_price_at_prediction": "null (reserved for future use)"
}


# ============================================================
# OUTCOME SCHEMA (DESIGN — NOT YET POPULATED)
# ============================================================

OUTCOME_SCHEMA = {
    "prediction_id": "str (uuid-v4, FK to predictions.jsonl)",
    "evaluated_at_utc": "str (ISO 8601, when evaluation occurred)",
    
    # Market prices at various timeframes
    "price_at_prediction": "float or null",
    "price_1h": "float or null",
    "price_4h": "float or null",
    "price_24h": "float or null",
    
    # Returns (percentage change from price_at_prediction)
    "return_1h": "float or null",
    "return_4h": "float or null",
    "return_24h": "float or null",
    
    # Direction correctness (True if predicted bias matched actual direction)
    "direction_correct_1h": "bool or null",
    "direction_correct_4h": "bool or null",
    "direction_correct_24h": "bool or null",
}


# ============================================================
# PREDICTION RECORDER
# ============================================================

def record_prediction(state, prediction_id=None):
    """
    Record a single Agent 01 prediction to data/learning/predictions.jsonl
    
    IMMUTABLE: Once written, predictions are never modified.
    
    Args:
        state (dict): The state object from agent01.py Section 12.
                     Should contain: generated_at_utc, generated_at_ist,
                     symbol, gold_bias, usd_bias, gold_score, usd_score,
                     news_risk, confidence, bot_action, summary, invalidation,
                     sources_used
        
        prediction_id (str, optional): UUID for this prediction.
                                      Auto-generated if not provided.
    
    Returns:
        str: The prediction_id (UUID)
    
    Raises:
        IOError: If file cannot be written
        ValueError: If state is missing required fields
    """
    
    if prediction_id is None:
        prediction_id = str(uuid.uuid4())
    
    # Validate required fields
    required_fields = [
        "generated_at_utc", "generated_at_ist", "symbol",
        "gold_bias", "usd_bias", "gold_score", "usd_score",
        "news_risk", "confidence", "bot_action",
        "summary", "invalidation", "sources_used"
    ]
    
    missing_fields = [f for f in required_fields if f not in state]
    if missing_fields:
        raise ValueError(
            f"State missing required fields: {', '.join(missing_fields)}"
        )
    
    # Build immutable prediction record
    prediction_record = {
        "prediction_id": prediction_id,
        "generated_at_utc": state["generated_at_utc"],
        "generated_at_ist": state["generated_at_ist"],
        "symbol": state["symbol"],
        
        "gold_bias": state["gold_bias"],
        "usd_bias": state["usd_bias"],
        "gold_score": state["gold_score"],
        "usd_score": state["usd_score"],
        
        "news_risk": state["news_risk"],
        "confidence": state["confidence"],
        "bot_action": state["bot_action"],
        
        "summary": state["summary"],
        "invalidation": state["invalidation"],
        
        "sources_used": state["sources_used"],
        
        # Reserved for future use (market price module)
        "xauusd_price_at_prediction": None,
    }
    
    # Ensure data/learning directory exists
    predictions_file = Path("data/learning/predictions.jsonl")
    predictions_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Append as single line JSON (JSONL format)
    with open(predictions_file, "a") as f:
        f.write(json.dumps(prediction_record) + "\n")
    
    return prediction_id


def record_outcome(prediction_id, outcome_data):
    """
    FUTURE: Record market outcome for a prediction.
    
    NOT YET IMPLEMENTED. Awaits reliable XAUUSD market-data module.
    
    This function is reserved for future use. Do not populate outcomes
    until actual market price data is available and verified.
    
    Args:
        prediction_id (str): UUID of the prediction
        outcome_data (dict): Market price and return data
    
    Raises:
        NotImplementedError: Until market data module exists
    """
    raise NotImplementedError(
        "Outcome recording is not yet implemented. "
        "Awaits reliable XAUUSD market-data module."
    )
