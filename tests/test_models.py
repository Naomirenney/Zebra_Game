from datetime import date

from bank.models import Transaction, parse_date

"""Checks that inflows, outflows, and date parsing behave."""
def test_inflow_outflow_flags():
    out = Transaction(-10, "x", date.today())
    inn = Transaction(10, "y", date.today())
    assert out.is_outflow
    assert inn.is_inflow


def test_parse_date_iso():
    assert parse_date("2026-09-26") == date(2026, 9, 26)
    assert parse_date(None) is None