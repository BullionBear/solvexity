#!/usr/bin/env python3
"""
Test script for pydantic-protobuf mappings.

This script tests the 1-1 mapping between pydantic models and protobuf messages
in the solvexity.model module.
"""

import sys
import time
from typing import Any


def test_symbol_mapping():
    """Test Symbol pydantic-protobuf mapping."""
    print("🔍 Testing Symbol mapping...")
    
    try:
        from solvexity.model.shared import Symbol
        import solvexity.model.protobuf.shared_pb2 as pb2_shared
        
        # Create pydantic Symbol
        pydantic_symbol = Symbol(base="BTC", quote="USDT")
        
        # Convert to protobuf
        pb_symbol = pydantic_symbol.to_protobuf()
        assert isinstance(pb_symbol, pb2_shared.Symbol)
        assert pb_symbol.base == "BTC"
        assert pb_symbol.quote == "USDT"
        print("✅ Pydantic to protobuf conversion successful")
        
        # Convert back to pydantic
        pydantic_symbol2 = Symbol.from_protobuf(pb_symbol)
        assert pydantic_symbol2.base == "BTC"
        assert pydantic_symbol2.quote == "USDT"
        assert pydantic_symbol == pydantic_symbol2
        print("✅ Protobuf to pydantic conversion successful")
        
        return True
    except Exception as e:
        print(f"❌ Symbol mapping test failed: {e}")
        return False


def test_instrument_mapping():
    """Test Instrument enum mapping."""
    print("\n🔍 Testing Instrument mapping...")
    
    try:
        from solvexity.model.shared import Instrument
        import solvexity.model.protobuf.shared_pb2 as pb2_shared
        
        # Test all enum values
        test_values = [
            Instrument.INSTRUMENT_UNSPECIFIED,
            Instrument.INSTRUMENT_SPOT,
            Instrument.INSTRUMENT_MARGIN,
            Instrument.INSTRUMENT_PERP,
            Instrument.INSTRUMENT_INVERSE,
            Instrument.INSTRUMENT_FUTURES,
            Instrument.INSTRUMENT_OPTION,
        ]
        
        for instrument in test_values:
            # Convert to protobuf
            pb_instrument = instrument.to_protobuf()
            assert pb_instrument == instrument.value
            
            # Convert back to pydantic
            pydantic_instrument = Instrument.from_protobuf(pb_instrument)
            assert pydantic_instrument == instrument
        
        print("✅ All Instrument enum values mapped correctly")
        return True
    except Exception as e:
        print(f"❌ Instrument mapping test failed: {e}")
        return False


def test_exchange_mapping():
    """Test Exchange enum mapping."""
    print("\n🔍 Testing Exchange mapping...")
    
    try:
        from solvexity.model.shared import Exchange
        import solvexity.model.protobuf.shared_pb2 as pb2_shared
        
        # Test all enum values
        test_values = [
            Exchange.EXCHANGE_UNSPECIFIED,
            Exchange.EXCHANGE_BINANCE,
            Exchange.EXCHANGE_BINANCE_PERP,
            Exchange.EXCHANGE_BYBIT,
        ]
        
        for exchange in test_values:
            # Convert to protobuf
            pb_exchange = exchange.to_protobuf()
            assert pb_exchange == exchange.value
            
            # Convert back to pydantic
            pydantic_exchange = Exchange.from_protobuf(pb_exchange)
            assert pydantic_exchange == exchange
        
        print("✅ All Exchange enum values mapped correctly")
        return True
    except Exception as e:
        print(f"❌ Exchange mapping test failed: {e}")
        return False


def test_side_mapping():
    """Test Side enum mapping."""
    print("\n🔍 Testing Side mapping...")
    
    try:
        from solvexity.model.shared import Side
        import solvexity.model.protobuf.shared_pb2 as pb2_shared
        
        # Test all enum values
        test_values = [
            Side.SIDE_UNSPECIFIED,
            Side.SIDE_BUY,
            Side.SIDE_SELL,
        ]
        
        for side in test_values:
            # Convert to protobuf
            pb_side = side.to_protobuf()
            assert pb_side == side.value
            
            # Convert back to pydantic
            pydantic_side = Side.from_protobuf(pb_side)
            assert pydantic_side == side
        
        print("✅ All Side enum values mapped correctly")
        return True
    except Exception as e:
        print(f"❌ Side mapping test failed: {e}")
        return False


def test_time_in_force_mapping():
    """Test TimeInForce enum mapping."""
    print("\n🔍 Testing TimeInForce mapping...")
    
    try:
        from solvexity.model.shared import TimeInForce
        import solvexity.model.protobuf.shared_pb2 as pb2_shared
        
        # Test all enum values
        test_values = [
            TimeInForce.TIME_IN_FORCE_UNSPECIFIED,
            TimeInForce.TIME_IN_FORCE_GTC,
            TimeInForce.TIME_IN_FORCE_IOC,
            TimeInForce.TIME_IN_FORCE_FOK,
        ]
        
        for time_in_force in test_values:
            # Convert to protobuf
            pb_time_in_force = time_in_force.to_protobuf()
            assert pb_time_in_force == time_in_force.value
            
            # Convert back to pydantic
            pydantic_time_in_force = TimeInForce.from_protobuf(pb_time_in_force)
            assert pydantic_time_in_force == time_in_force
        
        print("✅ All TimeInForce enum values mapped correctly")
        return True
    except Exception as e:
        print(f"❌ TimeInForce mapping test failed: {e}")
        return False


def test_order_type_mapping():
    """Test OrderType enum mapping."""
    print("\n🔍 Testing OrderType mapping...")
    
    try:
        from solvexity.model.shared import OrderType
        import solvexity.model.protobuf.shared_pb2 as pb2_shared
        
        # Test all enum values
        test_values = [
            OrderType.ORDER_TYPE_UNSPECIFIED,
            OrderType.ORDER_TYPE_LIMIT,
            OrderType.ORDER_TYPE_MARKET,
            OrderType.ORDER_TYPE_STOP_MARKET,
        ]
        
        for order_type in test_values:
            # Convert to protobuf
            pb_order_type = order_type.to_protobuf()
            assert pb_order_type == order_type.value
            
            # Convert back to pydantic
            pydantic_order_type = OrderType.from_protobuf(pb_order_type)
            assert pydantic_order_type == order_type
        
        print("✅ All OrderType enum values mapped correctly")
        return True
    except Exception as e:
        print(f"❌ OrderType mapping test failed: {e}")
        return False


def test_trade_mapping():
    """Test Trade pydantic-protobuf mapping."""
    print("\n🔍 Testing Trade mapping...")
    
    try:
        from solvexity.model.trade import Trade
        from solvexity.model.shared import Symbol, Exchange, Instrument, Side
        import solvexity.model.protobuf.trade_pb2 as pb2_trade
        
        # Create pydantic Trade
        pydantic_trade = Trade(
            id=123456789,
            exchange=Exchange.EXCHANGE_BINANCE,
            instrument=Instrument.INSTRUMENT_SPOT,
            symbol=Symbol(base="ETH", quote="USDT"),
            side=Side.SIDE_BUY,
            price=3500.75,
            quantity=0.5,
            timestamp=int(time.time() * 1000)
        )
        
        # Convert to protobuf
        pb_trade = pydantic_trade.to_protobuf()
        assert isinstance(pb_trade, pb2_trade.Trade)
        assert pb_trade.id == 123456789
        assert pb_trade.exchange == Exchange.EXCHANGE_BINANCE.value
        assert pb_trade.instrument == Instrument.INSTRUMENT_SPOT.value
        assert pb_trade.symbol.base == "ETH"
        assert pb_trade.symbol.quote == "USDT"
        assert pb_trade.side == Side.SIDE_BUY.value
        assert abs(pb_trade.price - 3500.75) < 0.001
        assert abs(pb_trade.quantity - 0.5) < 0.001
        print("✅ Pydantic to protobuf conversion successful")
        
        # Convert back to pydantic
        pydantic_trade2 = Trade.from_protobuf(pb_trade)
        assert pydantic_trade2.id == pydantic_trade.id
        assert pydantic_trade2.exchange == pydantic_trade.exchange
        assert pydantic_trade2.instrument == pydantic_trade.instrument
        assert pydantic_trade2.symbol == pydantic_trade.symbol
        assert pydantic_trade2.side == pydantic_trade.side
        assert abs(pydantic_trade2.price - pydantic_trade.price) < 0.001
        assert abs(pydantic_trade2.quantity - pydantic_trade.quantity) < 0.001
        assert pydantic_trade2.timestamp == pydantic_trade.timestamp
        print("✅ Protobuf to pydantic conversion successful")
        
        # Test serialization roundtrip
        json_str = pydantic_trade.model_dump_json()
        pydantic_trade3 = Trade.model_validate_json(json_str)
        assert pydantic_trade3 == pydantic_trade
        print("✅ JSON serialization roundtrip successful")
        
        return True
    except Exception as e:
        print(f"❌ Trade mapping test failed: {e}")
        return False


def test_performance():
    """Test performance of mappings."""
    print("\n🔍 Testing mapping performance...")
    
    try:
        from solvexity.model.trade import Trade
        from solvexity.model.shared import Symbol, Exchange, Instrument, Side
        
        # Create test data
        pydantic_trade = Trade(
            id=123456789,
            exchange=Exchange.EXCHANGE_BINANCE,
            instrument=Instrument.INSTRUMENT_SPOT,
            symbol=Symbol(base="BTC", quote="USDT"),
            side=Side.SIDE_BUY,
            price=45000.50,
            quantity=0.001,
            timestamp=int(time.time() * 1000)
        )
        
        num_iterations = 10000
        
        # Test pydantic to protobuf performance
        start_time = time.time()
        for _ in range(num_iterations):
            pb_trade = pydantic_trade.to_protobuf()
        to_protobuf_time = time.time() - start_time
        
        # Test protobuf to pydantic performance
        pb_trade = pydantic_trade.to_protobuf()
        start_time = time.time()
        for _ in range(num_iterations):
            pydantic_trade2 = Trade.from_protobuf(pb_trade)
        from_protobuf_time = time.time() - start_time
        
        print(f"✅ Performance test completed:")
        print(f"  Pydantic→Protobuf: {num_iterations} ops in {to_protobuf_time:.3f}s "
              f"({num_iterations/to_protobuf_time:.0f} ops/sec)")
        print(f"  Protobuf→Pydantic: {num_iterations} ops in {from_protobuf_time:.3f}s "
              f"({num_iterations/from_protobuf_time:.0f} ops/sec)")
        
        return True
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False


def test_validation():
    """Test pydantic validation works correctly."""
    print("\n🔍 Testing pydantic validation...")
    
    try:
        from solvexity.model.trade import Trade
        from solvexity.model.shared import Symbol, Exchange, Instrument, Side
        from pydantic import ValidationError
        
        # Test valid data
        valid_trade = Trade(
            id=123456789,
            exchange=Exchange.EXCHANGE_BINANCE,
            instrument=Instrument.INSTRUMENT_SPOT,
            symbol=Symbol(base="BTC", quote="USDT"),
            side=Side.SIDE_BUY,
            price=45000.50,
            quantity=0.001,
            timestamp=int(time.time() * 1000)
        )
        assert valid_trade.id == 123456789
        print("✅ Valid data validation passed")
        
        # Test invalid data types
        try:
            invalid_trade = Trade(
                id="not_an_int",  # This should fail
                exchange=Exchange.EXCHANGE_BINANCE,
                instrument=Instrument.INSTRUMENT_SPOT,
                symbol=Symbol(base="BTC", quote="USDT"),
                side=Side.SIDE_BUY,
                price=45000.50,
                quantity=0.001,
                timestamp=int(time.time() * 1000)
            )
            print("❌ Should have failed validation for invalid id type")
            return False
        except ValidationError:
            print("✅ Invalid data type validation correctly failed")
        
        # Test missing required fields
        try:
            invalid_symbol = Symbol(base="BTC")  # Missing quote
            print("❌ Should have failed validation for missing quote")
            return False
        except ValidationError:
            print("✅ Missing required field validation correctly failed")
        
        return True
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        return False


def main():
    """Run all mapping tests."""
    print("🚀 Starting pydantic-protobuf mapping tests...\n")
    
    tests = [
        test_symbol_mapping,
        test_instrument_mapping,
        test_exchange_mapping,
        test_side_mapping,
        test_time_in_force_mapping,
        test_order_type_mapping,
        test_trade_mapping,
        test_performance,
        test_validation,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All mapping tests passed! Pydantic-protobuf integration is working correctly.")
        return 0
    else:
        print(f"❌ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
