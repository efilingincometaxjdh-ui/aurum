import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from market.ctrader_provider import CTraderProvider
from market.provider import get_default_provider


class CTraderOAuthIntegrationTests(unittest.TestCase):
    def _provider(self, account_id=None):
        return CTraderProvider(
            client_id="client",
            client_secret="secret",
            access_token="access",
            account_id=account_id,
        )

    def test_pinned_account_must_be_granted_to_access_token(self):
        provider = self._provider(account_id="200")
        response = SimpleNamespace(
            ctidTraderAccount=[SimpleNamespace(ctidTraderAccountId=100)]
        )
        with patch.object(provider, "_fail") as fail, patch.object(provider, "_authenticate_account") as auth:
            provider._on_account_list(response)
        fail.assert_called_once()
        auth.assert_not_called()
        self.assertIn("not authorized", str(fail.call_args.args[0]))

    def test_authorized_pinned_account_is_authenticated(self):
        provider = self._provider(account_id="200")
        response = SimpleNamespace(
            ctidTraderAccount=[SimpleNamespace(ctidTraderAccountId=100), SimpleNamespace(ctidTraderAccountId=200)]
        )
        with patch.object(provider, "_authenticate_account") as auth:
            provider._on_account_list(response)
        auth.assert_called_once_with()
        self.assertEqual(provider._account_id, 200)

    def test_factory_can_use_oauth_token_when_static_token_is_absent(self):
        class FakeProvider:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

        with patch.dict(
            os.environ,
            {
                "MARKET_PROVIDER": "ctrader",
                "CTRADER_CLIENT_ID": "client",
                "CTRADER_CLIENT_SECRET": "secret",
            },
            clear=True,
        ), patch("market.provider._oauth_access_token", return_value="oauth-access"), patch(
            "market.provider._import_ctrader", return_value=FakeProvider
        ):
            provider = get_default_provider()
        self.assertEqual(provider.kwargs["access_token"], "oauth-access")
        self.assertEqual(provider.kwargs["client_id"], "client")
        self.assertEqual(provider.kwargs["client_secret"], "secret")


if __name__ == "__main__":
    unittest.main()
