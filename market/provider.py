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


def get_default_provider() -> IMarketDataProvider:
    """Return the explicitly configured production provider.

    cTrader is the only supported runtime market-data provider. The legacy
    Twelve Data shim is available only when ``MARKET_PROVIDER=twelve_data`` is
    explicitly requested by deterministic tests or migration tooling.
    """
    choice = os.environ.get("MARKET_PROVIDER", "").strip().lower()

    if choice in {"twelve_data", "twelvedata"}:
        return TwelveDataProvider()

    ctrader_requested = choice in {"", "ctrader"}
    if ctrader_requested:
        if not (
            os.environ.get("CTRADER_CLIENT_ID")
            and os.environ.get("CTRADER_CLIENT_SECRET")
            and os.environ.get("CTRADER_ACCESS_TOKEN")
        ):
            raise RuntimeError(
                "cTrader runtime configuration missing: set CTRADER_CLIENT_ID, "
                "CTRADER_CLIENT_SECRET and CTRADER_ACCESS_TOKEN"
            )
        return _import_ctrader()()

    raise RuntimeError(
        f"Unsupported MARKET_PROVIDER={choice!r}; use 'ctrader' for runtime or 'twelve_data' only for explicit tests"
    )
