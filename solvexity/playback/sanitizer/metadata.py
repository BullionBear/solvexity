from solvexity.model import Exchange, Instrument, Symbol
from pydantic import BaseModel

class Segment(BaseModel):
    exchange: Exchange
    instrument: Instrument
    symbol: Symbol
    start_id: int
    end_id: int
    start_time: int
    end_time: int
    total_volume: float
    total_quote_volume: float
    total_trades: int
    

class Metadata(BaseModel):
    file: str
    md5: str
    segments: list[Segment]
    