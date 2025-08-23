from dataclasses import dataclass
from .enum import Side, Symbol, Exchange

@dataclass
class Trade:
    id: int
    symbol: Symbol
    exchange: Exchange
    taker_side: Side
    price: float
    quantity: float
    time_ms: int


