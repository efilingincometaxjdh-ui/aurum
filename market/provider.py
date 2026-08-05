"""market/provider.py

Keep the original TwelveDataProvider for backward compatibility and add a
factory to return the default provider — which will choose cTrader when
configured via environment variables or MARKET_PROVIDER=ctrader.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class IMarketDataProvider(ABC):
    """Abstract market data provider interface.

    Implementations must return a list of candle dictionaries sorted ascending
    by datetime. Each candle must contain at least the keys: open, high, low,
    close and datetime (ISO-8601 timezone-aware string).
    """

    @abstractmethod
    def fetch_candles(self, label: str, interval: str) -> List[Dict]:
        raise NotImplementedError


class TwelveDataProvider(IMarketDataProvider):
    """Minimal Twelve Data provider shim.

    - When no API key is available via constructor or TWELVE_DATA_API_KEY env var,
      the provider raises RuntimeError to preserve existing agent02 behavior.
    - If an API key is provided, a real network implementation would be called.
      For safety in unit tests and CI this method raises NotImplementedError when
      an API key is present because network calls are out of scope for unit
      tests. Tests should inject a FakeProvider implementing
      IMarketDataProvider instead.

    This design keeps Agent02 unchanged while enabling deterministic testing via
    dependency injection.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("TWELVE_DATA_API_KEY")

    def fetch_candles(self, label: str, interval: str) -> List[Dict]:
        # Preserve backward-compatible behaviour: missing API key raises.
        if not self.api_key:
            raise RuntimeError("TWELVE_DATA_API_KEY missing")

        # Networked provider behaviour is intentionally not implemented here to
        # keep unit tests deterministic and offline. If you run Agent02 in a
        # real environment with TWELVE_DATA_API_KEY set, replace this with a
        # proper HTTP client to Twelve Data's time series endpoint.
        raise NotImplementedError(
            "TwelveDataProvider network client not implemented in this shim; "
            "inject a provider in tests or implement network logic for runtime use."
        )


# Lazy import of CTraderProvider so tests that don't need it aren't forced to
# import requests / network libs.
def _import_ctrader():
    try:
        from market.ctrader_provider import CTraderProvider

        return CTraderProvider
    except Exception:
        return None


def get_default_provider() -> IMarketDataProvider:
    """Return a provider instance chosen by environment configuration.

    Priority:
      1. MARKET_PROVIDER env ("ctrader")
      2. presence of CTRADER_CLIENT_ID/SECRET
      3. fallback to TwelveDataProvider
    """
    provider_choice = os.environ.get("MARKET_PROVIDER", "").lower()
    if provider_choice == "ctrader":
        CTrader = _import_ctrader()
        if not CTrader:
            raise RuntimeError("CTrader provider requested but not available")
        return CTrader()

    # auto-detect by presence of credentials
    if os.environ.get("CTRADER_CLIENT_ID") and os.environ.get("CTRADER_CLIENT_SECRET"):
        CTrader = _import_ctrader()
        if CTrader:
            return CTrader()

    # default fallback
    return TwelveDataProvider()
