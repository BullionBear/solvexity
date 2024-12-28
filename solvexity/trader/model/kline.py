from pydantic import BaseModel
from decimal import Decimal

class KLine(BaseModel):
    interval: str
    open_time: int
    close_time: int
    event_time: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    number_of_trades: int
    base_asset_volume: Decimal
    quote_asset_volume: Decimal
    taker_buy_base_asset_volume: Decimal
    taker_buy_quote_asset_volume: Decimal
    is_closed: bool

    @classmethod
    def from_ws(cls, data: dict, event_time: int):
        return cls(
            interval=data["i"],
            open_time=data["t"],
            close_time=data["T"],
            event_time=event_time,
            open=Decimal(data["o"]),
            high=Decimal(data["h"]),
            low=Decimal(data["l"]),
            close=Decimal(data["c"]),
            number_of_trades=data["n"],
            base_asset_volume=Decimal(data["v"]),
            quote_asset_volume=Decimal(data["q"]),
            taker_buy_base_asset_volume=Decimal(data["V"]),
            taker_buy_quote_asset_volume=Decimal(data["Q"]),
            is_closed=data["x"]
        )
    
    @classmethod
    def from_rest(cls, data: list, granular: str):
        return cls(
            interval=granular,
            open_time=int(data[0]),
            close_time=int(data[6]),
            event_time=int(data[6]),
            open=Decimal(data[1]),
            high=Decimal(data[2]),
            low=Decimal(data[3]),
            close=Decimal(data[4]),
            number_of_trades=int(data[8]),
            base_asset_volume=Decimal(data[5]),
            quote_asset_volume=Decimal(data[7]),
            taker_buy_base_asset_volume=Decimal(data[9]),
            taker_buy_quote_asset_volume=Decimal(data[10]),
            is_closed=True
        )
    
    def to_numeric_dict(self) -> dict:
        """
        Convert the KLine instance to a dictionary, casting Decimal values to float.
        """
        data = self.model_dump()
        for key, value in data.items():
            if isinstance(value, Decimal):
                data[key] = float(value)
        return data
