import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

from config.settings import (
    ARTICLE_MAX_LENGTH,
    MAX_ARTICLES_PER_REQUEST,
    GEMINI_MODEL,
    GEMINI_TEMPERATURE,
    GEMINI_TIMEOUT,
    MAX_AGE_DAYS,
    ITEMS_PER_FEED_ANALYSIS,
    STATE_FILE_PATH,
)
from collectors.article_reader import extract_article_content
from intelligence.risk_engine import RiskEngine

# ============================================================
# RAHUL AI TEAM
# AGENT 01 — XAUUSD MACRO INTELLIGENCE
# VERSION 3.0
# ============================================================

API_KEY = os.environ["GEMINI_API_KEY"]

# ============================================================
# 1. LIVE INFORMATION SOURCES
# ============================================================

FEEDS = {
    "FED_MONETARY_POLICY":
        "https://www.federalreserve.gov/feeds/press_monetary.xml",

    "FED_SPEECHES":
        "https://www.federalreserve.gov/feeds/speeches.xml",

    "FED_PRESS_RELEASES":
        "https://www.federalreserve.gov/feeds/press_all.xml",
}

KEYWORDS = [
    "federal reserve",
    "fed",
    "fomc",
    "powell",
    "monetary policy",
    "interest rate",
    "rates",
    "inflation",
    "cpi",
    "ppi",
    "employment",
    "unemployment",
    "payroll",
    "jobs",
    "wages",
    "treasury",
    "yield",
    "economic",
    "economy",
    "dollar",
    "usd",
]


# ============================================================
# 2. RSS READER
# ============================================================

def clean_text(value):
    if value is None:
        return ""

    return " ".join(value.split())


def parse_date(value):
    if not value:
        return None

    try:
        dt = parsedate_to_datetime(value)

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(timezone.utc)

    except Exception:
        return None


def read_feed(source, url):
    items = []

    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 Rahul-AI-Team-XAUUSD-Agent/3.0"
            }
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)

        # Federal Reserve feeds use standard RSS <item> entries
        entries = root.findall(".//item")

        print(f"\n{source}: Found {len(entries)} RSS entries")

        now = datetime.now(timezone.utc)

        for entry in entries:

            title = clean_text(
                entry.findtext("title", default="")
            )

            description = clean_text(
                entry.findtext("description", default="")
            )

            pub_date = clean_text(
                entry.findtext("pubDate", default="")
            )

            link = clean_text(
                entry.findtext("link", default="")
            )

            # Parse RSS publication date
            published = None

            if pub_date:
                try:
                    published = parsedate_to_datetime(pub_date)

                    if published.tzinfo is None:
                        published = published.replace(
                            tzinfo=timezone.utc
                        )

                    published = published.astimezone(timezone.utc)

                except Exception as error:
                    print(
                        f"Date parse warning: {pub_date} | {error}"
                    )

            combined = (
                title + " " + description
            ).lower()

            # Keyword relevance
            relevant = any(
                keyword in combined
                for keyword in KEYWORDS
            )

            if not relevant:
                continue

            # Freshness check
            if published:
                age = now - published

                if age > timedelta(days=MAX_AGE_DAYS):
                    continue

            items.append({
                "source": source,
                "title": title,
                "description": description[:1200],
                "published": (
                    published.isoformat()
                    if published
                    else "UNKNOWN"
                ),
                "link": link,
                "article_text": ""  # Will populate in Section 4
            })

        print(
            f"{source}: Accepted {len(items)} relevant recent items"
        )

    except Exception as error:
        print(
            f"Warning: {source} unavailable: {error}"
        )

    return items


# ============================================================
# 3. COLLECT LIVE INFORMATION
# ============================================================

news = []

for source, feed_url in FEEDS.items():

    collected = read_feed(
        source,
        feed_url
    )

    news.extend(collected)


# Remove duplicate titles

unique_news = []
seen_titles = set()

for item in news:

    title_key = item["title"].lower().strip()

    if title_key and title_key not in seen_titles:

        seen_titles.add(title_key)
        unique_news.append(item)


news = unique_news

print(
    f"\nCollected {len(news)} "
    f"relevant recent macro items."
)


# ============================================================
# 4. FETCH ARTICLE CONTENT
# ============================================================

print("\nFetching article content from trusted sources...")

articles_fetched = 0
articles_with_content = 0

for idx, item in enumerate(news):
    if articles_fetched >= MAX_ARTICLES_PER_REQUEST:
        break
    
    if item["link"]:
        success, article_text = extract_article_content(item["link"])
        
        if success and article_text:
            item["article_text"] = article_text
            articles_fetched += 1
            articles_with_content += 1

print(
    f"Successfully fetched {articles_fetched} full articles "
    f"({articles_with_content} with substantial content)"
)


# ============================================================
# 5. BUILD MARKET INFORMATION
# ============================================================

if news:

    sections = []

    for item in news[:ITEMS_PER_FEED_ANALYSIS]:

        # Prefer article content if available, fall back to description
        details = item["article_text"] if item["article_text"] else item["description"]

        sections.append(
            f"""
SOURCE: {item['source']}
PUBLISHED: {item['published']}
TITLE: {item['title']}
DETAILS: {details}
"""
        )

    market_information = "\n".join(sections)

else:

    market_information = """
No sufficiently recent relevant Federal Reserve
macroeconomic information was collected.

Do not infer a directional trading bias from
missing information.
"""


# ============================================================
# 6. GEMINI INTELLIGENCE PROMPT
# ============================================================

prompt = f"""
You are Agent 01 of Rahul AI Team.

ROLE:
You are a macroeconomic intelligence analyst supporting
an automated XAUUSD trading system.

You do NOT decide whether trades are executed.
You do NOT have authority over trading permissions.

Your responsibility is to analyze CURRENT macroeconomic
information and return structured intelligence on:

1. Gold strength or weakness
2. US Dollar strength or weakness
3. Elevated event/news risk

IMPORTANT RULES:

- Use ONLY the information supplied below.
- Never invent economic numbers.
- Never assume CPI, NFP, Fed decisions or market prices.
- Old or ambiguous information must receive low weight.
- Speech announcements without substantive policy
  information must receive low weight.
- If evidence is weak, return NEUTRAL.
- High confidence requires multiple pieces of
  consistent evidence.
- Distinguish news risk from directional bias.
- A high-risk environment does NOT automatically mean
  bullish or bearish Gold.

GENERAL MACRO RELATIONSHIPS:

Hawkish Fed / higher-rate pressure / stronger USD:
usually negative for Gold.

Dovish Fed / lower-rate expectations / weaker USD:
usually supportive for Gold.

Higher inflation can support Gold, but persistent
inflation can also strengthen USD if it increases
expectations of tighter Federal Reserve policy.

Risk-off/geopolitical stress may support Gold,
but do not assume this unless evidence is supplied.

SCORING:

Gold Score:
-100 = extremely bearish Gold
0 = neutral
+100 = extremely bullish Gold

USD Score:
-100 = extremely bearish USD
0 = neutral
+100 = extremely bullish USD

Confidence:
0-100: How confident are you in this analysis?

News Risk:
LOW = routine updates, no event risk
MEDIUM = scheduled releases or minor Fed communications
HIGH = important economic data or policy announcements
EXTREME = FOMC decisions, major policy shifts, crisis events

LIVE INFORMATION:

{market_information}

Return ONLY valid JSON.

Required structure:

{{
  "gold_bias": "BULLISH|BEARISH|NEUTRAL",
  "usd_bias": "BULLISH|BEARISH|NEUTRAL",
  "gold_score": -100 to +100,
  "usd_score": -100 to +100,
  "news_risk": "LOW|MEDIUM|HIGH|EXTREME",
  "confidence": 0 to 100,
  "reason": "short explanation",
  "invalidation": "what would invalidate this assessment"
}}
"""


# ============================================================
# 7. CALL GEMINI
# ============================================================

url = (
    "https://generativelanguage.googleapis.com/"
    f"v1beta/models/{GEMINI_MODEL}:generateContent"
    f"?key={API_KEY}"
)

payload = {
    "contents": [
        {
            "parts": [
                {
                    "text": prompt
                }
            ]
        }
    ],
    "generationConfig": {
        "temperature": GEMINI_TEMPERATURE,
        "responseMimeType": "application/json"
    }
}

data = json.dumps(payload).encode("utf-8")

request = urllib.request.Request(
    url,
    data=data,
    headers={
        "Content-Type": "application/json"
    },
    method="POST"
)


# ============================================================
# 8. READ GEMINI RESPONSE
# ============================================================

try:

    with urllib.request.urlopen(
        request,
        timeout=GEMINI_TIMEOUT
    ) as response:

        result = json.loads(
            response.read().decode("utf-8")
        )

    text = (
        result["candidates"][0]
        ["content"]["parts"][0]["text"]
    )

    analysis = json.loads(text)

except Exception as error:

    print(
        "\nAgent 01 Gemini analysis failed:"
    )

    print(error)

    raise


# ============================================================
# 9. VALIDATE GEMINI OUTPUT
# ============================================================

def safe_score(value):

    try:
        value = int(value)

    except Exception:
        return 0

    return max(-100, min(100, value))


def safe_confidence(value):

    try:
        value = int(value)

    except Exception:
        return 0

    return max(0, min(100, value))


gold_bias = analysis.get(
    "gold_bias",
    "NEUTRAL"
).upper()

usd_bias = analysis.get(
    "usd_bias",
    "NEUTRAL"
).upper()

gold_score = safe_score(
    analysis.get("gold_score", 0)
)

usd_score = safe_score(
    analysis.get("usd_score", 0)
)

news_risk = analysis.get(
    "news_risk",
    "HIGH"
).upper()

confidence = safe_confidence(
    analysis.get("confidence", 0)
)

reason = analysis.get(
    "reason",
    "No explanation provided."
)

invalidation = analysis.get(
    "invalidation",
    "No invalidation provided."
)


# Safety validation

VALID_BIASES = {
    "BULLISH",
    "BEARISH",
    "NEUTRAL"
}

VALID_RISK = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "EXTREME"
}


if gold_bias not in VALID_BIASES:
    gold_bias = "NEUTRAL"

if usd_bias not in VALID_BIASES:
    usd_bias = "NEUTRAL"

if news_risk not in VALID_RISK:
    news_risk = "HIGH"


# ============================================================
# 10. SET MAJOR EVENT (DETERMINISTIC, NOT FROM GEMINI)
# ============================================================

# major_event_detected is set deterministically in Python.
# In future versions, this will come from Economic Calendar module.
# For now, always False.

major_event_detected = False


# ============================================================
# 11. DETERMINISTIC RISK ENGINE — FINAL BOT ACTION
# ============================================================

engine = RiskEngine({
    "gold_bias": gold_bias,
    "usd_bias": usd_bias,
    "gold_score": gold_score,
    "usd_score": usd_score,
    "news_risk": news_risk,
    "confidence": confidence,
    "major_event_detected": major_event_detected,
})

bot_action, engine_rationale = engine.evaluate()


# ============================================================
# 12. GENERATE JSON STATE FILE
# ============================================================

# Create timestamps
now_utc = datetime.now(timezone.utc)
ist_offset = timedelta(hours=5, minutes=30)
now_ist = now_utc + ist_offset

# Build state object
state = {
    "generated_at_utc": now_utc.isoformat() + "Z",
    "generated_at_ist": now_ist.isoformat() + "Z",
    "agent": "agent01",
    "version": "3.0",
    "symbol": "XAUUSD",

    "gold_bias": gold_bias,
    "usd_bias": usd_bias,

    "gold_score": gold_score,
    "usd_score": usd_score,

    "news_risk": news_risk,
    "confidence": confidence,
    "major_event_detected": major_event_detected,

    "bot_action": bot_action,

    "summary": reason,
    "invalidation": invalidation,

    "sources_used": [
        {
            "source": item["source"],
            "title": item["title"],
            "published": item["published"],
            "link": item["link"],
            "has_article_content": bool(item["article_text"])
        }
        for item in news[:ITEMS_PER_FEED_ANALYSIS]
    ]
}

# Create data directory if needed
os.makedirs(os.path.dirname(STATE_FILE_PATH) or ".", exist_ok=True)

# Write state file
with open(STATE_FILE_PATH, "w") as f:
    json.dump(state, f, indent=2)

print(f"\n✅ State file written to {STATE_FILE_PATH}")


# ============================================================
# 13. DISPLAY AGENT 01 INTELLIGENCE
# ============================================================

print("\n")
print("🤖 RAHUL AI TEAM")
print("=" * 65)

print(
    "AGENT 01 — XAUUSD MACRO INTELLIGENCE v3.0"
)

print("=" * 65)

print()

print("📊 DATA COLLECTION:")
print(f"   Sources checked:      {len(FEEDS)}")
print(f"   Items collected:      {len(news)}")
print(f"   Articles fetched:     {articles_fetched}/{MAX_ARTICLES_PER_REQUEST}")
print(f"   Articles with content: {articles_with_content}")

print()

print("🔍 MACRO SIGNALS:")
print(f"   🥇 Gold Bias:         {gold_bias}")
print(f"   💵 USD Bias:          {usd_bias}")
print(f"   📊 Gold Score:        {gold_score:+d}/100")
print(f"   📊 USD Score:         {usd_score:+d}/100")

print()

print("⚠️  RISK ASSESSMENT:")
print(f"   News Risk:            {news_risk}")
print(f"   Major Event:          {'YES' if major_event_detected else 'NO'}")
print(f"   Confidence:           {confidence}%")

print()

print("=" * 65)
print(f"🤖 BOT ACTION: {bot_action}")
print("=" * 65)

print()

print("Risk Engine Rationale:")
print(engine_rationale)

print()

print("Gemini Analysis:")
print(reason)

print()

print("Invalidation:")
print(invalidation)

print()

print(f"Generated UTC:  {now_utc.isoformat()}Z")
print(f"Generated IST:  {now_ist.isoformat()}Z")

print()

print("=" * 65)

print("Agent 01 macro analysis complete.")

print("=" * 65)
