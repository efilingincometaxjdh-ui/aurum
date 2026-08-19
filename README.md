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
```

Authentication can be supplied either by `CTRADER_ACCESS_TOKEN` or by the server-side Aurum cTrader OAuth token store.

Optional:

```text
CTRADER_ACCESS_TOKEN
CTRADER_TOKEN_FILE
CTRADER_REDIRECT_URI
CTRADER_ACCOUNT_ID   # pin a specific authorized account; always verified against token grants
CTRADER_ENV          # demo (default) or live
CTRADER_SYMBOL       # XAU/USD (default)
CTRADER_REQUEST_COUNT
CTRADER_OAUTH_SCOPE  # accounts (default) or trading
```

### cTrader OAuth

Aurum now includes a server-side OAuth 2.0 implementation in `auth/ctrader_oauth.py` and a minimal callback service in `auth/ctrader_oauth_server.py`.

Start the callback service in a real HTTPS web runtime:

```bash
CTRADER_CLIENT_ID=... \
CTRADER_CLIENT_SECRET=... \
CTRADER_REDIRECT_URI=https://your-host/auth/ctrader/callback \
python -m auth.ctrader_oauth_server
```

Then open:

```text
https://your-host/auth/ctrader/connect
```

The callback exchanges the authorization code and stores the access/refresh tokens server-side. The token file is ignored by Git and must never be committed. Production multi-instance deployments should replace the file store with a durable encrypted secret store.

The provider factory uses a valid OAuth token automatically when `CTRADER_ACCESS_TOKEN` is not present. A configured `CTRADER_ACCOUNT_ID` is treated only as an account selector and is rejected unless it appears in `ProtoOAGetAccountListByAccessTokenRes` for the current token.

Use the **demo** environment for validation first. cTrader Open API separates demo and live endpoints. Historical bars are requested through the Open API trendbar messages and the Python SDK is maintained by Spotware.

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
