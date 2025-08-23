from dataclasses import dataclass
from .enum import Symbol, Exchange

@dataclass
class Kline:
    symbol: Symbol
    exchange: Exchange
    open_time_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: float
    close_time_ms: int