from dataclasses import dataclass
from .enum import Symbol, Exchange

@dataclass
class Bar:
    symbol: Symbol
    exchange: Exchange
    interval: str
    open_time_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: float
    close_time_ms: int