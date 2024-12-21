from pydantic import BaseModel
from typing import Literal


class Order(BaseModel):
    symbol: str
    order_id: int
    order_list_id: int  # -1 unless part of an order list
    client_order_id: str
    price: str  # Represented as string to preserve precision
    original_quantity: str  # Represented as string to preserve precision
    executed_quantity: str  # Represented as string to preserve precision
    cumulative_quote_quantity: str  # Represented as string to preserve precision
    status: Literal["NEW", "PARTIALLY_FILLED", "FILLED", "CANCELED", "PENDING_CANCEL", "REJECTED", "EXPIRED"]
    time_in_force: Literal["GTC", "IOC", "FOK"]
    order_type: Literal["LIMIT", "MARKET", "STOP_LOSS", "STOP_LOSS_LIMIT", "TAKE_PROFIT", "TAKE_PROFIT_LIMIT", "LIMIT_MAKER"]
    side: Literal["BUY", "SELL"]
    stop_price: str  # Represented as string to preserve precision
    iceberg_quantity: str  # Represented as string to preserve precision
    time: int  # Timestamp in milliseconds
    update_time: int  # Timestamp in milliseconds
    is_working: bool
    original_quote_order_quantity: str  # Represented as string to preserve precision
    working_time: int  # Timestamp in milliseconds
    self_trade_prevention_mode: Literal["NONE", "EXPIRE_TAKER", "EXPIRE_MAKER", "EXPIRE_BOTH"]

    @classmethod
    def from_rest(cls, data: dict) -> "Order":
        """
        Converts REST API response dictionary into an Order instance.

        Args:
            data (dict): REST API response.

        Returns:
            Order: An instance of the Order class.
        """
        return cls(
            symbol=data["symbol"],
            order_id=data["orderId"],
            order_list_id=data["orderListId"],
            client_order_id=data["clientOrderId"],
            price=data["price"],
            original_quantity=data["origQty"],
            executed_quantity=data["executedQty"],
            cumulative_quote_quantity=data["cummulativeQuoteQty"],
            status=data["status"],
            time_in_force=data["timeInForce"],
            order_type=data["type"],
            side=data["side"],
            stop_price=data["stopPrice"],
            iceberg_quantity=data["icebergQty"],
            time=data["time"],
            update_time=data["updateTime"],
            is_working=data["isWorking"],
            original_quote_order_quantity=data["origQuoteOrderQty"],
            working_time=data["workingTime"],
            self_trade_prevention_mode=data["selfTradePreventionMode"]
        )
    