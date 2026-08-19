"""Minimal HTTP callback service for cTrader OAuth.

Run behind a real HTTPS reverse proxy / Cloud Run service. GitHub Actions is
not a persistent OAuth callback host; this module is intended for the Aurum
web runtime deployed from this repository.

Endpoints:
  GET /auth/ctrader/connect  -> redirects to cTrader authorization
  GET /auth/ctrader/callback -> exchanges authorization code
  GET /auth/ctrader/status   -> safe connection status (no token values)
"""
from __future__ import annotations

import html
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from auth.ctrader_oauth import CTraderOAuth, CTraderOAuthError


_PENDING_STATE: str | None = None


def _oauth() -> CTraderOAuth:
    return CTraderOAuth()


class Handler(BaseHTTPRequestHandler):
    server_version = "AurumCTraderOAuth/1.0"

    def _send(self, status: int, body: str, content_type: str = "text/html") -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        global _PENDING_STATE
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path == "/auth/ctrader/connect":
            try:
                url, state = _oauth().authorization_url(
                    scope=os.environ.get("CTRADER_OAUTH_SCOPE", "accounts")
                )
                _PENDING_STATE = state
                self.send_response(302)
                self.send_header("Location", url)
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
            except CTraderOAuthError as exc:
                self._send(500, f"cTrader OAuth configuration error: {html.escape(str(exc))}")
            return

        if parsed.path == "/auth/ctrader/callback":
            code = query.get("code", [""])[0]
            state = query.get("state", [""])[0]
            if not code:
                self._send(400, "cTrader OAuth callback did not contain an authorization code")
                return
            if not _PENDING_STATE or not state or state != _PENDING_STATE:
                self._send(400, "cTrader OAuth state validation failed")
                return
            try:
                token = _oauth().exchange_code(code)
                _PENDING_STATE = None
                self._send(
                    200,
                    "<h1>cTrader connected</h1><p>Aurum stored the server-side token. You may close this window.</p>"
                    f"<p>Token expires in approximately {int(token.expires_at - __import__('time').time())} seconds.</p>",
                )
            except CTraderOAuthError as exc:
                _PENDING_STATE = None
                self._send(502, f"cTrader token exchange failed: {html.escape(str(exc))}")
            return

        if parsed.path == "/auth/ctrader/status":
            try:
                token = _oauth().token_store.load()
                status = "CONNECTED" if token and not token.refresh_required else (
                    "REFRESH_REQUIRED" if token else "DISCONNECTED"
                )
                self._send(200, f'{{"status":"{status}"}}', "application/json")
            except CTraderOAuthError:
                self._send(500, '{"status":"INVALID_STATE"}', "application/json")
            return

        self._send(404, "Not found")

    def log_message(self, format: str, *args) -> None:
        # Do not log query strings: OAuth callbacks contain authorization codes.
        print(f"[oauth] {self.command} {self.path.split('?')[0]}")


def main() -> None:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Aurum cTrader OAuth callback server listening on {host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
