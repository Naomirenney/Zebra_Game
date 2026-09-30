"""Project a simple future balance from past transactions.

A description that repeats, or looks like a debit order, becomes a monthly outflow.
Large inflows become a payday guess. The first day the running balance goes below
zero is the danger day. This is a projection, not advice.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from statistics import median

from bank.models import ForecastEvent, Transaction


DEBIT_HINTS = ("DEBIT ORDER", "NAEDO", "MAGTAPE", "DEBITORDER")


def normalise(description: str) -> str:
    text = description.upper()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^A-Z0-9 ]+", "", text)
    return text.strip()


@dataclass
class ForecastResult:
    starting_balance: float
    events: list[ForecastEvent]
    daily_balances: list[tuple[date, float]]
    danger_on: date | None

    @property
    def ending_balance(self) -> float:
        return self.daily_balances[-1][1] if self.daily_balances else self.starting_balance


class ForecastEngine:
    def __init__(self, horizon_days: int = 21, payday_day: int | None = 25) -> None:
        self.horizon_days = horizon_days
        self.payday_day = payday_day

    def build(
            self,
            starting_balance: float,
            transactions: list[Transaction],
            today: date | None = None,
    ) -> ForecastResult:
        today = today or date.today()
        recurring = self._detect_recurring(transactions)
        events = self._project(recurring, today)
        if self.payday_day:
            events.extend(self._paydays(transactions, today))
        events.sort(key=lambda event: (event.on, event.amount))

        balances: list[tuple[date, float]] = []
        running = starting_balance
        danger: date | None = None
        by_day: dict[date, list[ForecastEvent]] = defaultdict(list)
        for event in events:
            by_day[event.on].append(event)

        for offset in range(self.horizon_days + 1):
            day = today + timedelta(days=offset)
            for event in by_day.get(day, []):
                running += event.amount
            if running < 0 and danger is None:
                danger = day
            balances.append((day, running))

        return ForecastResult(
            starting_balance=starting_balance,
            events=events,
            daily_balances=balances,
            danger_on=danger,
        )

    def _detect_recurring(self, transactions: list[Transaction]) -> list[tuple[str, float, int]]:
        groups: dict[str, list[Transaction]] = defaultdict(list)
        for tx in transactions:
            if tx.amount >= 0:
                continue
            key = normalise(tx.description)[:24] or "UNKNOWN"
            groups[key].append(tx)

        found: list[tuple[str, float, int]] = []
        for key, items in groups.items():
            if len(items) < 2:
                hinted = any(hint in normalise(items[0].description) for hint in DEBIT_HINTS)
                if not hinted:
                    continue
            amounts = [abs(item.amount) for item in items]
            typical = float(median(amounts))
            days = [item.posted_on.day for item in items]
            typical_day = int(median(days)) if days else 1
            found.append((key.title(), -typical, typical_day))
        return found

    def _project(self, recurring: list[tuple[str, float, int]], today: date) -> list[ForecastEvent]:
        events: list[ForecastEvent] = []
        end = today + timedelta(days=self.horizon_days)
        for label, amount, month_day in recurring:
            month_day = min(max(month_day, 1), 28)
            cursor = date(today.year, today.month, month_day)
            if cursor < today:
                month = today.month + 1
                year = today.year + (1 if month > 12 else 0)
                month = 1 if month > 12 else month
                cursor = date(year, month, month_day)
            while cursor <= end:
                events.append(ForecastEvent(on=cursor, amount=amount, label=label, kind="outflow"))
                month = cursor.month + 1
                year = cursor.year + (1 if month > 12 else 0)
                month = 1 if month > 12 else month
                cursor = date(year, month, month_day)
        return events

    def _paydays(self, transactions: list[Transaction], today: date) -> list[ForecastEvent]:
        inflows = [tx for tx in transactions if tx.amount > 0]
        if not inflows:
            return []
        big = sorted(inflows, key=lambda tx: tx.amount, reverse=True)[:6]
        typical = float(median(abs(tx.amount) for tx in big))
        day = self.payday_day or int(median(tx.posted_on.day for tx in big))
        day = min(max(day, 1), 28)
        events: list[ForecastEvent] = []
        end = today + timedelta(days=self.horizon_days)
        cursor = date(today.year, today.month, day)
        if cursor < today:
            month = today.month + 1
            year = today.year + (1 if month > 12 else 0)
            month = 1 if month > 12 else month
            cursor = date(year, month, day)
        while cursor <= end:
            events.append(ForecastEvent(on=cursor, amount=typical, label="Payday", kind="payday"))
            month = cursor.month + 1
            year = cursor.year + (1 if month > 12 else 0)
            month = 1 if month > 12 else month
            cursor = date(year, month, day)
        return events