import os
import json
import urllib.request

API_KEY = os.environ["GEMINI_API_KEY"]

# For our first test we provide the information manually.
# Next version will collect live information automatically.
market_information = """
US inflation remains an important concern for markets.
Traders are monitoring Federal Reserve interest-rate expectations.
Gold traders are watching US dollar strength, Treasury yields,
geopolitical developments and upcoming US economic data.
"""

prompt = f"""
You are Agent 01 of Rahul AI Team.

Your job is to analyze macroeconomic information ONLY for its
potential effect on XAUUSD (Gold vs US Dollar).

Analyze the information below:

from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

FEEDS = {
    "FED": "https://www.federalreserve.gov/feeds/press_monetary.xml",
    "FED_SPEECHES": "https://www.federalreserve.gov/feeds/speeches.xml",
    "BLS_LATEST": "https://www.bls.gov/feed/bls_latest.rss",
}

KEYWORDS = [
    "federal reserve", "fomc", "monetary policy",
    "interest rate", "inflation", "consumer price",
    "cpi", "producer price", "ppi",
    "employment", "unemployment", "payroll",
    "jobs", "wages", "jolts"
]

def read_feed(source, url):
    try:
        req = Request(
            url,
            headers={"User-Agent": "Rahul-AI-Team/1.0"}
        )

        with urlopen(req, timeout=15) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)
        items = []

        # RSS
        for item in root.findall(".//item"):
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            date = item.findtext("pubDate", "").strip()

            if any(k in title.lower() for k in KEYWORDS):
                items.append({
                    "source": source,
                    "title": title,
                    "date": date,
                    "url": link
                })

        # Atom feeds
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        for entry in root.findall(".//atom:entry", ns):
            title = entry.findtext("atom:title", "", ns).strip()
            date = entry.findtext("atom:updated", "", ns).strip()

            link_element = entry.find("atom:link", ns)
            link = (
                link_element.attrib.get("href", "")
                if link_element is not None else ""
            )

            if any(k in title.lower() for k in KEYWORDS):
                items.append({
                    "source": source,
                    "title": title,
                    "date": date,
                    "url": link
                })

        return items[:10]

    except Exception as e:
        print(f"Warning: {source} unavailable: {e}")
        return []


news = []

for source, feed_url in FEEDS.items():
    news.extend(read_feed(source, feed_url))


if not news:
    market_information = """
No relevant current macroeconomic headlines were collected.
Do not infer a directional XAUUSD bias.
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

print(f"Collected {len(news)} relevant macro items.")

Return ONLY valid JSON in exactly this structure:

{{
  "gold_bias": "BULLISH, BEARISH or NEUTRAL",
  "usd_bias": "BULLISH, BEARISH or NEUTRAL",
  "gold_score": "integer from -100 to 100",
  "usd_score": "integer from -100 to 100",
  "news_risk": "LOW, MEDIUM or HIGH",
  "confidence": "integer from 0 to 100",
  "reason": "short explanation",
  "invalidation": "what could change this assessment"
}}

Do not recommend buying or selling.
Do not invent economic events that are not in the supplied information.
"""

url = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-flash-latest:generateContent"
    f"?key={API_KEY}"
)

data = {
    "contents": [{
        "parts": [{"text": prompt}]
    }],
    "generationConfig": {
        "responseMimeType": "application/json"
    }
}

request = urllib.request.Request(
    url,
    data=json.dumps(data).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

with urllib.request.urlopen(request) as response:
    result = json.loads(response.read().decode("utf-8"))

text = result["candidates"][0]["content"]["parts"][0]["text"]
analysis = json.loads(text)

print("\n🤖 RAHUL AI TEAM")
print("=" * 45)
print("AGENT 01 — XAUUSD INTELLIGENCE")
print("=" * 45)

print(f"\n🥇 Gold Bias:    {analysis['gold_bias']}")
print(f"💵 USD Bias:     {analysis['usd_bias']}")
print(f"📊 Gold Score:   {analysis['gold_score']}/100")
print(f"📊 USD Score:    {analysis['usd_score']}/100")
print(f"⚠️ News Risk:    {analysis['news_risk']}")
print(f"🧠 Confidence:   {analysis['confidence']}%")

print(f"\nReason:\n{analysis['reason']}")
print(f"\nInvalidation:\n{analysis['invalidation']}")

print("\n" + "=" * 45)
print("Agent 01 analysis complete.")
