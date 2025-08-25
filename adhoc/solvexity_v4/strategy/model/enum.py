from dataclasses import dataclass
from enum import Enum

class Side(Enum):
    BUY = "buy"
    SELL = "sell"

@dataclass
class Symbol:
    quote: str
    base: str

class Instrument(Enum):
    SPOT = "spot"
    PERP = "perp"
    INVERSE = "inverse"

class Exchange(Enum):
    BINANCE = "binance"
    BINANCE_PERP = "binance_perp"