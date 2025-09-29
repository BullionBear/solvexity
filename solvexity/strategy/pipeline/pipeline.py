from solvexity.model.trade import Trade
from solvexity.toolbox.aggregator import (
    BarType, TimeBarAggregator, TickBarAggregator, BaseVolumeBarAggregator, QuoteVolumeBarAggregator
)

def get_aggregator(bar_type: BarType, buf_size: int, reference_cutoff: int|float):
    if bar_type == BarType.TIME:
        return TimeBarAggregator(buf_size, reference_cutoff)
    elif bar_type == BarType.TICK:
        return TickBarAggregator(buf_size, reference_cutoff)
    elif bar_type == BarType.BASE_VOLUME:
        return BaseVolumeBarAggregator(buf_size, reference_cutoff)
    elif bar_type == BarType.QUOTE_VOLUME:
        return QuoteVolumeBarAggregator(buf_size, reference_cutoff)

class Pipeline:
    def __init__(self, bar_type: BarType, buf_size: int, reference_cutoff: int|float):
        self.trade_id = 0
        self.aggregator = get_aggregator(bar_type, buf_size, reference_cutoff)

    async def on_trade(self, trade: Trade):
        if trade.id == 0:
            self.trade_id = trade.id
        if trade.id != self.trade_id + 1:
            self.aggregator.reset()
            self.trade_id = trade.id
        self.aggregator.on_trade(trade)
