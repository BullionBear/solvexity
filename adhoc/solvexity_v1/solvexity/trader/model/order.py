from pydantic import BaseModel
from typing import Literal
from decimal import Decimal


class Order(BaseModel):
    symbol: str
    order_id: int
    order_list_id: int
    client_order_id: str
    price: Decimal
    original_quantity: Decimal
    executed_quantity: Decimal
    cumulative_quote_quantity: Decimal
    status: Literal["NEW", "PARTIALLY_FILLED", "FILLED", "CANCELED", "PENDING_CANCEL", "REJECTED", "EXPIRED"]
    time_in_force: Literal["GTC", "IOC", "FOK"]
    order_type: Literal["LIMIT", "MARKET", "STOP_LOSS", "STOP_LOSS_LIMIT", "TAKE_PROFIT", "TAKE_PROFIT_LIMIT", "LIMIT_MAKER"]
    side: Literal["BUY", "SELL"]
    stop_price: Decimal
    iceberg_quantity: Decimal
    time: int
    update_time: int
    is_working: bool
    original_quote_order_quantity: Decimal
    working_time: int
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
            price=Decimal(data["price"]),
            original_quantity=Decimal(data["origQty"]),
            executed_quantity=Decimal(data["executedQty"]),
            cumulative_quote_quantity=Decimal(data["cummulativeQuoteQty"]),
            status=data["status"],
            time_in_force=data["timeInForce"],
            order_type=data["type"],
            side=data["side"],
            stop_price=Decimal(data["stopPrice"]),
            iceberg_quantity=Decimal(data["icebergQty"]),
            time=data["time"],
            update_time=data["updateTime"],
            is_working=data["isWorking"],
            original_quote_order_quantity=Decimal(data["origQuoteOrderQty"]),
            working_time=data["workingTime"],
            self_trade_prevention_mode=data["selfTradePreventionMode"]
        )
