# Rahul AI Team

Rahul AI Team is modular XAUUSD intelligence infrastructure built around deterministic, fail-closed contracts. It is **not an autonomous trading system**.

## Deterministic V1 architecture

```text
Agent 02 — Technical Intelligence ─┐
                                  ├→ Agent 04 — Decision Engine
Agent 03 — Macro/News Intelligence┘
                                         ↓
                              Agent 05 — Permission Engine
                                         ↓
                              Agent 06 — Alert Gateway
                                  (read-only / no execution)
```

Agent 01 is intentionally isolated from V1 because its legacy macro/bot-action path overlaps Agent 03 and conflicts with the intelligence → decision → permission separation.

## Agent 02 — XAUUSD Technical Intelligence

Agent 02 uses the **official Spotware cTrader Open API Python SDK** for runtime market data. It discovers the authorized trading account from the provisioned access token, resolves the broker-specific XAU/USD symbol, and requests M5, M15, H1 and H4 historical trendbars. The normalized output is written to `data/current/agent02.json`.

Required runtime environment:

```text
CTRADER_CLIENT_ID
CTRADER_CLIENT_SECRET
CTRADER_ACCESS_TOKEN
```

Optional:

```text
CTRADER_ACCOUNT_ID   # pin a specific authorized account
CTRADER_ENV          # demo (default) or live
CTRADER_SYMBOL       # XAU/USD (default)
CTRADER_REQUEST_COUNT
```

Use the **demo** environment for validation first. cTrader Open API separates demo and live endpoints, and historical bars are requested with `ProtoOAGetTrendbarsReq`; the Python SDK is maintained by Spotware. citeturn683079search3turn969868search0turn969868search3

## Agent 03 — XAUUSD Macro/News Intelligence

Uses official Federal Reserve RSS sources and deterministic gold-impact headline scoring. RSS risk is `LOW`, `MEDIUM`, or `HIGH`; `EXTREME` remains reserved for validated event-calendar evidence.

## Agents 04–06 and safety

Agent 04 performs deterministic multi-timeframe fusion. Agent 05 remains the final permission authority. Agent 06 is read-only and always exposes `execution_enabled: false`.

Missing, malformed, failed, stale or future-dated upstream state can only reduce authority. No broker order placement or trade modification belongs in this V1 runtime.

## Run locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Run Agent 02 with cTrader credentials present:

```bash
python agent02.py
```

## Tests

```bash
python -m unittest discover -s tests -v
```

GitHub Actions runs the deterministic suite on pushes and pull requests. A separate manual **cTrader integration smoke test** validates credential presence and performs a real read-only Agent 02 market-data fetch against the demo environment.

## Phase 2 direction

The immediate Phase 2 objective is real observation evidence: authenticated cTrader data → normalized Agent 02 state → repeated observation/outcome collection → empirical freshness/timing evidence. Analytics and ML must remain downstream of trustworthy evidence and must never increase trading authority.
