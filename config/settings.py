# ============================================================
# RAHUL AI TEAM — AGENT 01 CONFIGURATION
# ============================================================

# Article Content Extraction
ARTICLE_MAX_LENGTH = 10000  # Max characters to extract per article
ARTICLE_FETCH_TIMEOUT = 10  # Timeout in seconds
MAX_ARTICLES_PER_REQUEST = 5  # Max full articles to send to Gemini

# RSS Feed Configuration
MAX_AGE_DAYS = 7  # Only use items published within this many days
ITEMS_PER_FEED_ANALYSIS = 20  # Max items to process per feed

# Gemini Configuration
GEMINI_MODEL = "gemini-3.5-flash"
GEMINI_TEMPERATURE = 0.1
GEMINI_TIMEOUT = 60

# Risk Engine Thresholds
CONFIDENCE_THRESHOLD = 40  # Minimum confidence to allow directional trades
STRONG_SCORE_THRESHOLD = 50  # Score magnitude required for ALLOW_BUYS/SELLS
MODERATE_SCORE_THRESHOLD = 30  # Score magnitude for supporting evidence

# News Risk Controls
NEWS_RISK_BLOCKS_TRADING = "EXTREME"  # Block trading if risk reaches this level
HIGH_RISK_TRIGGERS_CAUTION = "HIGH"  # Caution if news risk is high

# Output Paths
STATE_FILE_PATH = "data/latest_intelligence.json"
