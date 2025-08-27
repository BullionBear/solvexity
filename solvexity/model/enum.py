import enum

from pydantic import BaseModel


class Side(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class Exchange(enum.Enum):
    BINANCE = "BINANCE"
    BINANCE_PERP = "BINANCE_PERP"


class Instrument(enum.Enum):
    SPOT = "SPOT"
    PERP = "PERP"


class Symbol(BaseModel):
    base: str
    quote: str


class OrderType(enum.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(enum.Enum):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"
