from pydantic import BaseModel
from decimal import Decimal


class Trade(BaseModel):
    symbol: str
    id: int
    order_id: int
    order_list_id: int
    price: Decimal
    qty: Decimal
    quote_qty: Decimal
    commission: Decimal
    commission_asset: str
    time: int
    is_buyer: bool
    is_maker: bool
    is_best_match: bool

    @classmethod
    def from_rest(cls, data: dict) -> 'Trade':
        """
        Create a Trade instance from a standard REST API response.
        """
        return cls(
            symbol=data["symbol"],
            id=data["id"],
            order_id=data["orderId"],
            order_list_id=data["orderListId"],
            price=Decimal(data["price"]),
            qty=Decimal(data["qty"]),
            quote_qty=Decimal(data["quoteQty"]),
            commission=Decimal(data["commission"]),
            commission_asset=data["commissionAsset"],
            time=data["time"],
            is_buyer=data["isBuyer"],
            is_maker=data["isMaker"],
            is_best_match=data["isBestMatch"]
        )

    @classmethod
    def from_perp_rest(cls, data: dict) -> 'Trade':
        """
        Create a Trade instance from a perpetual REST API response.
        """
        return cls(
            symbol=data['symbol'],
            id=data['id'],
            order_id=data['orderId'],
            order_list_id=0,  # Assuming it's not present in data
            price=Decimal(data['price']),
            qty=Decimal(data['qty']),
            quote_qty=Decimal(data['quoteQty']),
            commission=Decimal(data['commission']),
            commission_asset=data['commissionAsset'],
            time=data['time'],
            is_buyer=data['buyer'],
            is_maker=data['maker'],
            is_best_match=True  # Assuming True; adjust based on data if available
        )
