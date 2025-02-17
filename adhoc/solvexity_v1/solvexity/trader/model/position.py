from pydantic import BaseModel


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