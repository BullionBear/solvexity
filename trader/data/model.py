from pydantic import BaseModel


class KLine(BaseModel):
    interval: str
    open_time: int
    close_time: int
    event_time: int
    open: float
    high: float
    low: float
    close: float
    number_of_trades: int
    base_asset_volume: float
    quote_asset_volume: float
    taker_buy_base_asset_volume: float
    taker_buy_quote_asset_volume: float
    is_closed: bool

    @classmethod
    def from_ws(cls, data: dict, event_time: int):
        return cls(
            interval=data["i"],
            open_time=data["t"],
            close_time=data["T"],
            event_time=event_time,
            open=float(data["o"]),
            high=float(data["h"]),
            low=float(data["l"]),
            close=float(data["c"]),
            number_of_trades=data["n"],
            base_asset_volume=float(data["v"]),
            quote_asset_volume=float(data["q"]),
            taker_buy_base_asset_volume=float(data["V"]),
            taker_buy_quote_asset_volume=float(data["Q"]),
            is_closed=data["x"]
        )
    
    @classmethod
    def from_rest(cls, data: list, granular: str):
        return cls(
            interval=granular,
            open_time=data[0],
            close_time=data[6],
            update_time=data[6],
            open=float(data[1]),
            high=float(data[2]),
            low=float(data[3]),
            close=float(data[4]),
            number_of_trades=data[8],
            base_asset_volume=float(data[5]),
            quote_asset_volume=float(data[7]),
            taker_buy_base_asset_volume=float(data[9]),
            taker_buy_quote_asset_volume=float(data[10]),
            is_closed=True
        )
