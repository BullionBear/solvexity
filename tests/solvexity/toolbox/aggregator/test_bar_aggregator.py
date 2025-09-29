import pytest
from unittest.mock import patch
import logging

from solvexity.toolbox.aggregator.bar_aggregator import (
    TimeBarAggregator,
    TickBarAggregator,
    BaseVolumeBarAggregator,
    QuoteVolumeBarAggregator
)
from solvexity.model.trade import Trade
from solvexity.model.bar import Bar
from solvexity.model.shared import Symbol, Exchange, Instrument, Side


@pytest.fixture
def sample_trade():
    """Create a sample trade for testing"""
    return Trade(
        id=1,
        exchange=Exchange.EXCHANGE_BINANCE,
        instrument=Instrument.INSTRUMENT_SPOT,
        symbol=Symbol(base="BTC", quote="USDT"),
        side=Side.SIDE_BUY,
        price=50000.0,
        quantity=0.1,
        timestamp=1000
    )


@pytest.fixture
def sample_trades():
    """Create multiple sample trades for testing"""
    return [
        Trade(
            id=1,
            exchange=Exchange.EXCHANGE_BINANCE,
            instrument=Instrument.INSTRUMENT_SPOT,
            symbol=Symbol(base="BTC", quote="USDT"),
            side=Side.SIDE_BUY,
            price=50000.0,
            quantity=0.1,
            timestamp=1000
        ),
        Trade(
            id=2,
            exchange=Exchange.EXCHANGE_BINANCE,
            instrument=Instrument.INSTRUMENT_SPOT,
            symbol=Symbol(base="BTC", quote="USDT"),
            side=Side.SIDE_SELL,
            price=50100.0,
            quantity=0.05,
            timestamp=1500
        ),
        Trade(
            id=3,
            exchange=Exchange.EXCHANGE_BINANCE,
            instrument=Instrument.INSTRUMENT_SPOT,
            symbol=Symbol(base="BTC", quote="USDT"),
            side=Side.SIDE_BUY,
            price=49900.0,
            quantity=0.2,
            timestamp=2000
        )
    ]


class TestTimeBarAggregator:
    """Test cases for TimeBarAggregator"""

    def test_init(self):
        """Test TimeBarAggregator initialization"""
        aggregator = TimeBarAggregator(buf_size=10, reference_cutoff=1000)
        assert aggregator.buf_size == 10
        assert aggregator.reference_cutoff == 1000
        assert len(aggregator.bars) == 10
        assert all(bar is None for bar in aggregator.bars)
        assert aggregator.reference_index == -1
        assert aggregator.finished_bars == 0

    def test_reset(self):
        """Test reset functionality"""
        aggregator = TimeBarAggregator(buf_size=5, reference_cutoff=1000)
        aggregator.reference_index = 2
        aggregator.finished_bars = 3
        aggregator.bars[0] = "some_bar"
        
        aggregator.reset()
        
        assert aggregator.reference_index == -1
        assert aggregator.finished_bars == 0
        assert all(bar is None for bar in aggregator.bars)

    @patch('solvexity.toolbox.aggregator.bar_aggregator.logger')
    def test_first_trade_creates_bar(self, mock_logger, sample_trade):
        """Test that first trade creates a new bar"""
        aggregator = TimeBarAggregator(buf_size=5, reference_cutoff=1000)
        
        aggregator.on_trade(sample_trade)
        
        # Should create a bar at index 1 (timestamp 1000 // 1000 = 1)
        bar = aggregator.bars[1]
        assert bar is not None
        assert bar.open == 50000.0
        assert bar.high == 50000.0
        assert bar.low == 50000.0
        assert bar.close == 50000.0
        assert bar.volume == 0.1
        assert bar.open_time == 1000  # 1 * 1000
        assert aggregator.reference_index == 1
        assert aggregator.finished_bars == 0

    @patch('solvexity.toolbox.aggregator.bar_aggregator.logger')
    def test_trades_in_same_time_window(self, mock_logger, sample_trades):
        """Test trades within the same time window are accumulated"""
        aggregator = TimeBarAggregator(buf_size=5, reference_cutoff=1000)
        
        # First trade at timestamp 1000
        aggregator.on_trade(sample_trades[0])
        
        # Second trade at timestamp 1500 (same time window: 1500 // 1000 = 1)
        trade2 = sample_trades[1]
        trade2.timestamp = 1500
        aggregator.on_trade(trade2)
        
        bar = aggregator.bars[1]
        assert bar is not None
        assert bar.volume == pytest.approx(0.15, rel=1e-10)  # 0.1 + 0.05
        assert bar.high == 50100.0  # max(50000, 50100)
        assert bar.low == 50000.0   # min(50000, 50100)
        assert bar.close == 50100.0
        assert bar.number_of_trades == 2

    @patch('solvexity.toolbox.aggregator.bar_aggregator.logger')
    def test_trades_in_different_time_windows(self, mock_logger, sample_trades):
        """Test trades in different time windows create separate bars"""
        aggregator = TimeBarAggregator(buf_size=5, reference_cutoff=1000)
        
        # First trade at timestamp 1000 (window 1)
        aggregator.on_trade(sample_trades[0])
        
        # Second trade at timestamp 2000 (window 2)
        trade2 = sample_trades[1]
        trade2.timestamp = 2000
        aggregator.on_trade(trade2)
        
        # First bar should be finished
        bar1 = aggregator.bars[1]
        assert bar1 is not None
        assert bar1.is_closed
        assert bar1.close_time == 1999  # next_reference_index * cutoff - 1
        
        # Second bar should be created
        bar2 = aggregator.bars[2]
        assert bar2 is not None
        assert not bar2.is_closed
        assert bar2.open == 50100.0
        
        assert aggregator.finished_bars == 1
        assert aggregator.reference_index == 2

    @patch('solvexity.toolbox.aggregator.bar_aggregator.logger')
    def test_circular_buffer(self, mock_logger, sample_trade):
        """Test circular buffer functionality"""
        aggregator = TimeBarAggregator(buf_size=3, reference_cutoff=1000)
        
        # Create bars that will wrap around the buffer
        for i in range(5):
            trade = sample_trade.model_copy(deep=True)
            trade.timestamp = i * 1000
            trade.id = i + 1
            aggregator.on_trade(trade)
        
        # Should have bars at indices 0, 1, 2 (wrapped around)
        assert aggregator.bars[0] is not None  # timestamp 3000
        assert aggregator.bars[1] is not None  # timestamp 4000
        assert aggregator.bars[2] is not None  # timestamp 2000 (oldest)

    @patch('solvexity.toolbox.aggregator.bar_aggregator.logger')
    def test_invalid_reference_index_warning(self, mock_logger, sample_trade):
        """Test warning for invalid reference index"""
        aggregator = TimeBarAggregator(buf_size=5, reference_cutoff=1000)
        
        # Manually set an invalid state
        aggregator.reference_index = 5
        sample_trade.timestamp = 1000  # This would give index 1
        
        aggregator.on_trade(sample_trade)
        
        mock_logger.warning.assert_called_once()


class TestTickBarAggregator:
    """Test cases for TickBarAggregator"""

    def test_init(self):
        """Test TickBarAggregator initialization"""
        aggregator = TickBarAggregator(buf_size=10, reference_cutoff=100)
        assert aggregator.buf_size == 10
        assert aggregator.reference_cutoff == 100
        assert len(aggregator.bars) == 10
        assert all(bar is None for bar in aggregator.bars)
        assert aggregator.reference_index == -1
        assert aggregator.finished_bars == 0

    def test_reset(self):
        """Test reset functionality"""
        aggregator = TickBarAggregator(buf_size=5, reference_cutoff=100)
        aggregator.reference_index = 2
        aggregator.finished_bars = 3
        aggregator.bars[0] = "some_bar"
        
        aggregator.reset()
        
        assert aggregator.reference_index == -1
        assert aggregator.finished_bars == 0
        assert all(bar is None for bar in aggregator.bars)

    @patch('solvexity.toolbox.aggregator.bar_aggregator.logger')
    def test_first_trade_creates_bar(self, mock_logger, sample_trade):
        """Test that first trade creates a new bar"""
        aggregator = TickBarAggregator(buf_size=5, reference_cutoff=100)
        
        aggregator.on_trade(sample_trade)
        
        # Should create a bar at index 0 (id 1 // 100 = 0)
        bar = aggregator.bars[0]
        assert bar is not None
        assert bar.open == 50000.0
        assert bar.volume == 0.1
        assert aggregator.reference_index == 0
        assert aggregator.finished_bars == 0

    @patch('solvexity.toolbox.aggregator.bar_aggregator.logger')
    def test_trades_in_same_tick_window(self, mock_logger, sample_trades):
        """Test trades within the same tick window are accumulated"""
        aggregator = TickBarAggregator(buf_size=5, reference_cutoff=100)
        
        # First trade with id 1
        aggregator.on_trade(sample_trades[0])
        
        # Second trade with id 50 (same tick window: 50 // 100 = 0)
        trade2 = sample_trades[1]
        trade2.id = 50
        aggregator.on_trade(trade2)
        
        bar = aggregator.bars[0]
        assert bar is not None
        assert bar.volume == pytest.approx(0.15, rel=1e-10)  # 0.1 + 0.05
        assert bar.number_of_trades == 2

    @patch('solvexity.toolbox.aggregator.bar_aggregator.logger')
    def test_trades_in_different_tick_windows(self, mock_logger, sample_trades):
        """Test trades in different tick windows create separate bars"""
        aggregator = TickBarAggregator(buf_size=5, reference_cutoff=100)
        
        # First trade with id 1 (window 0)
        aggregator.on_trade(sample_trades[0])
        
        # Second trade with id 150 (window 1)
        trade2 = sample_trades[1]
        trade2.id = 150
        aggregator.on_trade(trade2)
        
        # First bar should be finished
        bar1 = aggregator.bars[0]
        assert bar1 is not None
        assert bar1.is_closed
        
        # Second bar should be created
        bar2 = aggregator.bars[1]
        assert bar2 is not None
        assert not bar2.is_closed
        
        assert aggregator.finished_bars == 1
        assert aggregator.reference_index == 1


class TestBaseVolumeBarAggregator:
    """Test cases for BaseVolumeBarAggregator"""

    def test_init(self):
        """Test BaseVolumeBarAggregator initialization"""
        aggregator = BaseVolumeBarAggregator(buf_size=10, reference_cutoff=1.0)
        assert aggregator.buf_size == 10
        assert aggregator.reference_cutoff == 1.0
        assert len(aggregator.bars) == 10
        assert all(bar is None for bar in aggregator.bars)
        assert aggregator.reference_index == 0
        assert aggregator.finished_bars == 0

    def test_reset(self):
        """Test reset functionality"""
        aggregator = BaseVolumeBarAggregator(buf_size=5, reference_cutoff=1.0)
        aggregator.reference_index = 2
        aggregator.finished_bars = 3
        aggregator.bars[0] = "some_bar"
        
        aggregator.reset()
        
        assert aggregator.reference_index == 0
        assert aggregator.finished_bars == 0
        assert all(bar is None for bar in aggregator.bars)

    @patch('solvexity.toolbox.aggregator.bar_aggregator.logger')
    def test_trade_exactly_fills_bar(self, mock_logger, sample_trade):
        """Test trade that exactly fills a bar"""
        aggregator = BaseVolumeBarAggregator(buf_size=5, reference_cutoff=0.1)
        sample_trade.quantity = 0.1
        
        aggregator.on_trade(sample_trade)
        
        bar = aggregator.bars[0]
        assert bar is not None
        assert bar.is_closed
        assert bar.volume == 0.1
        assert aggregator.finished_bars == 1
        assert aggregator.reference_index == 1

    @patch('solvexity.toolbox.aggregator.bar_aggregator.logger')
    def test_trade_partially_fills_bar(self, mock_logger, sample_trade):
        """Test trade that partially fills a bar"""
        aggregator = BaseVolumeBarAggregator(buf_size=5, reference_cutoff=1.0)
        sample_trade.quantity = 0.3
        
        aggregator.on_trade(sample_trade)
        
        bar = aggregator.bars[0]
        assert bar is not None
        assert not bar.is_closed
        assert bar.volume == 0.3
        assert aggregator.finished_bars == 0
        assert aggregator.reference_index == 0

    @patch('solvexity.toolbox.aggregator.bar_aggregator.logger')
    def test_trade_overflows_bar(self, mock_logger, sample_trade):
        """Test trade that overflows a bar"""
        aggregator = BaseVolumeBarAggregator(buf_size=5, reference_cutoff=0.1)
        sample_trade.quantity = 0.15  # More than the cutoff
        
        aggregator.on_trade(sample_trade)
        
        # First bar should be finished with 0.1 volume
        bar1 = aggregator.bars[0]
        assert bar1 is not None
        assert bar1.is_closed
        assert bar1.volume == 0.1
        
        # Second bar should be created with remaining 0.05 volume
        bar2 = aggregator.bars[1]
        assert bar2 is not None
        assert not bar2.is_closed
        assert bar2.volume == pytest.approx(0.05, rel=1e-10)
        
        assert aggregator.finished_bars == 1
        assert aggregator.reference_index == 1

    @patch('solvexity.toolbox.aggregator.bar_aggregator.logger')
    def test_multiple_trades_accumulate(self, mock_logger, sample_trades):
        """Test multiple trades accumulating in the same bar"""
        aggregator = BaseVolumeBarAggregator(buf_size=5, reference_cutoff=1.0)
        
        # Set quantities that won't overflow
        sample_trades[0].quantity = 0.3
        sample_trades[1].quantity = 0.2
        sample_trades[2].quantity = 0.4
        
        for trade in sample_trades:
            aggregator.on_trade(trade)
        
        bar = aggregator.bars[0]
        assert bar is not None
        assert bar.volume == 0.9  # 0.3 + 0.2 + 0.4
        assert bar.number_of_trades == 3
        assert not bar.is_closed


class TestQuoteVolumeBarAggregator:
    """Test cases for QuoteVolumeBarAggregator"""

    def test_init(self):
        """Test QuoteVolumeBarAggregator initialization"""
        aggregator = QuoteVolumeBarAggregator(buf_size=10, reference_cutoff=1000.0)
        assert aggregator.buf_size == 10
        assert aggregator.reference_cutoff == 1000.0
        assert len(aggregator.bars) == 10
        assert all(bar is None for bar in aggregator.bars)
        assert aggregator.reference_index == 0
        assert aggregator.finished_bars == 0

    def test_reset(self):
        """Test reset functionality"""
        aggregator = QuoteVolumeBarAggregator(buf_size=5, reference_cutoff=1000.0)
        aggregator.reference_index = 2
        aggregator.finished_bars = 3
        aggregator.bars[0] = "some_bar"
        
        aggregator.reset()
        
        assert aggregator.reference_index == 0
        assert aggregator.finished_bars == 0
        assert all(bar is None for bar in aggregator.bars)

    @patch('solvexity.toolbox.aggregator.bar_aggregator.logger')
    def test_trade_exactly_fills_quote_volume(self, mock_logger, sample_trade):
        """Test trade that exactly fills a quote volume bar"""
        aggregator = QuoteVolumeBarAggregator(buf_size=5, reference_cutoff=5000.0)  # $5000 quote volume
        sample_trade.quantity = 0.1  # 0.1 * 50000 = $5000
        
        aggregator.on_trade(sample_trade)
        
        bar = aggregator.bars[0]
        assert bar is not None
        assert bar.is_closed
        assert bar.quote_volume == 5000.0
        assert aggregator.finished_bars == 1
        assert aggregator.reference_index == 1

    @patch('solvexity.toolbox.aggregator.bar_aggregator.logger')
    def test_trade_partially_fills_quote_volume(self, mock_logger, sample_trade):
        """Test trade that partially fills a quote volume bar"""
        aggregator = QuoteVolumeBarAggregator(buf_size=5, reference_cutoff=10000.0)  # $10000 quote volume
        sample_trade.quantity = 0.1  # 0.1 * 50000 = $5000 (partial)
        
        aggregator.on_trade(sample_trade)
        
        bar = aggregator.bars[0]
        assert bar is not None
        assert not bar.is_closed
        assert bar.quote_volume == 5000.0
        assert aggregator.finished_bars == 0
        assert aggregator.reference_index == 0

    @patch('solvexity.toolbox.aggregator.bar_aggregator.logger')
    def test_trade_overflows_quote_volume(self, mock_logger, sample_trade):
        """Test trade that overflows a quote volume bar"""
        aggregator = QuoteVolumeBarAggregator(buf_size=5, reference_cutoff=5000.0)  # $5000 quote volume
        sample_trade.quantity = 0.15  # 0.15 * 50000 = $7500 (overflows)
        
        aggregator.on_trade(sample_trade)
        
        # First bar should be finished with $5000 quote volume
        bar1 = aggregator.bars[0]
        assert bar1 is not None
        assert bar1.is_closed
        assert bar1.quote_volume == 5000.0
        
        # Second bar should be created with remaining $2500 quote volume
        bar2 = aggregator.bars[1]
        assert bar2 is not None
        assert not bar2.is_closed
        assert bar2.quote_volume == pytest.approx(2500.0, rel=1e-10)
        
        assert aggregator.finished_bars == 1
        assert aggregator.reference_index == 1


class TestEdgeCases:
    """Test edge cases for all aggregators"""

    def test_zero_quantity_trade(self, sample_trade):
        """Test handling of zero quantity trades"""
        sample_trade.quantity = 0.0
        
        # TimeBarAggregator should handle zero quantity
        time_agg = TimeBarAggregator(buf_size=5, reference_cutoff=1000)
        time_agg.on_trade(sample_trade)
        
        # TickBarAggregator should handle zero quantity
        tick_agg = TickBarAggregator(buf_size=5, reference_cutoff=100)
        tick_agg.on_trade(sample_trade)
        
        # Volume aggregators should handle zero quantity
        base_vol_agg = BaseVolumeBarAggregator(buf_size=5, reference_cutoff=1.0)
        base_vol_agg.on_trade(sample_trade)
        
        quote_vol_agg = QuoteVolumeBarAggregator(buf_size=5, reference_cutoff=1000.0)
        quote_vol_agg.on_trade(sample_trade)

    def test_negative_quantity_trade(self, sample_trade):
        """Test handling of negative quantity trades"""
        sample_trade.quantity = -0.1
        
        # All aggregators should handle negative quantities
        time_agg = TimeBarAggregator(buf_size=5, reference_cutoff=1000)
        time_agg.on_trade(sample_trade)
        
        tick_agg = TickBarAggregator(buf_size=5, reference_cutoff=100)
        tick_agg.on_trade(sample_trade)
        
        base_vol_agg = BaseVolumeBarAggregator(buf_size=5, reference_cutoff=1.0)
        base_vol_agg.on_trade(sample_trade)
        
        quote_vol_agg = QuoteVolumeBarAggregator(buf_size=5, reference_cutoff=1000.0)
        quote_vol_agg.on_trade(sample_trade)

    def test_very_small_quantity_trade(self, sample_trade):
        """Test handling of very small quantity trades"""
        sample_trade.quantity = 1e-15  # Very small quantity
        
        # Volume aggregators should handle very small quantities
        base_vol_agg = BaseVolumeBarAggregator(buf_size=5, reference_cutoff=1.0)
        base_vol_agg.on_trade(sample_trade)
        
        quote_vol_agg = QuoteVolumeBarAggregator(buf_size=5, reference_cutoff=1000.0)
        quote_vol_agg.on_trade(sample_trade)

    def test_large_buffer_size(self, sample_trade):
        """Test aggregators with large buffer sizes"""
        large_buf_size = 1000
        
        time_agg = TimeBarAggregator(buf_size=large_buf_size, reference_cutoff=1000)
        assert len(time_agg.bars) == large_buf_size
        
        tick_agg = TickBarAggregator(buf_size=large_buf_size, reference_cutoff=100)
        assert len(tick_agg.bars) == large_buf_size
        
        base_vol_agg = BaseVolumeBarAggregator(buf_size=large_buf_size, reference_cutoff=1.0)
        assert len(base_vol_agg.bars) == large_buf_size
        
        quote_vol_agg = QuoteVolumeBarAggregator(buf_size=large_buf_size, reference_cutoff=1000.0)
        assert len(quote_vol_agg.bars) == large_buf_size

    def test_single_element_buffer(self, sample_trade):
        """Test aggregators with single element buffer"""
        time_agg = TimeBarAggregator(buf_size=1, reference_cutoff=1000)
        time_agg.on_trade(sample_trade)
        
        # Should work with buffer size 1
        assert time_agg.bars[0] is not None
