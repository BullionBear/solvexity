from enum import Enum
from pydantic import BaseModel, Field
from decimal import Decimal

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

class InstrumentType(Enum):
    SPOT = "SPOT"
    FUTURES = "FUTURES"
    MARGIN = "MARGIN"
    PERPETUAL = "PERPETUAL"
    OPTION = "OPTION"

class Symbol(BaseModel):
    base_asset: str = Field(..., description="The base asset of the symbol")
    quote_asset: str = Field(..., description="The quote asset of the symbol")
    instrument_type: InstrumentType = Field(..., description="The type of instrument")

class Order(BaseModel):
    symbol: Symbol = Field(..., description="The symbol of the order")
    side: OrderSide = Field(..., description="The side of the order")
    order_type: OrderType = Field(..., description="The type of the order")
    quantity: Decimal = Field(..., description="The quantity of the order")
    price: Decimal | None = Field(None, description="The price of the order")
    time_in_force: TimeInForce = Field(..., description="The time in force of the order")
    stop_price: Decimal | None = Field(None, description="The stop price of the order")

class OrderBook(BaseModel):
    symbol: Symbol = Field(..., description="The symbol of the order book")
    bids: list[tuple[Decimal, Decimal]] = Field(..., description="The bids of the order book")
    asks: list[tuple[Decimal, Decimal]] = Field(..., description="The asks of the order book")

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
    n_trades: int|None = Field(None, description="The number of trades of the OHLCV")
    taker_buy_base_asset_volume: Decimal|None = Field(None, description="The taker buy base asset volume of the OHLCV")
    taker_buy_quote_asset_volume: Decimal|None = Field(None, description="The taker buy quote asset volume of the OHLCV")

class Trade(BaseModel):
    id: int = Field(..., description="The id of the trade")
    symbol: Symbol = Field(..., description="The symbol of the trade")
    price: Decimal = Field(..., description="The price of the trade")
    quantity: Decimal = Field(..., description="The quantity of the trade")
    quote_quantity: Decimal = Field(..., description="The quote quantity of the trade")
    time: int = Field(..., description="The time of the trade")
    side: OrderSide = Field(..., description="The side of the trade")

