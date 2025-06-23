from solvexity.connector.types import Trade, Symbol, InstrumentType, OrderSide
from pydantic import BaseModel, Field
from decimal import Decimal, ROUND_HALF_UP
from influxdb_client import Point
from influxdb_client.client.flux_table import FluxRecord
from typing import Union


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
    
    def to_point(self) -> Point:
        """Convert to InfluxDB Point with controlled decimal precision"""
        
        return Point("trades") \
            .tag("symbol", self.symbol) \
            .field("id", self.id) \
            .field("side", self.side) \
            .field("price", str(self.price)) \
            .field("quantity", str(self.quantity)) \
            .field("timestamp", self.timestamp) \
            .time(self.timestamp, write_precision='ms')
    
    @classmethod
    def from_record(cls, record: FluxRecord) -> "TradePayload":
        return cls(
            id=int(record.values.get("id")),
            symbol=record.values.get("symbol"),
            price=Decimal(record.values.get("price")),
            quantity=Decimal(record.values.get("quantity")),
            timestamp=int(record.get_time().timestamp() * 1000),
            side=record.values.get("side"),
        )

    