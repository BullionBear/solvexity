import pytest
from collections import deque
from unittest.mock import patch

from solvexity.toolbox.aggregator.bar_aggregator import TimeBarAggregator
from solvexity.model.trade import Trade
from solvexity.model.bar import Bar
from solvexity.model.shared import Symbol, Exchange, Instrument, Side


class TestTimeBarAggregator:
    """Test suite for TimeBarAggregator class"""

    @pytest.fixture
    def sample_trade(self):
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
    def aggregator(self):
        """Create a TimeBarAggregator instance for testing"""
        return TimeBarAggregator(buf_size=10, reference_cutoff=100)

    def test_initialization(self):
        """Test TimeBarAggregator initialization with different parameters"""
        # Test with default parameters
        agg = TimeBarAggregator(buf_size=5, reference_cutoff=60)
        assert agg.buf_size == 5
        assert agg.reference_cutoff == 60
        assert isinstance(agg.bars, deque)
        assert agg.bars.maxlen == 5
        assert len(agg.bars) == 0
        assert agg.accumulator == 0

        # Test with different parameters
        agg2 = TimeBarAggregator(buf_size=100, reference_cutoff=300)
        assert agg2.buf_size == 100
        assert agg2.reference_cutoff == 300
        assert agg2.bars.maxlen == 100

    def test_reset(self, aggregator, sample_trade):
        """Test reset method clears bars and accumulator"""
        # Add some data first
        aggregator.on_trade(sample_trade)
        assert len(aggregator.bars) == 1
        assert aggregator.accumulator == sample_trade.timestamp

        # Reset and verify
        aggregator.reset()
        assert len(aggregator.bars) == 0
        assert aggregator.accumulator == 0

    def test_first_trade(self, aggregator, sample_trade):
        """Test handling of first trade creates initial bar"""
        aggregator.on_trade(sample_trade)

        assert len(aggregator.bars) == 1
        assert aggregator.accumulator == sample_trade.timestamp

        bar = aggregator.bars[0]
        assert bar.symbol == sample_trade.symbol
        assert bar.start_id == sample_trade.id
        assert bar.current_id == sample_trade.id
        assert bar.open == sample_trade.price
        assert bar.high == sample_trade.price
        assert bar.low == sample_trade.price
        assert bar.close == sample_trade.price
        assert bar.volume == sample_trade.quantity
        assert bar.number_of_trades == 1
        assert bar.open_time == (sample_trade.timestamp // aggregator.reference_cutoff) * aggregator.reference_cutoff

    def test_same_timeframe_aggregation(self, aggregator, sample_trade):
        """Test trades within same timeframe are aggregated into same bar"""
        # First trade
        trade1 = sample_trade.model_copy()
        trade1.timestamp = 1000
        trade1.price = 50000.0
        trade1.quantity = 0.1
        aggregator.on_trade(trade1)

        # Second trade in same timeframe (same reference index)
        trade2 = sample_trade.model_copy()
        trade2.id = 2
        trade2.timestamp = 1050  # Still within same 100ms window
        trade2.price = 50100.0
        trade2.quantity = 0.2
        aggregator.on_trade(trade2)

        assert len(aggregator.bars) == 1
        bar = aggregator.bars[0]
        assert bar.current_id == trade2.id
        assert bar.open == trade1.price  # First trade's price
        assert bar.high == trade2.price  # Higher price
        assert bar.low == trade1.price   # Lower price
        assert bar.close == trade2.price # Last trade's price
        assert bar.volume == trade1.quantity + trade2.quantity
        assert bar.number_of_trades == 2

    def test_new_timeframe_creates_new_bar(self, aggregator, sample_trade):
        """Test trades in new timeframe create new bar and close previous"""
        # First trade
        trade1 = sample_trade.model_copy()
        trade1.timestamp = 1000
        aggregator.on_trade(trade1)

        # Second trade in new timeframe
        trade2 = sample_trade.model_copy()
        trade2.id = 2
        trade2.timestamp = 1200  # New 100ms window
        trade2.price = 51000.0
        aggregator.on_trade(trade2)

        assert len(aggregator.bars) == 2
        
        # First bar should be closed
        first_bar = aggregator.bars[0]
        assert first_bar.is_closed is True
        assert first_bar.close_time == 1199  # next_reference_index * reference_cutoff - 1

        # Second bar should be current
        second_bar = aggregator.bars[1]
        assert second_bar.is_closed is False
        assert second_bar.open_time == 1200  # New reference index * reference_cutoff
        assert second_bar.close == trade2.price

    def test_invalid_timestamp_warning(self, aggregator, sample_trade, caplog):
        """Test handling of trades with timestamps going backwards"""
        # First trade
        trade1 = sample_trade.model_copy()
        trade1.timestamp = 1000
        aggregator.on_trade(trade1)

        # Second trade with earlier timestamp (invalid)
        trade2 = sample_trade.model_copy()
        trade2.id = 2
        trade2.timestamp = 900  # Earlier than first trade
        aggregator.on_trade(trade2)

        # Should log warning
        assert "Invalid reference index" in caplog.text
        assert len(aggregator.bars) == 1  # Should not create new bar

    def test_buffer_overflow_behavior(self, sample_trade):
        """Test behavior when buffer size is exceeded"""
        # Create aggregator with small buffer
        agg = TimeBarAggregator(buf_size=2, reference_cutoff=100)

        # Add trades that will exceed buffer
        for i in range(5):
            trade = sample_trade.model_copy()
            trade.id = i + 1
            trade.timestamp = 1000 + (i * 200)  # Each in different timeframe
            agg.on_trade(trade)

        # Should only keep last 2 bars due to maxlen
        assert len(agg.bars) == 2
        assert agg.bars[0].start_id == 4  # Second to last trade
        assert agg.bars[1].start_id == 5  # Last trade

    def test_reference_cutoff_calculation(self, sample_trade):
        """Test that reference cutoff calculations are correct"""
        agg = TimeBarAggregator(buf_size=10, reference_cutoff=100)

        # Test with timestamp that should create specific reference index
        trade = sample_trade.model_copy()
        trade.timestamp = 1234
        agg.on_trade(trade)

        expected_reference_index = 1234 // 100  # 12
        expected_open_time = expected_reference_index * 100  # 1200

        bar = agg.bars[0]
        assert bar.open_time == expected_open_time

    def test_multiple_trades_different_timeframes(self, sample_trade):
        """Test multiple trades across different timeframes"""
        agg = TimeBarAggregator(buf_size=10, reference_cutoff=100)

        # Create trades in different timeframes
        timestamps = [1000, 1100, 1200, 1300, 1400]
        for i, timestamp in enumerate(timestamps):
            trade = sample_trade.model_copy()
            trade.id = i + 1
            trade.timestamp = timestamp
            trade.price = 50000.0 + (i * 100)
            agg.on_trade(trade)

        assert len(agg.bars) == 5

        # Check that each bar has correct timeframe
        for i, bar in enumerate(agg.bars):
            expected_open_time = timestamps[i]
            assert bar.open_time == expected_open_time
            assert bar.close == 50000.0 + (i * 100)

    def test_bar_enclose_called_correctly(self, aggregator, sample_trade):
        """Test that enclose is called with correct timestamp when creating new bar"""
        # First trade
        trade1 = sample_trade.model_copy()
        trade1.timestamp = 1000
        aggregator.on_trade(trade1)

        # Second trade in new timeframe
        trade2 = sample_trade.model_copy()
        trade2.id = 2
        trade2.timestamp = 1200
        aggregator.on_trade(trade2)

        # First bar should be closed with correct timestamp
        first_bar = aggregator.bars[0]
        assert first_bar.is_closed is True
        assert first_bar.close_time == 1199  # next_reference_index * reference_cutoff - 1

    def test_edge_case_zero_reference_cutoff(self, sample_trade):
        """Test edge case with zero reference cutoff"""
        with pytest.raises(ZeroDivisionError):
            agg = TimeBarAggregator(buf_size=10, reference_cutoff=0)
            agg.on_trade(sample_trade)

    def test_edge_case_negative_reference_cutoff(self, sample_trade):
        """Test edge case with negative reference cutoff"""
        agg = TimeBarAggregator(buf_size=10, reference_cutoff=-100)
        agg.on_trade(sample_trade)
        
        # Should still work but with negative calculations
        assert len(agg.bars) == 1

    def test_logging_behavior(self, aggregator, sample_trade, caplog):
        """Test that appropriate logging occurs"""
        with caplog.at_level("INFO"):
            # First trade
            trade1 = sample_trade.model_copy()
            trade1.timestamp = 1000
            aggregator.on_trade(trade1)

            # Second trade in new timeframe to trigger logging
            trade2 = sample_trade.model_copy()
            trade2.id = 2
            trade2.timestamp = 1200
            aggregator.on_trade(trade2)

            # Should log info about finished bar
            assert "Finished time bar:" in caplog.text

    def test_accumulator_tracking(self, aggregator, sample_trade):
        """Test that accumulator correctly tracks latest timestamp"""
        trade1 = sample_trade.model_copy()
        trade1.timestamp = 1000
        aggregator.on_trade(trade1)
        assert aggregator.accumulator == 1000

        trade2 = sample_trade.model_copy()
        trade2.id = 2
        trade2.timestamp = 1500
        aggregator.on_trade(trade2)
        assert aggregator.accumulator == 1500

    def test_bar_properties_consistency(self, aggregator, sample_trade):
        """Test that bar properties are set consistently"""
        trade = sample_trade.model_copy()
        trade.timestamp = 1000
        trade.price = 50000.0
        trade.quantity = 0.5
        trade.side = Side.SIDE_BUY

        aggregator.on_trade(trade)
        bar = aggregator.bars[0]

        # Test all bar properties
        assert bar.symbol == trade.symbol
        assert bar.start_id == trade.id
        assert bar.current_id == trade.id
        assert bar.next_id == trade.id + 1
        assert bar.open == trade.price
        assert bar.high == trade.price
        assert bar.low == trade.price
        assert bar.close == trade.price
        assert bar.volume == trade.quantity
        assert bar.quote_volume == trade.price * trade.quantity
        assert bar.number_of_trades == 1
        assert bar.taker_buy_base_asset_volume == trade.quantity
        assert bar.taker_buy_quote_asset_volume == trade.price * trade.quantity
        assert bar.is_closed is False

    def test_sell_trade_taker_volume_calculation(self, aggregator, sample_trade):
        """Test that sell trades don't contribute to taker buy volumes"""
        trade = sample_trade.model_copy()
        trade.side = Side.SIDE_SELL
        trade.price = 50000.0
        trade.quantity = 0.5

        aggregator.on_trade(trade)
        bar = aggregator.bars[0]

        assert bar.taker_buy_base_asset_volume == 0
        assert bar.taker_buy_quote_asset_volume == 0
        assert bar.volume == trade.quantity
        assert bar.quote_volume == trade.price * trade.quantity
