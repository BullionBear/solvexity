from pydantic import BaseModel
from .trade import Trade
from .shared import Side, Symbol

class Bar(BaseModel):
    symbol: Symbol
    start_id: int
    current_id: int
    next_id: int
    open_time: int
    close_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    quote_volume: float
    is_closed: bool
    number_of_trades: int
    taker_buy_base_asset_volume: float
    taker_buy_quote_asset_volume: float

    @classmethod
    def from_trade(cls, trade: Trade) -> 'Bar':
        return cls(
            symbol=trade.symbol,
            start_id=trade.id,
            current_id=trade.id,
            next_id=trade.id + 1,
            open_time=trade.timestamp,
            close_time=trade.timestamp,
            open=trade.price,
            high=trade.price,
            low=trade.price,
            close=trade.price,
            volume=trade.quantity,
            quote_volume=trade.price * trade.quantity,
            number_of_trades=1,
            taker_buy_base_asset_volume=trade.quantity if trade.side == Side.SIDE_BUY else 0,
            taker_buy_quote_asset_volume=trade.price * trade.quantity if trade.side == Side.SIDE_BUY else 0,
            is_closed=False
        )

    def __radd__(self, other: Trade) -> 'Bar':
        return self.__iadd__(other)
    
    def __iadd__(self, other: Trade) -> 'Bar':
        self.current_id = other.id
        self.next_id = other.id + 1
        self.high = max(self.high, other.price)
        self.low = min(self.low, other.price)
        self.close = other.price
        self.volume += other.quantity
        self.quote_volume += other.price * other.quantity
        self.number_of_trades += 1
        self.taker_buy_base_asset_volume += other.quantity if other.side == Side.SIDE_BUY else 0
        self.taker_buy_quote_asset_volume += other.price * other.quantity if other.side == Side.SIDE_BUY else 0
        return self
    
    def enclose(self, timestamp: int):
        self.close_time = timestamp
        self.is_closed = True
        return self