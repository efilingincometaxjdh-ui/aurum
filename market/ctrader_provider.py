"""cTrader market data provider for Aurum

This provider implements an OAuth2 client-credentials flow to obtain an
access token and a small candles fetcher that calls a configurable
CTRADER_CANDLES_URL. The URL should be a format string containing
"{symbol}" and optionally "{granularity}" and "{count}".

Environment variables / required configuration:
- CTRADER_CLIENT_ID
- CTRADER_CLIENT_SECRET
- CTRADER_TOKEN_URL  # OAuth2 token endpoint
- CTRADER_API_BASE (optional) or CTRADER_CANDLES_URL (recommended)

Example CTRADER_CANDLES_URL:
  https://api.ctrader.com/v1/markets/{symbol}/candles?granularity={granularity}&count={count}

The provider purposefully validates inputs and raises RuntimeError when
credentials or essential endpoints are missing so CI/dev can detect
misconfiguration early. Network errors raise requests exceptions.
"""
from __future__ import annotations

import os
import time
import logging
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class CTraderProvider:
    """cTrader-compatible market data provider implementing the same
    interface expected by the rest of the codebase.

    Notes:
    - This implementation expects the caller to set CTRADER_TOKEN_URL and
      CTRADER_CANDLES_URL (or CTRADER_API_BASE + a default path). That keeps
      the code generic and avoids hardcoding a specific public endpoint which
      may vary between environments.
    - Tokens are cached in-memory for the lifetime of the process and
      refreshed when expired.
    """

    def __init__(self, *, client_id: Optional[str] = None, client_secret: Optional[str] = None,
                 token_url: Optional[str] = None, candles_url: Optional[str] = None, timeout: int = 10):
        self.client_id = client_id or os.environ.get("CTRADER_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("CTRADER_CLIENT_SECRET")
        self.token_url = token_url or os.environ.get("CTRADER_TOKEN_URL")
        self.candles_url = candles_url or os.environ.get("CTRADER_CANDLES_URL")
        self.timeout = int(os.environ.get("CTRADER_REQUEST_TIMEOUT", str(timeout)))

        if not (self.client_id and self.client_secret):
            raise RuntimeError("cTrader credentials missing (CTRADER_CLIENT_ID/CTRADER_CLIENT_SECRET)")

        if not self.token_url:
            raise RuntimeError("CTRADER_TOKEN_URL must be set to the OAuth2 token endpoint")

        if not self.candles_url:
            raise RuntimeError(
                "CTRADER_CANDLES_URL must be set (use a format string with {symbol} and optional {granularity}/{count})"
            )

        # token info
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

    def _fetch_token(self) -> str:
        """Fetch an access token using client_credentials grant.

        Expects the token endpoint to accept form-encoded body with
        grant_type=client_credentials, client_id and client_secret.
        """
        now = time.time()
        if self._access_token and now < self._token_expires_at - 30:
            return self._access_token

        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        resp = requests.post(self.token_url, data=data, timeout=self.timeout)
        resp.raise_for_status()
        payload = resp.json()

        access_token = payload.get("access_token")
        if not access_token:
            raise RuntimeError(f"Token response missing access_token: {payload}")

        expires_in = int(payload.get("expires_in", 3600))
        self._access_token = access_token
        self._token_expires_at = now + expires_in
        logger.debug("Obtained cTrader token; expires in %s seconds", expires_in)
        return self._access_token

    def _get_headers(self) -> Dict[str, str]:
        token = self._fetch_token()
        return {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    def fetch_candles(self, label: str, interval: str, count: int = 500) -> List[Dict]:
        """Fetch candles for the given symbol/interval.

        Parameters:
        - label: e.g. 'XAU/USD' (Agent02 passes SYMBOL)
        - interval: e.g. '5min', '15min', '1h', '4h'
        - count: number of candles to request (default 500)

        The CTRADER_CANDLES_URL environment variable must be a format string
        containing '{symbol}' and optionally '{granularity}' and '{count}'.
        """
        # Normalize symbol for URL usage (most APIs expect no slash or a dash)
        symbol = label.replace("/", "-").replace(" ", "")

        # Map our internal interval strings to a granularity value consumed by the
        # cTrader endpoint. By default we pass the raw interval string through as
        # 'granularity' — override mapping here if your API expects different values.
        granularity = interval

        url = self.candles_url.format(symbol=symbol, granularity=granularity, count=count)

        headers = self._get_headers()

        resp = requests.get(url, headers=headers, timeout=self.timeout)
        resp.raise_for_status()

        payload = resp.json()

        # Attempt common shapes: either a top-level list of candles or a dict with
        # a 'candles' key. Normalize into a list of candles.
        if isinstance(payload, dict) and "candles" in payload:
            candles_src = payload["candles"]
        elif isinstance(payload, list):
            candles_src = payload
        else:
            # Give a helpful error message to aid configuration debugging.
            raise ValueError(f"Unexpected candles response shape: {payload}")

        normalized = []
        for c in candles_src:
            # support common key names: time / datetime / timestamp
            time_key = None
            for k in ("time", "datetime", "timestamp"):
                if k in c:
                    time_key = k
                    break

            if time_key is None:
                raise ValueError(f"Candle missing time field: {c}")

            normalized.append({
                "open": float(c["open"]),
                "high": float(c["high"]),
                "low": float(c["low"]),
                "close": float(c["close"]),
                "datetime": str(c[time_key]),
            })

        # Ensure ascending by datetime — rely on provider but enforce here
        normalized.sort(key=lambda x: x["datetime"])
        return normalized
