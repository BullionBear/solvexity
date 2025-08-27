from pydantic import BaseModel

from .enum import Exchange, Instrument, Side, Symbol


class Trade(BaseModel):
    exchange: Exchange
    instrument: Instrument
    trade_id: str
    symbol: Symbol
    side: Side
    price: float
    quantity: float
    timestamp: int
