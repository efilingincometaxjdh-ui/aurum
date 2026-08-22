# Aurum cTrader cBot Market Bridge

This integration is a **read-only market-data adapter**. It does not place, modify, or close orders.

The cBot runs inside an authenticated cTrader desktop terminal and sends completed candles to Aurum over HTTP. cTrader Algo supports HTTP requests with `AccessRights.None`, so the bridge does not need trading/file privileges for network access. See the official cTrader documentation: https://help.ctrader.com/ctrader-algo/guides/network-access/

## Architecture

```text
Authenticated cTrader desktop
        |
        | AurumMarketBridge cBot
        | POST completed candle
        v
Aurum receiver
        |
        +--> validation
        +--> data/current/ctrader_cbot_latest.json
        +--> data/current/ctrader_cbot_candles.jsonl
```

## First local test

1. Open `integrations/ctrader-cbot/AurumMarketBridge.cs` in cTrader Algo.
2. Build the cBot in cTrader.
3. Start the local receiver from the Aurum repository root:

```powershell
python integrations/ctrader-cbot/receiver.py
```

4. Confirm health:

```powershell
curl http://127.0.0.1:8000/api/market-data/ctrader-cbot/health
```

5. Attach `AurumMarketBridge` to a chart for a symbol you want to test.
6. Leave `Aurum Endpoint` at the local default for the first test.
7. Start the cBot.
8. Verify the cBot log reports an accepted candle and inspect the local `data/current/` files.

## Optional ingest token

Set the receiver token before starting it:

```powershell
$env:AURUM_CBOT_INGEST_TOKEN="a-long-local-test-token"
python integrations/ctrader-cbot/receiver.py
```

Then configure the same value in the cBot's `Ingest Token` parameter. Never commit the token.

## Contract

Each completed candle contains:

- `schemaVersion`: `1`
- `provider`: `ctrader_cbot`
- `symbol`
- `timeframe`
- `timestamp` (UTC)
- `open`, `high`, `low`, `close`
- `tickVolume`
- `digits`

The receiver rejects missing fields, non-finite prices, invalid OHLC relationships, invalid digits/volume, unsupported schema versions, and non-cBot providers.

## Scope

This first milestone intentionally does **not**:

- run Agent02;
- replace the existing cTrader Open API provider;
- create a production remote endpoint;
- create or modify trading orders;
- implement custom M9/M18 aggregation.

After the local transport is proven, the next step is to connect this validated contract to the existing market-data provider interface and add historical backfill/export.
