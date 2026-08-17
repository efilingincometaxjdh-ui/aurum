"""cTrader OAuth 2.0 helpers for Aurum.

This module deliberately keeps OAuth state separate from the market-data
provider. It implements the authorization-code exchange and refresh flow
without logging or exposing secrets. A web application can use these helpers
from its /auth/ctrader/callback endpoint.

cTrader requires the exact redirect URI to be registered in the Open API app.
Access tokens expire after roughly 30 days; refresh tokens are used to obtain
replacement tokens.
"""
from __future__ import annotations

import json
import os
import secrets
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

AUTHORIZATION_URL = "https://id.ctrader.com/my/settings/openapi/grantingaccess/"
TOKEN_URL = "https://openapi.ctrader.com/apps/token"


class CTraderOAuthError(RuntimeError):
    """Raised when cTrader OAuth cannot complete safely."""


@dataclass
class OAuthToken:
    access_token: str
    refresh_token: str
    expires_at: float
    token_type: str = "bearer"

    @property
    def expired(self) -> bool:
        return time.time() >= self.expires_at

    @property
    def refresh_required(self) -> bool:
        # Refresh slightly before expiry to avoid races during a live request.
        return time.time() >= self.expires_at - 120


class FileTokenStore:
    """Minimal server-side token store for development/single-instance use.

    The file is never intended for Git. Production multi-instance deployments
    should replace this with a durable encrypted secret store.
    """

    def __init__(self, path: Optional[str] = None) -> None:
        self.path = Path(path or os.environ.get(
            "CTRADER_TOKEN_FILE", "data/current/ctrader_oauth.json"
        ))

    def load(self) -> Optional[OAuthToken]:
        if not self.path.exists():
            return None
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            return OAuthToken(
                access_token=str(payload["access_token"]),
                refresh_token=str(payload["refresh_token"]),
                expires_at=float(payload["expires_at"]),
                token_type=str(payload.get("token_type", "bearer")),
            )
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise CTraderOAuthError("cTrader OAuth token state is invalid") from exc

    def save(self, token: OAuthToken) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(asdict(token), separators=(",", ":")),
            encoding="utf-8",
        )
        os.replace(temporary, self.path)
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass


class CTraderOAuth:
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        token_store: Optional[FileTokenStore] = None,
    ) -> None:
        self.client_id = client_id or os.environ.get("CTRADER_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("CTRADER_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or os.environ.get("CTRADER_REDIRECT_URI")
        self.token_store = token_store or FileTokenStore()
        if not self.client_id or not self.client_secret or not self.redirect_uri:
            raise CTraderOAuthError(
                "CTRADER_CLIENT_ID, CTRADER_CLIENT_SECRET and CTRADER_REDIRECT_URI are required"
            )

    def authorization_url(self, scope: str = "accounts", state: Optional[str] = None) -> tuple[str, str]:
        if scope not in {"accounts", "trading"}:
            raise CTraderOAuthError("cTrader OAuth scope must be 'accounts' or 'trading'")
        state_value = state or secrets.token_urlsafe(32)
        query = urlencode({
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": scope,
            "product": "web",
            "state": state_value,
        })
        return f"{AUTHORIZATION_URL}?{query}", state_value

    def exchange_code(self, code: str) -> OAuthToken:
        if not code:
            raise CTraderOAuthError("authorization code is missing")
        payload = self._token_request({
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        })
        token = self._parse_token(payload)
        self.token_store.save(token)
        return token

    def refresh(self, token: Optional[OAuthToken] = None) -> OAuthToken:
        current = token or self.token_store.load()
        if current is None or not current.refresh_token:
            raise CTraderOAuthError("no cTrader refresh token is available")
        payload = self._token_request({
            "grant_type": "refresh_token",
            "refresh_token": current.refresh_token,
        })
        refreshed = self._parse_token(payload)
        self.token_store.save(refreshed)
        return refreshed

    def get_valid_token(self) -> OAuthToken:
        token = self.token_store.load()
        if token is None:
            raise CTraderOAuthError("cTrader account is not connected")
        if token.refresh_required:
            return self.refresh(token)
        return token

    def _token_request(self, values: Dict[str, str]) -> Dict[str, Any]:
        params = {
            **values,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        request = Request(
            f"{TOKEN_URL}?{urlencode(params)}",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            method="GET",
        )
        try:
            with urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            raise CTraderOAuthError("cTrader token endpoint request failed") from exc
        if payload.get("errorCode"):
            raise CTraderOAuthError(
                f"cTrader token exchange failed: {payload.get('description') or payload['errorCode']}"
            )
        return payload

    @staticmethod
    def _parse_token(payload: Dict[str, Any]) -> OAuthToken:
        try:
            access_token = str(payload["accessToken"])
            refresh_token = str(payload["refreshToken"])
            expires_in = int(payload["expiresIn"])
        except (KeyError, TypeError, ValueError) as exc:
            raise CTraderOAuthError("cTrader token response is incomplete") from exc
        if not access_token or not refresh_token or expires_in <= 0:
            raise CTraderOAuthError("cTrader token response is invalid")
        return OAuthToken(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=time.time() + expires_in,
            token_type=str(payload.get("tokenType", "bearer")),
        )
