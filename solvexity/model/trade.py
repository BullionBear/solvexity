from pydantic import BaseModel
from .enum import Symbol, Side, Exchange, Instrument

class Trade(BaseModel):
    exchange: Exchange
    instrument: Instrument
    trade_id: str
    symbol: Symbol
    side: Side
    price: float
    quantity: float
    timestamp: int
