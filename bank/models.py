from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

"""Plain data for an account, a balance, a transaction, and a future event.

No HTTP and no Pygame in this file.
"""

@dataclass(frozen=True)
class Account:
    account_id: str
    account_name: str
    account_number: str
    product_name: str = ""


@dataclass(frozen=True)
class Balance:
    current: float
    available: float
    currency: str = "ZAR"


@dataclass(frozen=True)
class Transaction:
    amount: float
    description: str
    posted_on: date
    transaction_id: str = ""
    reference: str = ""
    type_code: str = ""

    @property
    def is_inflow(self) -> bool:
        return self.amount > 0

    @property
    def is_outflow(self) -> bool:
        return self.amount < 0


@dataclass(frozen=True)
class ForecastEvent:
    on: date
    amount: float
    label: str
    kind: str

    @property
    def is_inflow(self) -> bool:
        return self.amount > 0


def parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        pass
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None