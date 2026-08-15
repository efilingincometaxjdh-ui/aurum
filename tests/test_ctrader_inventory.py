from types import SimpleNamespace

from scripts.ctrader_account_inventory import authorized_account_ids


def test_authorized_account_ids_extracts_nonzero_ctid_ids():
    response = SimpleNamespace(
        ctidTraderAccount=[
            SimpleNamespace(ctidTraderAccountId=48204113),
            SimpleNamespace(ctidTraderAccountId=0),
            SimpleNamespace(ctidTraderAccountId=48204114),
        ]
    )

    assert authorized_account_ids(response) == [48204113, 48204114]


def test_authorized_account_ids_handles_empty_response():
    response = SimpleNamespace(ctidTraderAccount=[])

    assert authorized_account_ids(response) == []
