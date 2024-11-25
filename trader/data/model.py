from pydantic import BaseModel

class Trade(BaseModel):
    symbol: str
    id: int
    order_id: int
    order_list_id: int
    price: float
    qty: float
    quote_qty: float
    commission: float
    commission_asset: str
    time: int
    is_buyer: bool
    is_maker: bool
    is_best_match: bool

    @classmethod
    def from_rest(cls, data: dict):
        return cls(
            symbol=data["symbol"],
            id=data["id"],
            order_id=data["orderId"],
            order_list_id=data["orderListId"],
            price=float(data["price"]),
            qty=float(data["qty"]),
            quote_qty=float(data["quoteQty"]),
            commission=float(data["commission"]),
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
            price=float(data['price']),
            qty=float(data['qty']),
            quote_qty=float(data['quoteQty']),
            commission=float(data['commission']),
            commission_asset=data['commissionAsset'],
            time=data['time'],
            is_buyer=data['buyer'],
            is_maker=data['maker'],
            is_best_match=True  # Assuming True; adjust based on data if available
        )



class KLine(BaseModel):
    interval: str
    open_time: int
    close_time: int
    event_time: int
    open: float
    high: float
    low: float
    close: float
    number_of_trades: int
    base_asset_volume: float
    quote_asset_volume: float
    taker_buy_base_asset_volume: float
    taker_buy_quote_asset_volume: float
    is_closed: bool

    @classmethod
    def from_ws(cls, data: dict, event_time: int):
        return cls(
            interval=data["i"],
            open_time=data["t"],
            close_time=data["T"],
            event_time=event_time,
            open=float(data["o"]),
            high=float(data["h"]),
            low=float(data["l"]),
            close=float(data["c"]),
            number_of_trades=data["n"],
            base_asset_volume=float(data["v"]),
            quote_asset_volume=float(data["q"]),
            taker_buy_base_asset_volume=float(data["V"]),
            taker_buy_quote_asset_volume=float(data["Q"]),
            is_closed=data["x"]
        )
    
    @classmethod
    def from_rest(cls, data: list, granular: str):
        return cls(
            interval=granular,
            open_time=int(data[0]),
            close_time=int(data[6]),
            event_time=int(data[6]),
            open=float(data[1]),
            high=float(data[2]),
            low=float(data[3]),
            close=float(data[4]),
            number_of_trades=int(data[8]),
            base_asset_volume=float(data[5]),
            quote_asset_volume=float(data[7]),
            taker_buy_base_asset_volume=float(data[9]),
            taker_buy_quote_asset_volume=float(data[10]),
            is_closed=True
        )


class Position(BaseModel):
    symbol: str
    position_side: str
    position_amt: float
    entry_price: float
    break_even_price: float
    mark_price: float
    unrealized_profit: float
    liquidation_price: float
    isolated_margin: float
    notional: float
    margin_asset: str
    isolated_wallet: float
    initial_margin: float
    maint_margin: float
    position_initial_margin: float
    open_order_initial_margin: float
    adl: int
    bid_notional: float
    ask_notional: float
    update_time: int

    @classmethod
    def from_perp_rest(cls, data: dict) -> 'Position':
        """
        Create a Position instance from a perpetual REST API response.
        """
        return cls(
            symbol=data['symbol'],
            position_side=data['positionSide'],
            position_amt=float(data['positionAmt']),
            entry_price=float(data['entryPrice']),
            break_even_price=float(data['breakEvenPrice']),
            mark_price=float(data['markPrice']),
            unrealized_profit=float(data['unRealizedProfit']),
            liquidation_price=float(data['liquidationPrice']),
            isolated_margin=float(data['isolatedMargin']),
            notional=float(data['notional']),
            margin_asset=data['marginAsset'],
            isolated_wallet=float(data['isolatedWallet']),
            initial_margin=float(data['initialMargin']),
            maint_margin=float(data['maintMargin']),
            position_initial_margin=float(data['positionInitialMargin']),
            open_order_initial_margin=float(data['openOrderInitialMargin']),
            adl=int(data['adl']),
            bid_notional=float(data['bidNotional']),
            ask_notional=float(data['askNotional']),
            update_time=data['updateTime']
        )