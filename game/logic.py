"""Turn a forecast into things on the track.

Money out becomes a rock. Money in becomes a coin.
This file does not open a window, so the tests can run it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from bank.forecast import ForecastResult
from bank.models import ForecastEvent
from game.settings import PIXELS_PER_DAY, WORLD_WIDTH


@dataclass
class Create:
    kind: str
    label: str
    amount: float
    x: float
    day: date
    size: int = 40


def days_ahead(event_day: date, today: date) -> int:
    return (event_day - today).days


def event_to_x(event: ForecastEvent, today: date) -> float:
    offset = max(days_ahead(event.on, today), 0)
    return float(WORLD_WIDTH + offset * PIXELS_PER_DAY)


def build_creates(forecast: ForecastResult, today: date) -> list[Create]:
    spawns: list[Create] = []
    
    # Calculate min and max for scaling
    outflows = [abs(e.amount) for e in forecast.events if e.amount < 0]
    inflows = [e.amount for e in forecast.events if e.amount > 0]
    
    max_outflow = max(outflows) if outflows else 1.0
    min_outflow = min(outflows) if outflows else 1.0
    max_inflow = max(inflows) if inflows else 1.0
    min_inflow = min(inflows) if inflows else 1.0

    from game.settings import ROCK_MIN_SIZE, ROCK_MAX_SIZE, COIN_MIN_SIZE, COIN_MAX_SIZE

    for event in forecast.events:
        if event.on < today:
            continue
            
        if event.amount < 0:
            kind = "rock"
            amount_abs = abs(event.amount)
            if max_outflow == min_outflow:
                size = (ROCK_MIN_SIZE + ROCK_MAX_SIZE) // 2
            else:
                scale = (amount_abs - min_outflow) / (max_outflow - min_outflow)
                size = int(ROCK_MIN_SIZE + scale * (ROCK_MAX_SIZE - ROCK_MIN_SIZE))
        else:
            kind = "coin"
            if max_inflow == min_inflow:
                size = (COIN_MIN_SIZE + COIN_MAX_SIZE) // 2
            else:
                scale = (event.amount - min_inflow) / (max_inflow - min_inflow)
                size = int(COIN_MIN_SIZE + scale * (COIN_MAX_SIZE - COIN_MIN_SIZE))

        spawns.append(
            Create(
                kind=kind,
                label=event.label,
                amount=event.amount,
                x=event_to_x(event, today),
                day=event.on,
                size=size,
            )
        )
    spawns.sort(key=lambda item: item.x)
    
    # Enforce minimum horizontal spacing so objects don't stack
    min_spacing = 300
    for i in range(1, len(spawns)):
        if spawns[i].x < spawns[i-1].x + min_spacing:
            spawns[i].x = spawns[i-1].x + min_spacing
            
    return spawns


def apply_hit(balance: float, spawn: Create) -> float:
    return balance + spawn.amount


def is_bankrupt(balance: float) -> bool:
    return balance < 0

def resolve_miss(kind: str) -> str:
    """A rock you jump is a skipped payment. A coin you miss is cash you did not collect."""
    if kind == "rock":
        return "skipped"
    return "missed"
