"""Provider contracts and the explicit runtime provider factory."""
from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class IMarketDataProvider(ABC):
    """Canonical read-only market-data provider contract."""

    @abstractmethod
    def fetch_candles(self, label: str, interval: str) -> List[Dict]:
        raise NotImplementedError


class TwelveDataProvider(IMarketDataProvider):
    """Legacy deterministic shim retained only for explicit test use."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("TWELVE_DATA_API_KEY")

    def fetch_candles(self, label: str, interval: str) -> List[Dict]:
        if not self.api_key:
            raise RuntimeError("TWELVE_DATA_API_KEY missing")
        raise NotImplementedError(
            "TwelveDataProvider is a test-only shim; the production runtime uses cTrader"
        )


def _import_ctrader():
    """Import cTrader lazily so deterministic tests remain offline."""
    try:
        from market.ctrader_provider import CTraderProvider
    except Exception as exc:
        raise RuntimeError(f"cTrader provider import failed: {exc}") from exc
    return CTraderProvider


def _oauth_access_token() -> Optional[str]:
    """Load/refresh an OAuth token when no static token is configured."""
    try:
        from auth.ctrader_oauth import CTraderOAuth, CTraderOAuthError
        return CTraderOAuth().get_valid_token().access_token
    except CTraderOAuthError:
        return None


def get_default_provider() -> IMarketDataProvider:
    """Return the explicitly configured production provider.

    cTrader is the only supported runtime market-data provider. Its access
    token may come from the OAuth token store when CTRADER_ACCESS_TOKEN is not
    set. The legacy Twelve Data shim remains explicit-test-only.
    """
    choice = os.environ.get("MARKET_PROVIDER", "").strip().lower()

    if choice in {"twelve_data", "twelvedata"}:
        return TwelveDataProvider()

    ctrader_requested = choice in {"", "ctrader"}
    if ctrader_requested:
        client_id = os.environ.get("CTRADER_CLIENT_ID")
        client_secret = os.environ.get("CTRADER_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise RuntimeError(
                "cTrader runtime configuration missing: set CTRADER_CLIENT_ID and CTRADER_CLIENT_SECRET"
            )

        access_token = os.environ.get("CTRADER_ACCESS_TOKEN") or _oauth_access_token()
        if not access_token:
            raise RuntimeError(
                "cTrader runtime authentication missing: provide CTRADER_ACCESS_TOKEN "
                "or complete the Aurum cTrader OAuth flow"
            )

        return _import_ctrader()(
            client_id=client_id,
            client_secret=client_secret,
            access_token=access_token,
        )

    raise RuntimeError(
        f"Unsupported MARKET_PROVIDER={choice!r}; use 'ctrader' for runtime or 'twelve_data' only for explicit tests"
    )
