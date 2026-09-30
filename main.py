"""Start Future You.

Uses the Investec sandbox when .env has a client id. Otherwise uses a fake history
so the zebra still runs. Prints the forecast, then opens the window.
"""

from __future__ import annotations

from game.app import PlayableAccount, run_game
import os
from datetime import date, timedelta

from dotenv import load_dotenv

from bank.client import InvestecClient, InvestecError
from bank.forecast import ForecastEngine
from bank.models import Transaction
from game.app import run_game


def sample_transactions(today: date) -> list[Transaction]:
    return [
        Transaction(-899.0, "DSTV DEBIT ORDER", today - timedelta(days=30)),
        Transaction(-899.0, "DSTV DEBIT ORDER", today - timedelta(days=60)),
        Transaction(-350.0, "GYM DEBIT ORDER", today - timedelta(days=28)),
        Transaction(-350.0, "GYM DEBIT ORDER", today - timedelta(days=58)),
        Transaction(18500.0, "SALARY PAYMENT", today - timedelta(days=32)),
        Transaction(18500.0, "SALARY PAYMENT", today - timedelta(days=62)),
    ]
def demo_transactions(today: date) -> list[Transaction]:
    """A made-up account. Paying every bill ends below zero. Skipping rent does not."""

    def on(months_ago: int, day: int) -> date:
        month = today.month - months_ago
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        return date(year, month, min(day, 28))

    rows: list[Transaction] = []
    for months_ago in (1, 2):
        rows.extend(
            [
                Transaction(-3000, "RENT DEBIT ORDER", on(months_ago, 4)),
                Transaction(-600, "WOOLWORTHS DEBIT ORDER", on(months_ago, 9)),
                Transaction(-350, "VODACOM DEBIT ORDER", on(months_ago, 14)),
                Transaction(-200, "NETFLIX DEBIT ORDER", on(months_ago, 18)),
                Transaction(-120, "SWEETS DEBIT ORDER", on(months_ago, 22)),
                Transaction(2000, "SALARY", on(months_ago, 27)),
            ]
        )
    return rows

def main() -> None:
    load_dotenv()
    today = date.today()
    horizon = int(os.getenv("FORECAST_DAYS", "21"))
    payday_raw = os.getenv("PAYDAY_DAY", "25").strip()
    payday_day = int(payday_raw) if payday_raw else None
    engine = ForecastEngine(horizon_days=horizon, payday_day=payday_day)

    client_id = os.getenv("INVESTEC_CLIENT_ID", "").strip()
    transactions = sample_transactions(today)
    balance_value = 4500.0

    runs: list[PlayableAccount] = []
    if client_id:
        client = InvestecClient(
            base_url=os.getenv("INVESTEC_BASE_URL", "https://openapisandbox.investec.com"),
            client_id=client_id,
            client_secret=os.getenv("INVESTEC_CLIENT_SECRET", ""),
            api_key=os.getenv("INVESTEC_API_KEY", ""),
        )
        try:
            for account in client.list_accounts():
                balance_value = client.get_balance(account.account_id).current
                transactions = client.list_transactions(account.account_id)
                forecast = engine.build(balance_value, transactions, today=today)
                title = f"{account.account_name} {account.account_number}"
                print(f"{title} | R{balance_value:.2f} | {len(forecast.events)} events")
                runs.append(PlayableAccount(title, forecast))
        except InvestecError as exc:
            print(f"Investec call failed, using sample data: {exc}")

    if not runs:
        sample = engine.build(4500.0, sample_transactions(today), today=today)
        runs.append(PlayableAccount("Sample account", sample))

    demo = ForecastEngine(horizon_days=35, payday_day=27).build(
        1500.0, demo_transactions(today), today=today
    )
    runs.insert(0, PlayableAccount("Future You demo overdraft", demo))
    
    run_game(runs)


if __name__ == "__main__":
    main()