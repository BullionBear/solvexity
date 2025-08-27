from pydantic import BaseModel

class Bar(BaseModel):
    symbol: str
    interval: str
    open_time: int
    close_time: int
    open: float
    high: float
    low: float
    close: float
    is_closed: bool
    volume: float
    timestamp: int