"""cTrader market data provider for Aurum

This provider implements an access-token based cTrader client suitable for
runtimes where tokens are provisioned externally. The provider requires the
following environment values:

- CTRADER_CLIENT_ID
- CTRADER_CLIENT_SECRET
- CTRADER_ACCESS_TOKEN (pre-provisioned token)
- CTRADER_API_BASE (optional, defaults to https://api.ctrader.com)

The provider intentionally does not perform client_credentials token flow
by default; it uses the supplied access token for Authorization. This keeps
config simple and avoids depending on a token endpoint URL.
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

    Requirements:
    - CTRADER_CLIENT_ID
    - CTRADER_CLIENT_SECRET
    - CTRADER_ACCESS_TOKEN

    Optional:
    - CTRADER_API_BASE (defaults to https://api.ctrader.com)

    The provider uses the ACCESS_TOKEN for Authorization and constructs a
    default candles endpoint based on API_BASE. It does not require a token
    endpoint URL or explicit candles URL.
    """

    def __init__(
        self,
        *,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: int = 10,
    ):
        self.client_id = client_id or os.environ.get("CTRADER_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("CTRADER_CLIENT_SECRET")
        self._access_token = access_token or os.environ.get("CTRADER_ACCESS_TOKEN")
        self.api_base = api_base or os.environ.get("CTRADER_API_BASE") or "https://api.ctrader.com"
        self.timeout = int(os.environ.get("CTRADER_REQUEST_TIMEOUT", str(timeout)))

        if not (self.client_id and self.client_secret and self._access_token):
            raise RuntimeError(
                "cTrader configuration missing: CTRADER_CLIENT_ID, CTRADER_CLIENT_SECRET and CTRADER_ACCESS_TOKEN are required"
            )

        # Build default candles URL
        base = self.api_base.rstrip("/")
        self.candles_url = base + "/v1/markets/{symbol}/candles?granularity={granularity}&count={count}"

        # token info — we rely on pre-provisioned access token
        self._token_expires_at = time.time() + 24 * 3600

    def _get_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._access_token}", "Accept": "application/json"}

    def fetch_candles(self, label: str, interval: str, count: int = 500) -> List[Dict]:
        """Fetch candles for the given symbol/interval.

        Normalizes the API response into a list of dicts with keys: open, high,
        low, close, datetime (ISO-8601). The provider tolerates either a list
        payload or a dict with a 'candles' key.
        """
        symbol = label.replace("/", "-").replace(" ", "")
        granularity = interval

        url = self.candles_url.format(symbol=symbol, granularity=granularity, count=count)

        headers = self._get_headers()

        resp = requests.get(url, headers=headers, timeout=self.timeout)
        resp.raise_for_status()

        payload = resp.json()

        if isinstance(payload, dict) and "candles" in payload:
            candles_src = payload["candles"]
        elif isinstance(payload, list):
            candles_src = payload
        else:
            raise ValueError(f"Unexpected candles response shape: {payload}")

        normalized = []
        for c in candles_src:
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

        normalized.sort(key=lambda x: x["datetime"])
        return normalized
