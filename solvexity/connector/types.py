from enum import Enum
from pydantic import BaseModel, Field
from decimal import Decimal

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

