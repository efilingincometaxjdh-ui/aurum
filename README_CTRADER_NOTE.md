## Recent change: cTrader provider now requires pre-provisioned access token

- Objective: simplify runtime configuration by requiring CTRADER_ACCESS_TOKEN, CTRADER_CLIENT_ID and CTRADER_CLIENT_SECRET; remove the dependency on a token endpoint URL or explicit candles URL.

- Change: market/ctrader_provider.py now uses a pre-provisioned access token and constructs a default candles endpoint from CTRADER_API_BASE (defaults to https://api.ctrader.com). The provider no longer requires CTRADER_TOKEN_URL or CTRADER_CANDLES_URL.

- Test: updated tests to assert the provider requires CTRADER_ACCESS_TOKEN and related credentials for instantiation.
