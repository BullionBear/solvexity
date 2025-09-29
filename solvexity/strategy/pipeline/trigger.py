from solvexity.model.trade import Trade
from solvexity.toolbox.aggregator import (
    BarType, TimeBarAggregator, TickBarAggregator, BaseVolumeBarAggregator, QuoteVolumeBarAggregator
)
from solvexity.eventbus.eventbus import EventBus

def get_aggregator(bar_type: BarType, buf_size: int, reference_cutoff: int|float):
    if bar_type == BarType.TIME:
        return TimeBarAggregator(buf_size, reference_cutoff)
    elif bar_type == BarType.TICK:
        return TickBarAggregator(buf_size, reference_cutoff)
    elif bar_type == BarType.BASE_VOLUME:
        return BaseVolumeBarAggregator(buf_size, reference_cutoff)
    elif bar_type == BarType.QUOTE_VOLUME:
        return QuoteVolumeBarAggregator(buf_size, reference_cutoff)

class DataframeTrigger:
    def __init__(self, bar_type: BarType, buf_size: int, reference_cutoff: int|float, eventbus: EventBus):
        self.trade_id = 0
        self.aggregator = get_aggregator(bar_type, buf_size, reference_cutoff)
        self.eventbus = eventbus

    async def on_trade(self, trade: Trade):
        # Initialize trade_id on first trade
        if self.trade_id == 0:
            self.trade_id = trade.id
        # Only reset if trade ID goes backwards (invalid sequence)
        elif trade.id < self.trade_id:
            self.aggregator.reset()
            self.trade_id = trade.id
        else:
            # Update trade_id to latest trade
            self.trade_id = trade.id
        
        self.aggregator.on_trade(trade)
