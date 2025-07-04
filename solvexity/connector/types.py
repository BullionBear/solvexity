from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class Exchange(Enum):
    BINANCE = "BINANCE"
    BINANCE_FUTURES = "BINANCE_FUTURES"
    BYBIT = "BYBIT"


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP_LIMIT = "STOP_LIMIT"
    STOP_MARKET = "STOP_MARKET"
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"
    TAKE_PROFIT_MARKET = "TAKE_PROFIT_MARKET"


class TimeInForce(Enum):
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"


class OrderStatus(Enum):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    PENDING_CANCEL = "PENDING_CANCEL"
    REJECTED = "REJECTED"


class InstrumentType(Enum):
    SPOT = "SPOT"
    FUTURES = "FUTURES"
    MARGIN = "MARGIN"
    PERPETUAL = "PERP"
    OPTION = "OPTION"


class Symbol(BaseModel):
    base_currency: str = Field(..., description="The base currency of the symbol")
    quote_currency: str = Field(..., description="The quote currency of the symbol")
    instrument_type: InstrumentType = Field(..., description="The type of instrument")

    def to_str(self) -> str:
        return f"{self.base_currency}-{self.quote_currency}-{self.instrument_type.value}"
    
    @classmethod
    def from_str(cls, symbol_str: str) -> "Symbol":
        base_currency, quote_currency, instrument_type = symbol_str.split("-")
        return cls(base_currency=base_currency, quote_currency=quote_currency, instrument_type=InstrumentType(instrument_type))


class OrderBook(BaseModel):
    symbol: Symbol = Field(..., description="The symbol of the order book")
    last_update_id: int = Field(..., description="The last update id of the order book")
    bids: list[tuple[Decimal, Decimal]] = Field(
        ..., description="The bids of the order book"
    )
    asks: list[tuple[Decimal, Decimal]] = Field(
        ..., description="The asks of the order book"
    )


class OrderBookUpdate(BaseModel):
    symbol: Symbol = Field(..., description="The symbol of the order book update")
    event_time: int = Field(..., description="The event time of the order book update")
    first_update_id: int = Field(
        ..., description="The first update id of the order book update"
    )
    last_update_id: int = Field(
        ..., description="The last update id of the order book update"
    )
    prev_last_update_id: int = Field(
        ..., description="The previous last update id of the order book update"
    )
    bids: list[tuple[Decimal, Decimal]] = Field(
        ..., description="The bids of the order book update"
    )
    asks: list[tuple[Decimal, Decimal]] = Field(
        ..., description="The asks of the order book update"
    )


class OHLCV(BaseModel):
    symbol: Symbol = Field(..., description="The symbol of the OHLCV")
    open_time: int = Field(..., description="The open time of the OHLCV")
    open: Decimal = Field(..., description="The open price of the OHLCV")
    high: Decimal = Field(..., description="The high price of the OHLCV")
    low: Decimal = Field(..., description="The low price of the OHLCV")
    close: Decimal = Field(..., description="The close price of the OHLCV")
    volume: Decimal = Field(..., description="The volume of the OHLCV")
    close_time: int = Field(..., description="The close time of the OHLCV")
    quote_volume: Decimal = Field(..., description="The quote volume of the OHLCV")
    n_trades: int | None = Field(None, description="The number of trades of the OHLCV")
    taker_buy_base_currency_volume: Decimal | None = Field(
        None, description="The taker buy base asset volume of the OHLCV"
    )
    taker_buy_quote_currency_volume: Decimal | None = Field(
        None, description="The taker buy quote asset volume of the OHLCV"
    )


class Trade(BaseModel):
    id: int = Field(..., description="The id of the trade")
    exchange: Exchange = Field(..., description="The exchange of the trade")
    symbol: Symbol = Field(..., description="The symbol of the trade")
    price: Decimal = Field(..., description="The price of the trade")
    quantity: Decimal = Field(..., description="The quantity of the trade")
    timestamp: int = Field(..., description="The time of the trade")
    side: OrderSide = Field(..., description="The side of the trade")


class Order(BaseModel):
    symbol: Symbol = Field(..., description="The symbol of the order")
    order_id: str | int = Field(..., description="The id of the order")
    client_order_id: str = Field(..., description="The client id of the order")
    price: Decimal = Field(..., description="The price of the order")
    original_quantity: Decimal = Field(
        ..., description="The original quantity of the order"
    )
    executed_quantity: Decimal = Field(
        ..., description="The executed quantity of the order"
    )
    side: OrderSide = Field(..., description="The side of the order")
    order_type: OrderType = Field(..., description="The type of the order")
    time_in_force: TimeInForce = Field(
        ..., description="The time in force of the order"
    )
    status: OrderStatus = Field(..., description="The status of the order")
    timestamp: int = Field(..., description="The timestamp of the order")
    update_time: int = Field(..., description="The update time of the order")


class AccountBalance(BaseModel):
    asset: str = Field(..., description="The asset of the account balance")
    free: Decimal = Field(..., description="The free balance of the account balance")
    locked: Decimal = Field(
        ..., description="The locked balance of the account balance"
    )


class MyTrade(BaseModel):
    id: int = Field(..., description="The id of the trade")
    order_id: int = Field(..., description="The id of the order")
    symbol: Symbol = Field(..., description="The symbol of the trade")
    price: Decimal = Field(..., description="The price of the trade")
    quantity: Decimal = Field(..., description="The quantity of the trade")
    timestamp: int = Field(..., description="The time of the trade")
    side: OrderSide = Field(..., description="The side of the trade")
    is_maker: bool = Field(..., description="Whether the trade is a maker")
    commission: Decimal = Field(..., description="The commission of the trade")
    commission_asset: str = Field(..., description="The commission asset of the trade")
