from pydantic import BaseModel

class KLine(BaseModel):
    symbol: str
    interval: str
    open_time: int
    close_time: int
    open_px: float
    high_px: float
    low_px: float
    close_px: float
    number_of_trades: int
    base_asset_volume: float
    quote_asset_volume: float
    taker_buy_base_asset_volume: float
    taker_buy_quote_asset_volume: float
    is_closed: bool
