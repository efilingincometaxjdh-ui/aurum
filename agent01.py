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

{market_information}

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
    "models/gemini-2.5-flash:generateContent"
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
