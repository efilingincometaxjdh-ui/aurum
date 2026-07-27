"""
Configuration settings for Rahul AI Team Agent 01 - XAUUSD Macro Intelligence.

All values are architectural requirements for the agent's operation.
"""

# ============================================================
# ARTICLE COLLECTION SETTINGS
# ============================================================

ARTICLE_MAX_LENGTH = 10000
"""Maximum length of extracted article text in characters."""

MAX_ARTICLES_PER_REQUEST = 5
"""Maximum number of articles to fetch per agent run."""

ARTICLE_FETCH_TIMEOUT = 15
"""Timeout in seconds for individual article fetches."""

# ============================================================
# FEED ANALYSIS SETTINGS
# ============================================================

ITEMS_PER_FEED_ANALYSIS = 5
"""Maximum number of articles to include in Gemini analysis."""

MAX_AGE_DAYS = 7
"""Maximum age of articles to consider (in days)."""

# ============================================================
# GEMINI API SETTINGS
# ============================================================

GEMINI_MODEL = "gemini-1.5-flash"
"""Google Gemini model identifier."""

GEMINI_TEMPERATURE = 0.3
"""Gemini generation temperature (0.0 = deterministic, 1.0 = creative)."""

GEMINI_TIMEOUT = 30
"""Timeout in seconds for Gemini API requests."""

# ============================================================
# RISK ENGINE THRESHOLDS
# ============================================================

CONFIDENCE_THRESHOLD = 40
"""Minimum confidence level (0-100) for directional permissions."""

STRONG_SCORE_THRESHOLD = 50
"""Minimum absolute score magnitude for strong directional signals."""

# ============================================================
# STATE AND LEARNING PATHS
# ============================================================

STATE_FILE_PATH = "data/agent01_state.json"
"""Path where Agent 01 writes its JSON state output."""

PREDICTIONS_JSONL_PATH = "data/learning/predictions.jsonl"
"""Path to append-only JSONL file for prediction recording."""
