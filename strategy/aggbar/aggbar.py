from solvexity.model.trade import Trade
from solvexity.model.bar import Bar
from solvexity.model.shared import Side
from enum import Enum


import logging
logger = logging.getLogger(__name__)

class BarType(Enum):
    TIME_BAR = "TimeBar"
    TICK_BAR = "TickBar"
    BASE_VOLUME_BAR = "BaseVolumeBar"
    QUOTE_VOLUME_BAR = "QuoteVolumeBar"

    

class AggBar:
    def __init__(self, buf_size: int, reference_cutoff: int, bar_type: BarType):
        self.buf_size = buf_size
        self.bar_type = bar_type
        self.bar_ref_cutoff = reference_cutoff # Different type represents different reference cutoff
        self.method_dict = {
            BarType.TIME_BAR: self.on_time_bar,
            BarType.TICK_BAR: self.on_tick_bar,
            BarType.BASE_VOLUME_BAR: self.on_base_volume_bar,
            BarType.QUOTE_VOLUME_BAR: self.on_quote_volume_bar,
        }
        self.on_trade_aggregation = self.method_dict[bar_type]

        self._accumulator = 0
        self._reference_index = -1
        self._finished_bars = 0
        self.bars: list[Bar|None] = [None for _ in range(buf_size)]

    async def on_trade(self, trade: Trade):
        # logger.info(f"On trade: {trade}")
        try:
            self.on_trade_aggregation(trade)
        except AttributeError as e:
            logger.error(f"AttributeError on trade: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Exception on trade: {e}", exc_info=True)
            raise


    def on_time_bar(self, trade: Trade):
        self._accumulator = trade.timestamp
        next_reference_index = int(self._accumulator // self.bar_ref_cutoff)
        if next_reference_index == self._reference_index:
            self.bars[self._reference_index % self.buf_size] += trade
        elif next_reference_index > self._reference_index:
            self.bars[next_reference_index % self.buf_size] = Bar.from_trade(trade)
            self.bars[next_reference_index % self.buf_size].open_time = next_reference_index * self.bar_ref_cutoff
            if bar := self.bars[self._reference_index % self.buf_size]:
                bar.enclose(next_reference_index * self.bar_ref_cutoff - 1)
                logger.info(f"Finished {self._finished_bars}'th time bar: {bar}")
                self._finished_bars += 1
            self._reference_index = next_reference_index
                    
        else:
            logger.warning(f"Invalid reference index: {self._reference_index} and next reference index: {next_reference_index}")

    def on_tick_bar(self, trade: Trade):
        self._accumulator = trade.id
        next_reference_index = int(self._accumulator // self.bar_ref_cutoff)
        if next_reference_index == self._reference_index:
            self.bars[self._reference_index % self.buf_size] += trade
        elif next_reference_index > self._reference_index:
            self.bars[next_reference_index % self.buf_size] = Bar.from_trade(trade)
            if bar := self.bars[self._reference_index % self.buf_size]:
                bar.enclose(trade.timestamp)
                logger.info(f"Finished {self._finished_bars}'th tick bar: {bar}")
                self._finished_bars += 1
            self._reference_index = next_reference_index
            
        else:
            logger.warning(f"Invalid reference index: {self._reference_index} and next reference index: {next_reference_index}")

    def on_base_volume_bar(self, trade: Trade):
        def split_trade_by_base_volume(accumulator: float, cutoff: float, trade: Trade) -> list[Trade]:
            fragments = []
            # Use more precise calculation to avoid floating point errors
            remaining_volume = trade.quantity
            while abs(remaining_volume) > 1e-10:
            remainder = accumulator % cutoff
            if abs(remainder) > 1e-10:
                volume -= min(remainder, volume)

            
            
            
            # First fragment fills the gap to complete current bar
            if remaining <= gap + 1e-10:  # Add small epsilon for floating point comparison
                # Trade fits completely in current bar
                fragments.append(trade)
                return fragments
            
            # Create fragment to fill the gap
            fragment = trade.model_copy(deep=False)
            fragment.quantity = gap
            fragments.append(fragment)
            remaining -= gap
            
            # Create full cutoff fragments for complete bars
            while remaining >= cutoff - 1e-10:  # Use epsilon for comparison
                fragment = trade.model_copy(deep=False)
                fragment.quantity = cutoff
                fragments.append(fragment)
                remaining -= cutoff
            
            # Create final fragment for remainder
            if remaining > 1e-10:  # Only create fragment if remainder is significant
                fragment = trade.model_copy(deep=False)
                fragment.quantity = remaining
                fragments.append(fragment)
                
            return fragments

        trade_fragments = split_trade_by_base_volume(self._accumulator, self.bar_ref_cutoff, trade)

        for fragment in trade_fragments:
            # Add fragment to current bar
            if not self.bars[self._reference_index % self.buf_size]:
                self.bars[self._reference_index % self.buf_size] = Bar.from_trade(fragment)
            else:
                self.bars[self._reference_index % self.buf_size] += fragment
            
            self._accumulator += fragment.quantity
            next_reference_index = int(self._accumulator // self.bar_ref_cutoff)
            
            if next_reference_index > self._reference_index:
                # Current bar is now complete
                bar = self.bars[self._reference_index % self.buf_size]
                if bar:
                    # Ensure exact volume for completed bars and proportionally adjust taker volumes
                    if abs(bar.volume - self.bar_ref_cutoff) > 1e-10:
                        # Calculate the correction ratio
                        correction_ratio = self.bar_ref_cutoff / bar.volume if bar.volume > 0 else 1.0
                        
                        # Proportionally adjust all volumes to maintain consistency
                        bar.taker_buy_base_asset_volume *= correction_ratio
                        bar.taker_buy_quote_asset_volume *= correction_ratio
                        bar.quote_volume *= correction_ratio
                        bar.volume = self.bar_ref_cutoff
                    
                    bar.enclose(fragment.timestamp)
                    logger.info(f"Finished {self._finished_bars}'th base volume bar: {bar}")
                    self._finished_bars += 1
                
                # Move to next bar
                self._reference_index = next_reference_index


    def on_quote_volume_bar(self, trade: Trade):
        self._accumulator += trade.price * trade.quantity
        next_reference_index = int(self._accumulator // self.bar_ref_cutoff)
        if next_reference_index == self._reference_index:
            self.bars[self._reference_index % self.buf_size] += trade
        elif next_reference_index > self._reference_index:
            remainder = self._accumulator % self.bar_ref_cutoff
            trade_left = trade.model_copy(deep=False)
            trade_right = trade.model_copy(deep=False)
            trade_left.quantity = remainder / trade.price
            trade_right.quantity = trade.quantity - trade_left.quantity
            if bar := self.bars[self._reference_index % self.buf_size]:
                bar += trade_left
                bar.next_id = trade_right.id
                bar.enclose(trade.timestamp)
                logger.info(f"Finished {self._finished_bars}'th quote volume bar: {bar}")
                self._finished_bars += 1
            self.bars[next_reference_index % self.buf_size] = Bar.from_trade(trade_right)
            self._reference_index = next_reference_index
        else:
            logger.warning(f"Invalid reference index: {self._reference_index} and next reference index: {next_reference_index}")