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

    @classmethod
    def from_binance(cls, kline: list, symbol: str, interval: str) -> "KLine":
        return cls(
            symbol=symbol,
            interval=interval,
            open_time=int(kline[0]),
            open_px=float(kline[1]),
            high_px=float(kline[2]),
            low_px=float(kline[3]),
            close_px=float(kline[4]),
            base_asset_volume=float(kline[5]),
            close_time=int(kline[6]),
            quote_asset_volume=float(kline[7]),
            number_of_trades=int(kline[8]),
            taker_buy_base_asset_volume=float(kline[9]),
            taker_buy_quote_asset_volume=float(kline[10]),
            is_closed=True
        )
