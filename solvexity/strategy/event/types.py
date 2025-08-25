from dataclasses import dataclass
from enum import Enum

class Exchange(Enum):
    BINANCE = "binance"

class Side(Enum):
    BUY = "buy"
    SELL = "sell"

class InstrumentType(Enum):
    SPOT = "spot"
    FUTURES = "perp"

@dataclass
class Symbol:
    base: str
    quote: str


