import os
import json
import urllib.request
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


# =========================================================
# RAHUL AI TEAM
# AGENT 01 — XAUUSD INTELLIGENCE
# =========================================================

API_KEY = os.environ["GEMINI_API_KEY"]


# =========================================================
# 1. LIVE INFORMATION SOURCES
# =========================================================

FEEDS = {
    "FED_MONETARY_POLICY":
        "https://www.federalreserve.gov/feeds/press_monetary.xml",

    "FED_SPEECHES":
        "https://www.federalreserve.gov/feeds/speeches.xml",

    "BLS_LATEST":
        "https://www.bls.gov/feed/bls_latest.rss",
}


KEYWORDS = [
    "federal reserve",
    "fomc",
    "monetary policy",
    "interest rate",
    "rates",
    "inflation",
    "consumer price",
    "cpi",
    "producer price",
    "ppi",
    "employment",
    "unemployment",
    "payroll",
    "jobs",
    "wages",
    "jolts",
]


# =========================================================
# 2. READ + FILTER FEEDS
# =========================================================

def read_feed(source, url):

    try:

        request = Request(
            url,
            headers={
                "User-Agent":
                    "Mozilla/5.0 Rahul-AI-Team/1.0"
            },
        )

        with urlopen(request, timeout=15) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)

        items = []

        # RSS feeds
        for item in root.findall(".//item"):

            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            date = item.findtext("pubDate", "").strip()

            if any(
                keyword in title.lower()
                for keyword in KEYWORDS
            ):
                items.append({
                    "source": source,
                    "title": title,
                    "date": date,
                    "url": link,
                })


        # Atom feeds
        ns = {
            "atom":
                "http://www.w3.org/2005/Atom"
        }

        for entry in root.findall(
            ".//atom:entry", ns
        ):

            title = entry.findtext(
                "atom:title", "", ns
            ).strip()

            date = entry.findtext(
                "atom:updated", "", ns
            ).strip()

            link_element = entry.find(
                "atom:link", ns
            )

            link = ""

            if link_element is not None:
                link = link_element.attrib.get(
                    "href", ""
                )

            if any(
                keyword in title.lower()
                for keyword in KEYWORDS
            ):
                items.append({
                    "source": source,
                    "title": title,
                    "date": date,
                    "url": link,
                })

        return items[:10]


    except Exception as error:

        print(
            f"Warning: {source} unavailable: "
            f"{error}"
        )

        return []


# =========================================================
# 3. COLLECT INFORMATION
# =========================================================

news = []

for source, feed_url in FEEDS.items():

    collected_items = read_feed(
        source,
        feed_url
    )

    news.extend(collected_items)


print(
    f"\nCollected {len(news)} "
    f"relevant macro items."
)


# =========================================================
# 4. BUILD MARKET INFORMATION
# =========================================================

if not news:

    market_information = """
No relevant current macroeconomic headlines
were successfully collected.

There is insufficient evidence to establish
a directional macro bias.

Do not invent missing market information.
"""

else:

    market_information = "\n\n".join(

        f"""
SOURCE: {item['source']}
DATE: {item['date']}
HEADLINE: {item['title']}
URL: {item['url']}
"""

        for item in news[:20]
    )


# =========================================================
# 5. GEMINI ANALYST
# =========================================================

prompt = f"""
You are Agent 01 of Rahul AI Team.

You are an XAUUSD macro intelligence analyst.

Your job is to assess ONLY the information
provided below and determine its potential
implications for Gold versus the US Dollar.

IMPORTANT RULES:

1. Do not invent economic data.
2. Do not invent current market prices.
3. Do not assume that an old headline
   describes current market conditions.
4. If evidence is insufficient or conflicting,
   return NEUTRAL.
5. A headline merely mentioning inflation,
   employment or the Federal Reserve does not
   automatically imply a directional bias.
6. Do not recommend BUY or SELL.
7. Separate USD implications from Gold
   implications.
8. Be conservative with confidence.

MARKET INFORMATION:

{market_information}

Return ONLY valid JSON using exactly
this structure:

{{
  "gold_bias": "BULLISH, BEARISH or NEUTRAL",
  "usd_bias": "BULLISH, BEARISH or NEUTRAL",
  "gold_score": 0,
  "usd_score": 0,
  "news_risk": "LOW, MEDIUM or HIGH",
  "confidence": 0,
  "reason": "short evidence-based explanation",
  "invalidation": "what evidence could change the assessment"
}}

gold_score and usd_score must be integers
between -100 and 100.

confidence must be an integer between
0 and 100.
"""


# =========================================================
# 6. CALL GEMINI
# =========================================================

url = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/"
    "gemini-flash-latest:generateContent"
    f"?key={API_KEY}"
)


data = {

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
        "responseMimeType":
            "application/json"
    }
}


request = urllib.request.Request(

    url,

    data=json.dumps(data).encode(
        "utf-8"
    ),

    headers={
        "Content-Type":
            "application/json"
    },
)


with urllib.request.urlopen(
    request,
    timeout=30
) as response:

    result = json.loads(
        response.read().decode("utf-8")
    )


text = (
    result["candidates"][0]
    ["content"]["parts"][0]["text"]
)


analysis = json.loads(text)


# =========================================================
# 7. DISPLAY REPORT
# =========================================================

print("\n🤖 RAHUL AI TEAM")

print("=" * 45)

print(
    "AGENT 01 — XAUUSD INTELLIGENCE"
)

print("=" * 45)


print(
    f"\n🥇 Gold Bias:    "
    f"{analysis['gold_bias']}"
)

print(
    f"💵 USD Bias:     "
    f"{analysis['usd_bias']}"
)

print(
    f"📊 Gold Score:   "
    f"{analysis['gold_score']}/100"
)

print(
    f"📊 USD Score:    "
    f"{analysis['usd_score']}/100"
)

print(
    f"⚠️ News Risk:    "
    f"{analysis['news_risk']}"
)

print(
    f"🧠 Confidence:   "
    f"{analysis['confidence']}%"
)


print(
    f"\nReason:\n"
    f"{analysis['reason']}"
)

print(
    f"\nInvalidation:\n"
    f"{analysis['invalidation']}"
)


print("\n" + "=" * 45)

print(
    "Agent 01 analysis complete."
)
