from solvexity.connector.types import Trade, Symbol, InstrumentType, OrderSide
from pydantic import BaseModel, Field
from decimal import Decimal
from influxdb_client import Point

class TradePayload(BaseModel):
    id: int = Field(..., description="The id of the trade")
    symbol: str = Field(..., description="The symbol of the trade, e.g. BTC-USDT-SPOT")
    price: Decimal = Field(..., description="The price of the trade")
    quantity: Decimal = Field(..., description="The quantity of the trade")
    timestamp: int = Field(..., description="The time of the trade")
    side: str = Field(..., description="The side of the trade")

    @classmethod
    def from_trade(cls, trade: Trade) -> "TradePayload":
        return cls(
            id=trade.id,
            symbol=f"{trade.symbol.base_currency}-{trade.symbol.quote_currency}-{trade.symbol.instrument_type.value}",
            price=trade.price,
            quantity=trade.quantity,
            timestamp=trade.timestamp,
            side=trade.side.value,
        )

    def to_trade(self) -> Trade:
        base_currency, quote_currency, instrument_type = self.symbol.split("-")
        instrument = InstrumentType(instrument_type)
        return Trade(
            id=self.id,
            symbol=Symbol(base_currency=base_currency, quote_currency=quote_currency, instrument_type=instrument),
            price=self.price,
            quantity=self.quantity,
            timestamp=self.timestamp,
            side=OrderSide(self.side),
        )
    
    @classmethod
    def from_point(cls, point: Point) -> "TradePayload":
        base_currency, quote_currency, instrument_type = point.get_tag("symbol").split("-")
        return cls(
            id=point.get_field("id"),
            symbol=f"{base_currency}-{quote_currency}-{instrument_type}",
            price=point.get_field("price"),
            quantity=point.get_field("quantity"),
            timestamp=point.get_field("timestamp"),
            side=point.get_field("side"),
        )
    
    def to_point(self) -> Point:
        return Point("trades") \
            .tag("symbol", self.symbol) \
            .field("side", self.side) \
            .field("price", self.price) \
            .field("quantity", self.quantity) \
            .field("timestamp", self.timestamp) \
            .time(self.timestamp, write_precision='ms')
    

    