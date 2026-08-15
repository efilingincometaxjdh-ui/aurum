"""Read-only cTrader account/symbol inventory diagnostic.

This diagnostic is intentionally separate from Agent02 production behavior. It
verifies that the authorized DEMO account exposes symbol inventory and records
only non-sensitive account/symbol metadata needed to diagnose an empty
ProtoOASymbolsListRes response.
"""
from __future__ import annotations

import os
from typing import Optional

from ctrader_open_api import Client, EndPoints, TcpProtocol
from ctrader_open_api.messages.OpenApiMessages_pb2 import (
    ProtoOAAccountAuthReq,
    ProtoOAApplicationAuthReq,
    ProtoOAGetAccountListByAccessTokenReq,
    ProtoOASymbolsListReq,
)
from twisted.internet import reactor


class InventoryProbe:
    def __init__(self) -> None:
        self.client_id = os.environ["CTRADER_CLIENT_ID"]
        self.client_secret = os.environ["CTRADER_CLIENT_SECRET"]
        self.access_token = os.environ["CTRADER_ACCESS_TOKEN"]
        account_id = os.environ.get("CTRADER_ACCOUNT_ID")
        self.account_id: Optional[int] = int(account_id) if account_id else None
        self.client = None
        self.error: Optional[Exception] = None

    def start(self) -> None:
        host = EndPoints.PROTOBUF_DEMO_HOST
        self.client = Client(host, EndPoints.PROTOBUF_PORT, TcpProtocol)
        self.client.setConnectedCallback(self.on_connected)
        self.client.setDisconnectedCallback(self.on_disconnected)
        self.client.startService()
        reactor.callLater(20, self.fail, RuntimeError("cTrader inventory probe timed out"))
        reactor.run()
        if self.error:
            raise self.error

    def on_connected(self, _client) -> None:
        request = ProtoOAApplicationAuthReq()
        request.clientId = self.client_id
        request.clientSecret = self.client_secret
        self.send(request, self.on_application_auth)

    def on_application_auth(self, _response) -> None:
        if self.account_id is not None:
            self.authorize_account()
            return
        request = ProtoOAGetAccountListByAccessTokenReq()
        request.accessToken = self.access_token
        self.send(request, self.on_account_list)

    def on_account_list(self, response) -> None:
        accounts = list(getattr(response, "ctidTraderAccount", []))
        if not accounts:
            self.fail(RuntimeError("access token returned no authorized accounts"))
            return
        self.account_id = int(accounts[0].ctidTraderAccountId)
        print(f"Authorized accounts returned: {len(accounts)}")
        self.authorize_account()

    def authorize_account(self) -> None:
        request = ProtoOAAccountAuthReq()
        request.ctidTraderAccountId = self.account_id
        request.accessToken = self.access_token
        self.send(request, self.on_account_auth)

    def on_account_auth(self, response) -> None:
        print(f"Account authorization response received for configured account: {self.account_id is not None}")
        self.request_symbols(include_archived=False)

    def request_symbols(self, *, include_archived: bool) -> None:
        request = ProtoOASymbolsListReq()
        request.ctidTraderAccountId = self.account_id
        request.includeArchivedSymbols = include_archived
        self.send(request, lambda response: self.on_symbols(response, include_archived))

    def on_symbols(self, response, include_archived: bool) -> None:
        symbols = list(getattr(response, "symbol", []))
        archived = list(getattr(response, "archivedSymbol", []))
        names = [getattr(item, "symbolName", "") for item in symbols]
        archived_names = [getattr(item, "name", "") for item in archived]
        label = "including archived" if include_archived else "active only"
        print(f"Symbol inventory ({label}): active={len(symbols)} archived={len(archived)}")
        if names:
            print("Active symbols: " + ", ".join(sorted(filter(None, names))[:50]))
        if include_archived and archived_names:
            print("Archived symbols: " + ", ".join(sorted(filter(None, archived_names))[:50]))
        if not include_archived:
            self.request_symbols(include_archived=True)
            return
        if not symbols and not archived:
            self.fail(RuntimeError("cTrader returned zero active and zero archived symbols for the authorized account"))
            return
        self.stop()

    def send(self, request, callback) -> None:
        try:
            deferred = self.client.send(request)
            deferred.addCallback(callback)
            deferred.addErrback(self.on_error)
        except Exception as exc:
            self.fail(exc)

    def on_error(self, failure) -> None:
        try:
            failure.raiseException()
        except Exception as exc:
            self.fail(RuntimeError(f"cTrader inventory request failed: {exc}"))

    def on_disconnected(self, _client, reason) -> None:
        if self.error is None:
            self.fail(RuntimeError(f"cTrader connection closed before inventory completed: {reason}"))

    def fail(self, error: Exception) -> None:
        if self.error is None:
            self.error = error
        self.stop()

    def stop(self) -> None:
        if reactor.running:
            reactor.stop()
        if self.client is not None:
            try:
                self.client.stopService()
            except Exception:
                pass


if __name__ == "__main__":
    InventoryProbe().start()
