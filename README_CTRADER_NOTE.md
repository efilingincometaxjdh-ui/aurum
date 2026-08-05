<!-- README additions for cTrader -->

## cTrader integration

This repository supports using a market data provider for Agent02 via a
configurable provider. To use cTrader as the source of candles, set the
following environment variables (or add them as CI secrets):

- CTRADER_CLIENT_ID — your client id
- CTRADER_CLIENT_SECRET — your client secret
- CTRADER_TOKEN_URL — OAuth2 token endpoint for cTrader (client_credentials)
- CTRADER_CANDLES_URL — a URL format string for candle requests, for example:
  `https://api.ctrader.com/v1/markets/{symbol}/candles?granularity={granularity}&count={count}`

You can also set MARKET_PROVIDER=ctrader to force selection of the cTrader
provider. The provider uses the CTRADER_CANDLES_URL template and expects the
returned JSON to either be a list of candle objects or a dict with a
`candles` key.
