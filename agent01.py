import os
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

# ============================================================
# RAHUL AI TEAM
# AGENT 01 — XAUUSD MACRO INTELLIGENCE
# VERSION 2.0
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

# Only recent information should influence trading intelligence
MAX_AGE_DAYS = 7

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
                "User-Agent": "Mozilla/5.0 Rahul-AI-Team-XAUUSD-Agent/2.0"
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
                "link": link
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
# 4. BUILD MARKET INFORMATION
# ============================================================

if news:

    sections = []

    for item in news[:20]:

        sections.append(
            f"""
SOURCE: {item['source']}
PUBLISHED: {item['published']}
TITLE: {item['title']}
DETAILS: {item['description']}
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
# 5. GEMINI INTELLIGENCE PROMPT
# ============================================================

prompt = f"""
You are Agent 01 of Rahul AI Team.

ROLE:
You are a macroeconomic intelligence agent supporting
an automated XAUUSD trading system.

You do NOT execute trades.

Your responsibility is to determine whether CURRENT
macroeconomic information supports:

1. Gold strength or weakness
2. US Dollar strength or weakness
3. Elevated event/news risk
4. Whether automated XAUUSD trading should be allowed

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

BOT ACTION:

Return exactly ONE of:

ALLOW_BUYS
ALLOW_SELLS
ALLOW_BOTH
CAUTION
BLOCK_TRADING

Use BLOCK_TRADING when major uncertainty/event risk
makes automated entry dangerous.

Use CAUTION when information is insufficient or
conflicting.

Use ALLOW_BUYS only when evidence meaningfully
supports Gold strength.

Use ALLOW_SELLS only when evidence meaningfully
supports Gold weakness.

Use ALLOW_BOTH only when macro conditions are
relatively stable and there is no meaningful
directional restriction.

LIVE INFORMATION:

{market_information}

Return ONLY valid JSON.

Required structure:

{{
  "gold_bias": "BULLISH|BEARISH|NEUTRAL",
  "usd_bias": "BULLISH|BEARISH|NEUTRAL",
  "gold_score": 0,
  "usd_score": 0,
  "news_risk": "LOW|MEDIUM|HIGH|EXTREME",
  "confidence": 0,
  "bot_action": "ALLOW_BUYS|ALLOW_SELLS|ALLOW_BOTH|CAUTION|BLOCK_TRADING",
  "reason": "short explanation",
  "invalidation": "what would invalidate this assessment"
}}
"""


# ============================================================
# 6. CALL GEMINI
# ============================================================

MODEL = "gemini-3.5-flash"

url = (
    "https://generativelanguage.googleapis.com/"
    f"v1beta/models/{MODEL}:generateContent"
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
        "temperature": 0.1,
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
# 7. READ GEMINI RESPONSE
# ============================================================

try:

    with urllib.request.urlopen(
        request,
        timeout=60
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
# 8. VALIDATE OUTPUT
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

bot_action = analysis.get(
    "bot_action",
    "CAUTION"
).upper()

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

VALID_ACTIONS = {
    "ALLOW_BUYS",
    "ALLOW_SELLS",
    "ALLOW_BOTH",
    "CAUTION",
    "BLOCK_TRADING"
}


if gold_bias not in VALID_BIASES:
    gold_bias = "NEUTRAL"

if usd_bias not in VALID_BIASES:
    usd_bias = "NEUTRAL"

if news_risk not in VALID_RISK:
    news_risk = "HIGH"

if bot_action not in VALID_ACTIONS:
    bot_action = "CAUTION"


# ============================================================
# 9. DISPLAY AGENT 01 INTELLIGENCE
# ============================================================

print("\n")
print("🤖 RAHUL AI TEAM")
print("=" * 55)

print(
    "AGENT 01 — XAUUSD MACRO INTELLIGENCE v2"
)

print("=" * 55)

print()

print(
    f"🥇 Gold Bias:      {gold_bias}"
)

print(
    f"💵 USD Bias:       {usd_bias}"
)

print(
    f"📊 Gold Score:     {gold_score:+d}/100"
)

print(
    f"📊 USD Score:      {usd_score:+d}/100"
)

print(
    f"⚠️ News Risk:      {news_risk}"
)

print(
    f"🧠 Confidence:     {confidence}%"
)

print()

print(
    f"🤖 BOT ACTION:     {bot_action}"
)

print()

print("Reason:")
print(reason)

print()

print("Invalidation:")
print(invalidation)

print()

print("=" * 55)

print(
    "Agent 01 live macro analysis complete."
)
