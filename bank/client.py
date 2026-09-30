from __future__ import annotations

import base64
import time
from datetime import date, timedelta
from typing import Any, Optional

import requests

from bank.models import Account, Balance, Transaction, parse_date

# What it does: authenticate swaps your client id and secret for a bearer token that
# lasts about 30 minutes. list_accounts, get_balance, and list_transactions send that
# token. The session argument exists so tests can pass a fake instead of the real internet.

"""Talk to the Investec API.

This file logs in, then reads accounts, balances, and transactions.
It does not forecast and it does not draw the game.
Tests pass a fake session so this never has to touch the real bank.
"""
class InvestecError(RuntimeError):
    pass


class InvestecClient:
    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str,
        api_key: str,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_key = api_key
        self.session = session or requests.Session()
        self._token: Optional[str] = None
        self._token_expires_at: float = 0

    def authenticate(self) -> str:
        raw = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        basic = base64.b64encode(raw).decode("ascii")
        response = self.session.post(
            f"{self.base_url}/identity/v2/oauth2/token",
            headers={
                "Authorization": f"Basic {basic}",
                "x-api-key": self.api_key,
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials"},
            timeout=30,
        )
        if response.status_code >= 400:
            raise InvestecError(f"auth failed: {response.status_code} {response.text}")
        payload = response.json()
        token = payload.get("access_token") or payload.get("access token")
        if not token:
            raise InvestecError("auth response missing access_token")
        expires_in = int(payload.get("expires_in", 1799))
        self._token = token
        self._token_expires_at = time.time() + max(expires_in - 30, 60)
        return token

    def _bearer(self) -> str:
        if not self._token or time.time() >= self._token_expires_at:
            self.authenticate()
        return self._token  # type: ignore[return-value]

    def _get(self, path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        response = self.session.get(
            f"{self.base_url}{path}",
            headers={
                "Authorization": f"Bearer {self._bearer()}",
                "Accept": "application/json",
                "x-api-key": self.api_key,
            },
            params=params,
            timeout=30,
        )
        if response.status_code == 401:
            self.authenticate()
            response = self.session.get(
                f"{self.base_url}{path}",
                headers={
                    "Authorization": f"Bearer {self._bearer()}",
                    "Accept": "application/json",
                    "x-api-key": self.api_key,
                },
                params=params,
                timeout=30,
            )
        if response.status_code >= 400:
            raise InvestecError(f"GET {path} failed: {response.status_code} {response.text}")
        return response.json()

    def list_accounts(self) -> list[Account]:
        payload = self._get("/za/pb/v1/accounts")
        accounts = payload.get("data", {}).get("accounts", [])
        return [
            Account(
                account_id=str(item.get("accountId", "")),
                account_name=str(item.get("accountName") or item.get("referenceName") or ""),
                account_number=str(item.get("accountNumber", "")),
                product_name=str(item.get("productName", "")),
            )
            for item in accounts
        ]

    def get_balance(self, account_id: str) -> Balance:
        payload = self._get(f"/za/pb/v1/accounts/{account_id}/balance")
        data = payload.get("data", payload)
        current = float(data.get("currentBalance", data.get("balance", 0)) or 0)
        available = float(data.get("availableBalance", current) or current)
        currency = str(data.get("currency", "ZAR"))
        return Balance(current=current, available=available, currency=currency)

    def list_transactions(
        self,
        account_id: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> list[Transaction]:
        to_date = to_date or date.today()
        from_date = from_date or (to_date - timedelta(days=180))
        payload = self._get(
            f"/za/pb/v1/accounts/{account_id}/transactions",
            params={"fromDate": from_date.isoformat(), "toDate": to_date.isoformat()},
        )
        raw = payload.get("data", {}).get("transactions", [])
        transactions: list[Transaction] = []
        for item in raw:
            amount = item.get("amount") or item.get("Amount") or 0
            try:
                amount_f = float(amount)
            except (TypeError, ValueError):
                continue
            kind = str(item.get("type") or item.get("Type") or "").upper()
            if kind == "DEBIT" and amount_f > 0:
                amount_f = -amount_f
            elif kind == "CREDIT" and amount_f < 0:
                amount_f = abs(amount_f)
            posted = (
                parse_date(item.get("transactionDate"))
                or parse_date(item.get("postingDate"))
                or parse_date(item.get("valueDate"))
                or to_date
            )
            transactions.append(
                Transaction(
                    amount=amount_f,
                    description=str(item.get("description") or item.get("Description") or ""),
                    posted_on=posted,
                    transaction_id=str(item.get("transactionId") or item.get("TransactionId") or ""),
                    reference=str(item.get("reference") or item.get("Reference") or ""),
                    type_code=str(item.get("type") or item.get("TransactionCode") or ""),
                )
            )
        return transactions