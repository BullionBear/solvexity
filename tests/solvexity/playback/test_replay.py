#!/usr/bin/env python3
"""
Pytest tests for MarketSummary and MarketSegment classes from replay.py
"""

import pytest
import json
from datetime import datetime, timezone

from solvexity.playback.replay import MarketSummary, MarketSegment
from solvexity.model import Trade, Exchange, Instrument, Side, Symbol


class TestMarketSummary:
    """Test cases for MarketSummary class"""

    @pytest.fixture
    def market_summary(self):
        """Fixture providing a fresh MarketSummary instance"""
        return MarketSummary()
    
    @pytest.fixture
    def symbols(self):
        """Fixture providing test symbols"""
        return {
            'btc_usdt': Symbol(base="BTC", quote="USDT"),
            'eth_usdt': Symbol(base="ETH", quote="USDT")
        }
    
    @pytest.fixture
    def base_timestamp(self):
        """Fixture providing base timestamp in milliseconds"""
        return 1726329869000  # 2024-09-14 17:04:29 UTC in milliseconds

    def create_fake_trade(self, trade_id: int, symbol: Symbol, price: float, 
                         quantity: float, timestamp_offset: int = 0, 
                         side: Side = Side.SIDE_BUY, base_timestamp: int = 1726329869000) -> Trade:
        """Helper method to create fake trades"""
        return Trade(
            id=trade_id,
            exchange=Exchange.EXCHANGE_BINANCE,
            instrument=Instrument.INSTRUMENT_SPOT,
            symbol=symbol,
            side=side,
            price=price,
            quantity=quantity,
            timestamp=base_timestamp + timestamp_offset
        )

    def test_empty_market_summary(self, market_summary):
        """Test MarketSummary with no trades"""
        summary = market_summary.summarize()
        assert summary == ""
        assert market_summary.n_total == 0

    def test_single_trade_btc(self, market_summary, symbols, base_timestamp):
        """Test MarketSummary with single BTC trade"""
        trade = self.create_fake_trade(
            trade_id=1000001,
            symbol=symbols['btc_usdt'],
            price=65000.0,
            quantity=0.1,
            base_timestamp=base_timestamp
        )
        
        market_summary.on_trade(trade)
        
        # Verify summary structure
        summary = market_summary.summarize()
        assert "BTC" in summary
        assert "USDT" in summary
        assert "6500.0" in summary  # Quote volume, not price
        assert "0.1" in summary
        
        # Verify total count
        assert market_summary.n_total == 1
        
        # Parse JSON to verify structure
        summary_json = json.loads(summary)
        assert summary_json["exchange"] == "EXCHANGE_BINANCE"
        assert summary_json["instrument"] == "INSTRUMENT_SPOT"
        assert "BTC" in summary_json["symbol"]
        assert summary_json["current_id"] == 1000001
        assert summary_json["start_id"] == 1000001
        assert summary_json["total_volume"] == 0.1
        assert summary_json["total_quote_volume"] == 6500.0  # 65000 * 0.1
        assert summary_json["total_trades"] == 1

    def test_consecutive_trades_same_symbol(self, market_summary, symbols, base_timestamp):
        """Test consecutive trades for the same symbol get aggregated"""
        trades = [
            self.create_fake_trade(1000001, symbols['btc_usdt'], 65000.0, 0.1, 0, base_timestamp=base_timestamp),
            self.create_fake_trade(1000002, symbols['btc_usdt'], 65100.0, 0.2, 1000, base_timestamp=base_timestamp),
            self.create_fake_trade(1000003, symbols['btc_usdt'], 65200.0, 0.15, 2000, base_timestamp=base_timestamp),
        ]
        
        for trade in trades:
            market_summary.on_trade(trade)
        
        # Should have one segment for BTC-USDT
        key = (Exchange.EXCHANGE_BINANCE, Instrument.INSTRUMENT_SPOT, symbols['btc_usdt'])
        assert len(market_summary.segments[key]) == 1
        
        segment = market_summary.segments[key][0]
        assert segment.start_id == 1000001
        assert segment.current_id == 1000003
        assert segment.total_trades == 3
        assert segment.total_volume == pytest.approx(0.45)  # 0.1 + 0.2 + 0.15
        assert segment.total_quote_volume == pytest.approx(
            65000.0*0.1 + 65100.0*0.2 + 65200.0*0.15)  # 32830.0
        
        assert market_summary.n_total == 3

    def test_non_consecutive_trades_create_new_segments(self, market_summary, symbols, base_timestamp):
        """Test non-consecutive trade IDs create new segments"""
        trades = [
            self.create_fake_trade(1000001, symbols['btc_usdt'], 65000.0, 0.1, 0, base_timestamp=base_timestamp),
            self.create_fake_trade(1000002, symbols['btc_usdt'], 65100.0, 0.2, 1000, base_timestamp=base_timestamp),
            self.create_fake_trade(1000005, symbols['btc_usdt'], 65200.0, 0.15, 2000, base_timestamp=base_timestamp),  # Gap in ID
        ]
        
        for trade in trades:
            market_summary.on_trade(trade)
        
        # Should have two segments for BTC-USDT due to ID gap
        key = (Exchange.EXCHANGE_BINANCE, Instrument.INSTRUMENT_SPOT, symbols['btc_usdt'])
        assert len(market_summary.segments[key]) == 2
        
        # First segment: trades 1000001-1000002
        first_segment = market_summary.segments[key][0]
        assert first_segment.start_id == 1000001
        assert first_segment.current_id == 1000002
        assert first_segment.total_trades == 2
        
        # Second segment: trade 1000005
        second_segment = market_summary.segments[key][1]
        assert second_segment.start_id == 1000005
        assert second_segment.current_id == 1000005
        assert second_segment.total_trades == 1

    def test_alternating_btc_eth_trades(self, market_summary, symbols, base_timestamp):
        """Test alternating BTC-USDT and ETH-USDT trades"""
        trades = [
            self.create_fake_trade(2000001, symbols['btc_usdt'], 65000.0, 0.1, 0, base_timestamp=base_timestamp),
            self.create_fake_trade(2000002, symbols['eth_usdt'], 3500.0, 1.0, 1000, base_timestamp=base_timestamp),
            self.create_fake_trade(2000003, symbols['btc_usdt'], 65100.0, 0.2, 2000, base_timestamp=base_timestamp),
            self.create_fake_trade(2000004, symbols['eth_usdt'], 3510.0, 1.5, 3000, base_timestamp=base_timestamp),
            self.create_fake_trade(2000005, symbols['btc_usdt'], 65200.0, 0.15, 4000, base_timestamp=base_timestamp),
            self.create_fake_trade(2000006, symbols['eth_usdt'], 3520.0, 0.8, 5000, base_timestamp=base_timestamp),
        ]
        
        for trade in trades:
            market_summary.on_trade(trade)
        
        # Should have segments for both symbols
        btc_key = (Exchange.EXCHANGE_BINANCE, Instrument.INSTRUMENT_SPOT, symbols['btc_usdt'])
        eth_key = (Exchange.EXCHANGE_BINANCE, Instrument.INSTRUMENT_SPOT, symbols['eth_usdt'])
        
        # Each symbol should have 3 segments due to alternating pattern
        assert len(market_summary.segments[btc_key]) == 3
        assert len(market_summary.segments[eth_key]) == 3
        
        # Verify BTC segments
        btc_segments = market_summary.segments[btc_key]
        assert btc_segments[0].start_id == 2000001
        assert btc_segments[1].start_id == 2000003
        assert btc_segments[2].start_id == 2000005
        
        # Verify ETH segments
        eth_segments = market_summary.segments[eth_key]
        assert eth_segments[0].start_id == 2000002
        assert eth_segments[1].start_id == 2000004
        assert eth_segments[2].start_id == 2000006
        
        # Verify total count
        assert market_summary.n_total == 6

    def test_mixed_consecutive_and_non_consecutive_trades(self, market_summary, symbols, base_timestamp):
        """Test complex scenario with mixed consecutive and non-consecutive trades"""
        trades = [
            # BTC consecutive block
            self.create_fake_trade(3000001, symbols['btc_usdt'], 65000.0, 0.1, 0, base_timestamp=base_timestamp),
            self.create_fake_trade(3000002, symbols['btc_usdt'], 65100.0, 0.2, 1000, base_timestamp=base_timestamp),
            self.create_fake_trade(3000003, symbols['btc_usdt'], 65200.0, 0.15, 2000, base_timestamp=base_timestamp),
            
            # ETH consecutive block
            self.create_fake_trade(3000004, symbols['eth_usdt'], 3500.0, 1.0, 3000, base_timestamp=base_timestamp),
            self.create_fake_trade(3000005, symbols['eth_usdt'], 3510.0, 1.5, 4000, base_timestamp=base_timestamp),
            
            # Gap, then BTC again
            self.create_fake_trade(3000010, symbols['btc_usdt'], 66000.0, 0.3, 10000, base_timestamp=base_timestamp),
            self.create_fake_trade(3000011, symbols['btc_usdt'], 66100.0, 0.25, 11000, base_timestamp=base_timestamp),
            
            # Gap, then ETH again
            self.create_fake_trade(3000015, symbols['eth_usdt'], 3600.0, 0.8, 15000, base_timestamp=base_timestamp),
        ]
        
        for trade in trades:
            market_summary.on_trade(trade)
        
        btc_key = (Exchange.EXCHANGE_BINANCE, Instrument.INSTRUMENT_SPOT, symbols['btc_usdt'])
        eth_key = (Exchange.EXCHANGE_BINANCE, Instrument.INSTRUMENT_SPOT, symbols['eth_usdt'])
        
        # BTC should have 2 segments: [3000001-3000003] and [3000010-3000011]
        btc_segments = market_summary.segments[btc_key]
        assert len(btc_segments) == 2
        
        # First BTC segment
        assert btc_segments[0].start_id == 3000001
        assert btc_segments[0].current_id == 3000003
        assert btc_segments[0].total_trades == 3
        
        # Second BTC segment
        assert btc_segments[1].start_id == 3000010
        assert btc_segments[1].current_id == 3000011
        assert btc_segments[1].total_trades == 2
        
        # ETH should have 2 segments: [3000004-3000005] and [3000015]
        eth_segments = market_summary.segments[eth_key]
        assert len(eth_segments) == 2
        
        # First ETH segment
        assert eth_segments[0].start_id == 3000004
        assert eth_segments[0].current_id == 3000005
        assert eth_segments[0].total_trades == 2
        
        # Second ETH segment
        assert eth_segments[1].start_id == 3000015
        assert eth_segments[1].current_id == 3000015
        assert eth_segments[1].total_trades == 1

    def test_summary_json_format(self, market_summary, symbols, base_timestamp):
        """Test that summary output is valid JSON with correct format"""
        trades = [
            self.create_fake_trade(4000001, symbols['btc_usdt'], 65000.0, 0.1, 0, base_timestamp=base_timestamp),
            self.create_fake_trade(4000002, symbols['eth_usdt'], 3500.0, 1.0, 1000, base_timestamp=base_timestamp),
        ]
        
        for trade in trades:
            market_summary.on_trade(trade)
        
        summary = market_summary.summarize()
        
        # Should contain two JSON objects, but they are formatted with indentation
        # So we need to parse the entire summary and count the root objects
        import re
        # Count the number of opening braces that are at the start of a line (root level)
        root_objects = len(re.findall(r'^{', summary, re.MULTILINE))
        assert root_objects == 2
        
        # Split by lines and reconstruct individual JSON objects
        lines = summary.strip().split('\n')
        json_objects = []
        current_object_lines = []
        brace_count = 0
        
        for line in lines:
            current_object_lines.append(line)
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0 and current_object_lines:
                json_objects.append('\n'.join(current_object_lines))
                current_object_lines = []
        
        assert len(json_objects) == 2
        
        # Parse each JSON object
        for json_str in json_objects:
            data = json.loads(json_str)
            
            # Verify required fields
            required_fields = [
                "exchange", "instrument", "symbol", "current_id", "start_id",
                "open_time", "close_time", "total_volume", "total_quote_volume", "total_trades"
            ]
            for field in required_fields:
                assert field in data
            
            # Verify timestamp format (should be ISO format)
            datetime.fromisoformat(data["open_time"].replace('Z', '+00:00'))
            datetime.fromisoformat(data["close_time"].replace('Z', '+00:00'))
            
            # Verify enum values are strings
            assert isinstance(data["exchange"], str)
            assert isinstance(data["instrument"], str)
            assert "EXCHANGE_" in data["exchange"]
            assert "INSTRUMENT_" in data["instrument"]

    def test_timestamp_conversion(self, market_summary, symbols, base_timestamp):
        """Test that timestamps are correctly converted from milliseconds to seconds"""
        trade = self.create_fake_trade(
            trade_id=5000001,
            symbol=symbols['btc_usdt'],
            price=65000.0,
            quantity=0.1,
            timestamp_offset=0,
            base_timestamp=base_timestamp
        )
        
        market_summary.on_trade(trade)
        summary = market_summary.summarize()
        
        data = json.loads(summary)
        
        # Parse the timestamp and verify it's reasonable
        open_time = datetime.fromisoformat(data["open_time"].replace('Z', '+00:00'))
        
        # Should be around the base timestamp (2024-09-14)
        assert open_time.year == 2024
        assert open_time.month == 9
        assert open_time.day == 14

    @pytest.mark.parametrize("side", [Side.SIDE_BUY, Side.SIDE_SELL])
    def test_different_sides(self, market_summary, symbols, base_timestamp, side):
        """Test trades with different sides (BUY/SELL)"""
        trades = [
            self.create_fake_trade(6000001, symbols['btc_usdt'], 65000.0, 0.1, 0, Side.SIDE_BUY, base_timestamp),
            self.create_fake_trade(6000002, symbols['btc_usdt'], 64900.0, 0.2, 1000, side, base_timestamp),
        ]
        
        for trade in trades:
            market_summary.on_trade(trade)
        
        # Should still be aggregated as consecutive trades regardless of side
        btc_key = (Exchange.EXCHANGE_BINANCE, Instrument.INSTRUMENT_SPOT, symbols['btc_usdt'])
        assert len(market_summary.segments[btc_key]) == 1
        
        segment = market_summary.segments[btc_key][0]
        assert segment.total_trades == 2
        assert segment.total_volume == pytest.approx(0.3)
        # Quote volume: 65000*0.1 + 64900*0.2 = 6500 + 12980 = 19480
        assert segment.total_quote_volume == pytest.approx(19480.0)


class TestMarketSegment:
    """Test cases for MarketSegment class"""

    @pytest.fixture
    def btc_usdt(self):
        """Fixture providing BTC-USDT symbol"""
        return Symbol(base="BTC", quote="USDT")
    
    @pytest.fixture
    def base_timestamp(self):
        """Fixture providing base timestamp"""
        return 1726329869000

    def create_fake_trade(self, trade_id: int, price: float, quantity: float, 
                         timestamp_offset: int = 0, btc_usdt: Symbol = None, 
                         base_timestamp: int = 1726329869000) -> Trade:
        """Helper method to create fake trades"""
        if btc_usdt is None:
            btc_usdt = Symbol(base="BTC", quote="USDT")
        
        return Trade(
            id=trade_id,
            exchange=Exchange.EXCHANGE_BINANCE,
            instrument=Instrument.INSTRUMENT_SPOT,
            symbol=btc_usdt,
            side=Side.SIDE_BUY,
            price=price,
            quantity=quantity,
            timestamp=base_timestamp + timestamp_offset
        )

    def test_market_segment_from_trade(self, btc_usdt, base_timestamp):
        """Test creating MarketSegment from a single trade"""
        trade = self.create_fake_trade(7000001, 65000.0, 0.1, 0, btc_usdt, base_timestamp)
        
        segment = MarketSegment.from_trade(trade)
        
        assert segment.exchange == Exchange.EXCHANGE_BINANCE
        assert segment.instrument == Instrument.INSTRUMENT_SPOT
        assert segment.symbol == btc_usdt
        assert segment.current_id == 7000001
        assert segment.start_id == 7000001
        assert segment.open_time == base_timestamp
        assert segment.close_time == base_timestamp
        assert segment.total_volume == 0.1
        assert segment.total_quote_volume == 6500.0
        assert segment.total_trades == 1

    def test_market_segment_addition(self, btc_usdt, base_timestamp):
        """Test adding trades to a MarketSegment using += operator"""
        trade1 = self.create_fake_trade(7000001, 65000.0, 0.1, 0, btc_usdt, base_timestamp)
        trade2 = self.create_fake_trade(7000002, 65100.0, 0.2, 1000, btc_usdt, base_timestamp)
        
        segment = MarketSegment.from_trade(trade1)
        segment += trade2
        
        assert segment.current_id == 7000002
        assert segment.start_id == 7000001  # Should remain unchanged
        assert segment.open_time == base_timestamp  # Should remain unchanged
        assert segment.close_time == base_timestamp + 1000  # Updated
        assert segment.total_volume == pytest.approx(0.3)  # 0.1 + 0.2, using pytest.approx for float precision
        assert segment.total_quote_volume == 19520.0  # 6500 + 13020
        assert segment.total_trades == 2

    def test_market_segment_summarize_json(self, btc_usdt, base_timestamp):
        """Test MarketSegment summarize method produces valid JSON"""
        trade = self.create_fake_trade(8000001, 65000.0, 0.1, 0, btc_usdt, base_timestamp)
        segment = MarketSegment.from_trade(trade)
        
        summary = segment.summarize()
        
        # Should be valid JSON
        data = json.loads(summary)
        
        # Verify structure
        assert data["exchange"] == "EXCHANGE_BINANCE"
        assert data["instrument"] == "INSTRUMENT_SPOT"
        assert "BTC" in data["symbol"]
        assert data["current_id"] == 8000001
        assert data["start_id"] == 8000001
        assert data["total_volume"] == 0.1
        assert data["total_quote_volume"] == 6500.0
        assert data["total_trades"] == 1
        
        # Verify timestamps are ISO format
        datetime.fromisoformat(data["open_time"].replace('Z', '+00:00'))
        datetime.fromisoformat(data["close_time"].replace('Z', '+00:00'))


class TestMarketSummaryEdgeCases:
    """Test edge cases and boundary conditions for MarketSummary"""

    @pytest.fixture
    def market_summary(self):
        return MarketSummary()
    
    @pytest.fixture 
    def symbols(self):
        return {
            'btc_usdt': Symbol(base="BTC", quote="USDT"),
            'eth_usdt': Symbol(base="ETH", quote="USDT")
        }

    def create_fake_trade(self, trade_id: int, symbol: Symbol, price: float, 
                         quantity: float, timestamp_offset: int = 0, 
                         side: Side = Side.SIDE_BUY, base_timestamp: int = 1726329869000) -> Trade:
        """Helper method to create fake trades"""
        return Trade(
            id=trade_id,
            exchange=Exchange.EXCHANGE_BINANCE,
            instrument=Instrument.INSTRUMENT_SPOT,
            symbol=symbol,
            side=side,
            price=price,
            quantity=quantity,
            timestamp=base_timestamp + timestamp_offset
        )

    def test_large_trade_volumes(self, market_summary, symbols):
        """Test handling of large trade volumes"""
        trade = self.create_fake_trade(
            trade_id=9000001,
            symbol=symbols['btc_usdt'],
            price=65000.0,
            quantity=1000.0  # Large volume
        )
        
        market_summary.on_trade(trade)
        summary = market_summary.summarize()
        data = json.loads(summary)
        
        assert data["total_volume"] == 1000.0
        assert data["total_quote_volume"] == 65000000.0  # 65000 * 1000

    def test_zero_quantity_trade(self, market_summary, symbols):
        """Test handling of zero quantity trades"""
        trade = self.create_fake_trade(
            trade_id=9000002,
            symbol=symbols['btc_usdt'],
            price=65000.0,
            quantity=0.0
        )
        
        market_summary.on_trade(trade)
        summary = market_summary.summarize()
        data = json.loads(summary)
        
        assert data["total_volume"] == 0.0
        assert data["total_quote_volume"] == 0.0

    def test_very_small_quantities(self, market_summary, symbols):
        """Test handling of very small quantities (precision)"""
        trade = self.create_fake_trade(
            trade_id=9000003,
            symbol=symbols['btc_usdt'],
            price=65000.0,
            quantity=0.00000001  # 1 satoshi equivalent
        )
        
        market_summary.on_trade(trade)
        summary = market_summary.summarize()
        data = json.loads(summary)
        
        assert data["total_volume"] == pytest.approx(0.00000001)
        assert data["total_quote_volume"] == pytest.approx(0.00065)

    @pytest.mark.parametrize("exchange", [Exchange.EXCHANGE_BINANCE, Exchange.EXCHANGE_BYBIT])
    def test_different_exchanges(self, market_summary, symbols, exchange):
        """Test trades from different exchanges are handled separately"""
        trade = Trade(
            id=9000004,
            exchange=exchange,
            instrument=Instrument.INSTRUMENT_SPOT,
            symbol=symbols['btc_usdt'],
            side=Side.SIDE_BUY,
            price=65000.0,
            quantity=0.1,
            timestamp=1726329869000
        )
        
        market_summary.on_trade(trade)
        
        key = (exchange, Instrument.INSTRUMENT_SPOT, symbols['btc_usdt'])
        assert len(market_summary.segments[key]) == 1
        assert market_summary.segments[key][0].exchange == exchange
