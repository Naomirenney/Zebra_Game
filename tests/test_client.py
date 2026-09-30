from bank.client import InvestecClient

"""Client tests with a fake HTTP session.

No network. The fake returns a token, one account, a balance, and one debit order.
"""
class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self):
        self.calls = []

    def post(self, url, headers=None, data=None, timeout=None):
        self.calls.append(("POST", url))
        return FakeResponse(200, {"access_token": "tok", "expires_in": 1799})

    def get(self, url, headers=None, params=None, timeout=None):
        self.calls.append(("GET", url))
        if url.endswith("/za/pb/v1/accounts"):
            return FakeResponse(
                200,
                {
                    "data": {
                        "accounts": [
                            {
                                "accountId": "acc-1",
                                "accountName": "Zebra Current",
                                "accountNumber": "1001",
                                "productName": "Private Bank Account",
                            }
                        ]
                    }
                },
            )
        if url.endswith("/balance"):
            return FakeResponse(
                200,
                {"data": {"currentBalance": 4500.5, "availableBalance": 4400, "currency": "ZAR"}},
            )
        if url.endswith("/transactions"):
            return FakeResponse(
                200,
                {
                    "data": {
                        "transactions": [
                            {
                                "transactionId": "t1",
                                "amount": -899,
                                "description": "DSTV DEBIT ORDER",
                                "transactionDate": "2026-08-27",
                            }
                        ]
                    }
                },
            )
        return FakeResponse(404, {})


def test_auth_and_list_accounts():
    session = FakeSession()
    client = InvestecClient(
        "https://openapisandbox.investec.com", "id", "secret", "key", session=session
    )
    accounts = client.list_accounts()
    assert accounts[0].account_id == "acc-1"
    assert any(call[0] == "POST" and call[1].endswith("/identity/v2/oauth2/token") for call in session.calls)


def test_balance_and_transactions():
    session = FakeSession()
    client = InvestecClient("https://example.test", "id", "secret", "key", session=session)
    balance = client.get_balance("acc-1")
    assert balance.current == 4500.5
    txs = client.list_transactions("acc-1")
    assert txs[0].description == "DSTV DEBIT ORDER"
    assert txs[0].amount == -899

def test_debit_amount_is_stored_negative():
    class DebitSession(FakeSession):
        def get(self, url, headers=None, params=None, timeout=None):
            if url.endswith("/transactions"):
                return FakeResponse(
                    200,
                    {
                        "data": {
                            "transactions": [
                                {
                                    "transactionId": "t-debit",
                                    "type": "DEBIT",
                                    "amount": 899,
                                    "description": "DSTV",
                                    "transactionDate": "2026-08-27",
                                }
                            ]
                        }
                    },
                )
            return super().get(url, headers=headers, params=params, timeout=timeout)

    client = InvestecClient("https://example.test", "id", "secret", "key", session=DebitSession())
    txs = client.list_transactions("acc-1")
    assert txs[0].amount == -899
    assert txs[0].is_outflow