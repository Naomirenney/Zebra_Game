"""Forecast tests using made-up transactions. No HTTP."""

from datetime import date, timedelta

from bank.forecast import ForecastEngine
from bank.models import Transaction


def test_detects_monthly_debit_and_projects_forward():
    today = date(2026, 9, 26)
    txs = [
        Transaction(-899.0, "DSTV DEBIT ORDER", date(2026, 8, 27)),
        Transaction(-899.0, "DSTV DEBIT ORDER", date(2026, 7, 27)),
        Transaction(18000.0, "SALARY", date(2026, 8, 25)),
        Transaction(18000.0, "SALARY", date(2026, 7, 25)),
    ]
    result = ForecastEngine(horizon_days=35, payday_day=25).build(5000, txs, today=today)
    labels = {event.label for event in result.events}
    assert any("Dstv" in label or "DSTV" in label.upper() for label in labels)
    assert any(event.kind == "payday" for event in result.events)
    assert result.daily_balances[0][0] == today


def test_danger_day_when_outflow_exceeds_balance():
    today = date(2026, 9, 26)
    txs = [
        Transaction(-4000.0, "RENT DEBIT ORDER", date(2026, 8, 28)),
        Transaction(-4000.0, "RENT DEBIT ORDER", date(2026, 7, 28)),
    ]
    result = ForecastEngine(horizon_days=10, payday_day=None).build(1000, txs, today=today)
    assert result.danger_on is not None
    assert result.danger_on >= today


def test_ignores_one_off_small_card_spend():
    today = date(2026, 9, 26)
    txs = [Transaction(-45.0, "WOOLIES POS", today - timedelta(days=3))]
    result = ForecastEngine(horizon_days=7, payday_day=None).build(2000, txs, today=today)
    assert result.events == []