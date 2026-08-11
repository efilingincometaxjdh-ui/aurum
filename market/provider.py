"""market/provider.py

Provider factory: prefer cTrader (runtime) when configured via CTRADER_ACCESS_TOKEN
or MARKET_PROVIDER=ctrader. TwelveDataProvider remains available as a fallback
for backwards compatibility and tests.
"""
from __future__ import annotations

import os
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class IMarketDataProvider(ABC):
    @abstractmethod
    def fetch_candles(self, label: str, interval: str) -> List[Dict]:
        raise NotImplementedError


class TwelveDataProvider(IMarketDataProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("TWELVE_DATA_API_KEY")

    def fetch_candles(self, label: str, interval: str) -> List[Dict]:
        if not self.api_key:
            raise RuntimeError("TWELVE_DATA_API_KEY missing")
        raise NotImplementedError(
            "TwelveDataProvider network client not implemented in this shim; "
            "inject a provider in tests or implement network logic for runtime use."
        )


# Lazy import helper
def _import_ctrader():
    try:
        from market.ctrader_provider import CTraderProvider

        return CTraderProvider
    except Exception as exc:
        logger.debug("cTrader provider import failed: %s", exc, exc_info=True)
        return None


def get_default_provider() -> IMarketDataProvider:
    provider_choice = os.environ.get("MARKET_PROVIDER", "").lower()
    # Explicit override
    if provider_choice == "ctrader":
        CTrader = _import_ctrader()
        if not CTrader:
            raise RuntimeError(
                "CTrader provider requested (MARKET_PROVIDER=ctrader) but the provider could not be imported. Ensure 'requests' is installed and provider is valid."
            )
        return CTrader()

    # Auto-detect by presence of a pre-provisioned access token (preferred)
    if os.environ.get("CTRADER_ACCESS_TOKEN"):
        CTrader = _import_ctrader()
        if CTrader:
            return CTrader()
        raise RuntimeError(
            "CTRADER_ACCESS_TOKEN present but cTrader provider failed to import. Ensure runtime dependencies are installed."
        )

    # Auto-detect by credentials (for environments that also provide access token)
    if os.environ.get("CTRADER_CLIENT_ID") and os.environ.get("CTRADER_CLIENT_SECRET") and os.environ.get("CTRADER_ACCESS_TOKEN"):
        CTrader = _import_ctrader()
        if CTrader:
            return CTrader()
        raise RuntimeError("CTRADER credentials present but cTrader provider failed to import")

    # Fallback
    return TwelveDataProvider()
