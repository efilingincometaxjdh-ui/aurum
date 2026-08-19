"""Read-only cTrader Open API market-data provider.

Uses Spotware's official ``ctrader-open-api`` Python SDK over the official
Open API connection. Authentication uses the provisioned access token plus
application client credentials, then discovers and authenticates an account.
Historical XAUUSD trendbars are requested through ``ProtoOAGetTrendbarsReq``.

Required environment:
- CTRADER_CLIENT_ID
- CTRADER_CLIENT_SECRET
- CTRADER_ACCESS_TOKEN (or an OAuth token supplied by the provider factory)

Optional:
- CTRADER_ACCOUNT_ID: pin a specific authorized account; it is always verified
  against the accounts granted to the current access token.
- CTRADER_ENV: ``demo`` (default) or ``live``.
- CTRADER_SYMBOL: target symbol, default ``XAU/USD``.
- CTRADER_SYMBOL_ALIASES: comma-separated broker-specific symbol aliases.
- CTRADER_REQUEST_COUNT: bars per timeframe, default 250.
"""
from __future__ import annotations

import calendar
import datetime as _dt
import os
from typing import Dict, List, Optional

from ctrader_open_api import Client, EndPoints, TcpProtocol
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAAccountAuthReq,
    ProtoOAApplicationAuthReq,
    ProtoOAGetAccountListByAccessTokenReq,
    ProtoOAGetTrendbarsReq,
    ProtoOASymbolByIdReq,
    ProtoOASymbolsListReq,
)
from ctrader_open_api.messages.OpenApiModelMessages_pb2 import ProtoOATrendbarPeriod
from twisted.internet import reactor


class CTraderProvider:
    """Synchronous facade over Spotware's asynchronous Open API client."""

    INTERVAL_TO_PERIOD = {
        "1min": "M1",
        "2min": "M2",
        "3min": "M3",
        "4min": "M4",
        "5min": "M5",
        "10min": "M10",
        "15min": "M15",
        "30min": "M30",
        "1h": "H1",
        "4h": "H4",
        "12h": "H12",
        "1d": "D1",
        "1w": "W1",
        "1mo": "MN1",
    }

    def __init__(
        self,
        *,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        account_id: Optional[str] = None,
        environment: Optional[str] = None,
        symbol: Optional[str] = None,
        request_count: Optional[int] = None,
        timeout: int = 20,
    ):
        self.client_id = client_id or os.environ.get("CTRADER_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("CTRADER_CLIENT_SECRET")
        self.access_token = access_token or os.environ.get("CTRADER_ACCESS_TOKEN")
        self.account_id = account_id or os.environ.get("CTRADER_ACCOUNT_ID")
        self.environment = (environment or os.environ.get("CTRADER_ENV") or "demo").lower()
        self.symbol_name = symbol or os.environ.get("CTRADER_SYMBOL") or "XAU/USD"
        self.symbol_aliases = self._configured_symbol_aliases()
        self.request_count = int(request_count or os.environ.get("CTRADER_REQUEST_COUNT", "250"))
        self.timeout = int(os.environ.get("CTRADER_REQUEST_TIMEOUT", str(timeout)))

        if not self.client_id or not self.client_secret or not self.access_token:
            raise RuntimeError(
                "cTrader configuration missing: CTRADER_CLIENT_ID, "
                "CTRADER_CLIENT_SECRET and an access token are required"
            )
        if self.environment not in {"demo", "live"}:
            raise RuntimeError("CTRADER_ENV must be 'demo' or 'live'")
        if self.request_count <= 0:
            raise RuntimeError("CTRADER_REQUEST_COUNT must be positive")

        self._client = None
        self._account_id: Optional[int] = int(self.account_id) if self.account_id else None
        self._symbol_id: Optional[int] = None
        self._symbol_digits = 5
        self._loaded = False
        self._timeframes: List[str] = []
        self._index = 0
        self._cache: Dict[str, List[Dict]] = {}
        self._error: Optional[Exception] = None

    @staticmethod
    def _normalize_symbol(value: str) -> str:
        return "".join(ch for ch in value.upper() if ch.isalnum())

    def _configured_symbol_aliases(self) -> List[str]:
        raw = os.environ.get("CTRADER_SYMBOL_ALIASES", "")
        return [item.strip() for item in raw.split(",") if item.strip()]

    @classmethod
    def _matches_symbol(cls, configured: str, candidate: str) -> bool:
        return cls._normalize_symbol(configured) == cls._normalize_symbol(candidate)

    @classmethod
    def _find_symbol(cls, configured: str, candidates, aliases=None):
        aliases = aliases or []
        for requested_name in [configured, *aliases]:
            match = next(
                (
                    item
                    for item in candidates
                    if cls._matches_symbol(requested_name, getattr(item, "symbolName", ""))
                ),
                None,
            )
            if match is not None:
                return match
        return None

    @staticmethod
    def _price_from_relative(relative: int, digits: int) -> float:
        """Convert cTrader's fixed 1e-5 relative price to symbol precision."""
        if not isinstance(digits, int) or isinstance(digits, bool) or digits < 0:
            raise ValueError("cTrader symbol digits must be a non-negative integer")
        if not isinstance(relative, int) or isinstance(relative, bool):
            raise ValueError("cTrader relative price must be an integer")
        return round(relative / 100000.0, digits)

    @classmethod
    def normalize_trendbar(cls, trendbar, digits: int) -> Dict:
        if not hasattr(trendbar, "low") or not trendbar.low:
            raise ValueError("cTrader trendbar missing low price")
        if not hasattr(trendbar, "utcTimestampInMinutes"):
            raise ValueError("cTrader trendbar missing utcTimestampInMinutes")

        low_relative = int(trendbar.low)
        open_relative = low_relative + int(getattr(trendbar, "deltaOpen", 0))
        high_relative = low_relative + int(getattr(trendbar, "deltaHigh", 0))
        close_relative = low_relative + int(getattr(trendbar, "deltaClose", 0))

        timestamp = int(trendbar.utcTimestampInMinutes) * 60
        dt = _dt.datetime.fromtimestamp(timestamp, tz=_dt.timezone.utc).isoformat()

        return {
            "open": cls._price_from_relative(open_relative, digits),
            "high": cls._price_from_relative(high_relative, digits),
            "low": cls._price_from_relative(low_relative, digits),
            "close": cls._price_from_relative(close_relative, digits),
            "datetime": dt,
        }

    def fetch_candles(self, label: str, interval: str, count: int = 250) -> List[Dict]:
        """Return normalized historical candles for one timeframe."""
        if interval not in self.INTERVAL_TO_PERIOD:
            raise ValueError(f"Unsupported cTrader interval: {interval}")
        self._ensure_loaded()
        return list(self._cache.get(interval, []))

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        if reactor.running:
            raise RuntimeError("cTrader provider cannot start its private reactor while another reactor is running")

        self._timeframes = ["5min", "15min", "1h", "4h"]
        host = EndPoints.PROTOBUF_LIVE_HOST if self.environment == "live" else EndPoints.PROTOBUF_DEMO_HOST
        self._client = Client(host, EndPoints.PROTOBUF_PORT, TcpProtocol)
        self._client.setConnectedCallback(self._on_connected)
        self._client.setDisconnectedCallback(self._on_disconnected)
        self._client.startService()

        reactor.callLater(self.timeout, self._fail, RuntimeError("cTrader connection timed out"))
        reactor.run()

        if self._error:
            raise self._error
        if not self._loaded:
            raise RuntimeError("cTrader provider stopped without producing market data")

    def _on_connected(self, _client) -> None:
        request = ProtoOAApplicationAuthReq()
        request.clientId = self.client_id
        request.clientSecret = self.client_secret
        self._send(request, self._on_application_auth)

    def _on_application_auth(self, _response) -> None:
        # Always enumerate the accounts granted to the current access token.
        # A configured account is only a selector, never an authorization grant.
        request = ProtoOAGetAccountListByAccessTokenReq()
        request.accessToken = self.access_token
        self._send(request, self._on_account_list)

    def _on_account_list(self, response) -> None:
        accounts = list(getattr(response, "ctidTraderAccount", []))
        if not accounts:
            self._fail(RuntimeError("cTrader access token has no authorized trading accounts"))
            return

        authorized_ids = {int(account.ctidTraderAccountId) for account in accounts}
        if self._account_id is not None:
            if self._account_id not in authorized_ids:
                self._fail(
                    RuntimeError(
                        "configured CTRADER_ACCOUNT_ID is not authorized by CTRADER_ACCESS_TOKEN"
                    )
                )
                return
        else:
            self._account_id = int(accounts[0].ctidTraderAccountId)

        self._authenticate_account()

    def _authenticate_account(self) -> None:
        request = ProtoOAAccountAuthReq()
        request.ctidTraderAccountId = self._account_id
        request.accessToken = self.access_token
        self._send(request, self._on_account_auth)

    def _on_account_auth(self, _response) -> None:
        request = ProtoOASymbolsListReq()
        request.ctidTraderAccountId = self._account_id
        request.includeArchivedSymbols = False
        self._send(request, self._on_symbols)

    def _on_symbols(self, response) -> None:
        candidates = list(getattr(response, "symbol", []))
        match = self._find_symbol(self.symbol_name, candidates, self.symbol_aliases)
        if match is None:
            available = sorted(
                getattr(item, "symbolName", "")
                for item in candidates
                if getattr(item, "symbolName", "")
            )
            preview = ", ".join(available[:30])
            suffix = " ..." if len(available) > 30 else ""
            self._fail(
                RuntimeError(
                    f"cTrader symbol not found: {self.symbol_name}; "
                    f"aliases={self.symbol_aliases or 'none'}; "
                    f"available_symbols={preview}{suffix}"
                )
            )
            return

        self._symbol_id = int(match.symbolId)
        detail = ProtoOASymbolByIdReq()
        detail.ctidTraderAccountId = self._account_id
        detail.symbolId.append(self._symbol_id)
        self._send(detail, self._on_symbol_details)

    def _on_symbol_details(self, response) -> None:
        symbols = list(getattr(response, "symbol", []))
        if symbols:
            self._symbol_digits = int(getattr(symbols[0], "digits", 5))
        self._index = 0
        self._request_next_timeframe()

    def _request_next_timeframe(self) -> None:
        if self._index >= len(self._timeframes):
            self._loaded = True
            self._stop_reactor()
            return

        interval = self._timeframes[self._index]
        period_name = self.INTERVAL_TO_PERIOD[interval]
        period = ProtoOATrendbarPeriod.Value(period_name)
        now = _dt.datetime.now(tz=_dt.timezone.utc)
        lookback_minutes = {
            "5min": self.request_count * 5 * 2,
            "15min": self.request_count * 15 * 2,
            "1h": self.request_count * 60 * 2,
            "4h": self.request_count * 240 * 2,
        }[interval]
        from_ts = calendar.timegm((now - _dt.timedelta(minutes=lookback_minutes)).utctimetuple()) * 1000
        to_ts = calendar.timegm(now.utctimetuple()) * 1000

        request = ProtoOAGetTrendbarsReq()
        request.ctidTraderAccountId = self._account_id
        request.period = period
        request.symbolId = self._symbol_id
        request.count = min(self.request_count, 2500)
        request.fromTimestamp = from_ts
        request.toTimestamp = to_ts
        self._send(request, lambda response: self._on_trendbars(interval, response))

    def _on_trendbars(self, interval: str, response) -> None:
        trendbars = list(getattr(response, "trendbar", []))
        normalized = [self.normalize_trendbar(bar, self._symbol_digits) for bar in trendbars]
        normalized.sort(key=lambda item: item["datetime"])
        self._cache[interval] = normalized
        self._index += 1
        self._request_next_timeframe()

    def _send(self, request, callback) -> None:
        try:
            deferred = self._client.send(request)
            deferred.addCallback(callback)
            deferred.addErrback(self._on_error)
        except Exception as exc:
            self._fail(exc)

    def _on_error(self, failure) -> None:
        try:
            failure.raiseException()
        except Exception as exc:
            self._fail(RuntimeError(f"cTrader API request failed: {exc}"))

    def _on_disconnected(self, _client, reason) -> None:
        if not self._loaded and self._error is None:
            self._fail(RuntimeError(f"cTrader connection closed before data load: {reason}"))

    def _fail(self, error: Exception) -> None:
        if self._error is None:
            self._error = error
        self._stop_reactor()

    def _stop_reactor(self) -> None:
        try:
            if reactor.running:
                reactor.stop()
        finally:
            if self._client is not None:
                try:
                    self._client.stopService()
                except Exception:
                    pass
