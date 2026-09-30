"""Track placement tests. No Pygame window."""

from datetime import date

from bank.forecast import ForecastEngine, ForecastResult
from bank.models import ForecastEvent, Transaction
from game.logic import apply_hit, build_creates, event_to_x, is_bankrupt
from game.settings import PIXELS_PER_DAY, WORLD_WIDTH


def test_event_x_moves_right_for_later_days():
    today = date(2026, 9, 27)
    soon = ForecastEvent(on=today, amount=-100, label="today", kind="outflow")
    later = ForecastEvent(on=date(2026, 9, 29), amount=-100, label="later", kind="outflow")
    assert event_to_x(soon, today) == float(WORLD_WIDTH)
    assert event_to_x(later, today) == float(WORLD_WIDTH + 2 * PIXELS_PER_DAY)


def test_build_creates_coins_and_rocks():
    today = date(2026, 9, 27)
    forecast = ForecastResult(
        starting_balance=1000,
        events=[
            ForecastEvent(on=today, amount=-200, label="DSTV", kind="outflow"),
            ForecastEvent(on=date(2026, 9, 28), amount=500, label="Payday", kind="payday"),
        ],
        daily_balances=[],
        danger_on=None,
    )
    spawns = build_creates(forecast, today)
    assert [item.kind for item in spawns] == ["rock", "coin"]
    assert apply_hit(1000, spawns[0]) == 800
    assert apply_hit(800, spawns[1]) == 1300


def test_bankrupt_flag():
    assert is_bankrupt(-0.01) is True
    assert is_bankrupt(0) is False


def test_engine_plus_spawns_end_to_end():
    today = date(2026, 9, 27)
    txs = [
        Transaction(-900, "DSTV DEBIT ORDER", date(2026, 8, 28)),
        Transaction(-900, "DSTV DEBIT ORDER", date(2026, 7, 28)),
    ]
    forecast = ForecastEngine(horizon_days=10, payday_day=None).build(5000, txs, today=today)
    spawns = build_creates(forecast, today)
    assert any(spawn.kind == "rock" for spawn in spawns)

def test_jumping_a_rock_is_a_skip_and_missing_a_coin_is_a_miss():
    from game.logic import resolve_miss

    assert resolve_miss("rock") == "skipped"
    assert resolve_miss("coin") == "missed"