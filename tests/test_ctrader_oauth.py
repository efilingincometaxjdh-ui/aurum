import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from auth.ctrader_oauth import CTraderOAuth, CTraderOAuthError, FileTokenStore, OAuthToken


class CTraderOAuthTests(unittest.TestCase):
    def test_authorization_url_contains_exact_redirect_and_scope(self):
        oauth = CTraderOAuth(
            client_id="client",
            client_secret="secret",
            redirect_uri="https://example.com/auth/callback",
        )
        url, state = oauth.authorization_url(scope="accounts", state="known-state")
        self.assertIn("client_id=client", url)
        self.assertIn("redirect_uri=https%3A%2F%2Fexample.com%2Fauth%2Fcallback", url)
        self.assertIn("scope=accounts", url)
        self.assertIn("product=web", url)
        self.assertIn("state=known-state", url)
        self.assertEqual(state, "known-state")

    def test_invalid_scope_fails_closed(self):
        oauth = CTraderOAuth("client", "secret", "https://example.com/callback")
        with self.assertRaises(CTraderOAuthError):
            oauth.authorization_url(scope="invalid")

    def test_token_store_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "token.json"
            store = FileTokenStore(str(path))
            token = OAuthToken("access", "refresh", time.time() + 3600)
            store.save(token)
            loaded = store.load()
            self.assertEqual(loaded.access_token, "access")
            self.assertEqual(loaded.refresh_token, "refresh")
            self.assertEqual(loaded.expires_at, token.expires_at)
            self.assertEqual(json.loads(path.read_text())["token_type"], "bearer")

    def test_parse_token_rejects_incomplete_response(self):
        with self.assertRaises(CTraderOAuthError):
            CTraderOAuth._parse_token({"accessToken": "only"})

    def test_exchange_persists_token_without_logging_secret(self):
        with tempfile.TemporaryDirectory() as directory:
            store = FileTokenStore(str(Path(directory) / "token.json"))
            oauth = CTraderOAuth(
                "client", "secret", "https://example.com/callback", store
            )
            payload = {
                "accessToken": "access",
                "refreshToken": "refresh",
                "expiresIn": 3600,
                "tokenType": "bearer",
                "errorCode": None,
            }
            with patch.object(oauth, "_token_request", return_value=payload) as request:
                token = oauth.exchange_code("authorization-code")
            request.assert_called_once()
            self.assertEqual(token.access_token, "access")
            self.assertIsNotNone(store.load())


if __name__ == "__main__":
    unittest.main()
