from pydantic import BaseModel
from decimal import Decimal

class BarPayload(BaseModel):
    symbol: str
    exchange: str
    interval: str
    open_time: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    close_time: int
    volume: Decimal
    quote_volume: Decimal
    number_of_trades: int
    taker_buy_base_volume: Decimal
    taker_buy_quote_volume: Decimal
