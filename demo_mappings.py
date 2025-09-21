#!/usr/bin/env python3
"""
Demonstration of pydantic-protobuf mappings.

This script shows how to use the 1-1 mapping between pydantic models 
and protobuf messages in the solvexity.model module.
"""

import time
from solvexity.model import Symbol, Instrument, Exchange, Side, Trade


def main():
    print("🚀 Pydantic-Protobuf Mapping Demonstration\n")
    
    # Create pydantic models
    print("1️⃣ Creating pydantic models:")
    symbol = Symbol(base="BTC", quote="USDT")
    print(f"   Symbol: {symbol}")
    
    trade = Trade(
        id=123456789,
        exchange=Exchange.EXCHANGE_BINANCE,
        instrument=Instrument.INSTRUMENT_SPOT,
        symbol=symbol,
        side=Side.SIDE_BUY,
        price=45000.50,
        quantity=0.001,
        timestamp=int(time.time() * 1000)
    )
    print(f"   Trade: {trade}")
    
    # Convert to protobuf
    print("\n2️⃣ Converting to protobuf:")
    pb_trade = trade.to_protobuf()
    print(f"   Protobuf Trade ID: {pb_trade.id}")
    print(f"   Protobuf Exchange: {pb_trade.exchange}")
    print(f"   Protobuf Symbol: {pb_trade.symbol.base}/{pb_trade.symbol.quote}")
    
    # Serialize protobuf
    print("\n3️⃣ Serializing protobuf:")
    serialized = pb_trade.SerializeToString()
    print(f"   Serialized size: {len(serialized)} bytes")
    
    # Deserialize and convert back
    print("\n4️⃣ Deserializing and converting back:")
    from solvexity.model.protobuf.trade_pb2 import Trade as PbTrade
    pb_trade2 = PbTrade()
    pb_trade2.ParseFromString(serialized)
    
    trade2 = Trade.from_protobuf(pb_trade2)
    print(f"   Reconstructed Trade: {trade2}")
    print(f"   Data integrity check: {'✅ PASSED' if trade == trade2 else '❌ FAILED'}")
    
    # Show JSON serialization
    print("\n5️⃣ JSON serialization:")
    json_str = trade.model_dump_json(indent=2)
    print(f"   JSON:\n{json_str}")
    
    # Show validation
    print("\n6️⃣ Pydantic validation in action:")
    try:
        invalid_trade = Trade(
            id="not_an_int",  # This will fail
            exchange=Exchange.EXCHANGE_BINANCE,
            instrument=Instrument.INSTRUMENT_SPOT,
            symbol=symbol,
            side=Side.SIDE_BUY,
            price=45000.50,
            quantity=0.001,
            timestamp=int(time.time() * 1000)
        )
    except Exception as e:
        print(f"   Validation error (expected): {type(e).__name__}")
    
    print("\n🎉 Demo completed! The pydantic-protobuf mapping is working perfectly.")


if __name__ == "__main__":
    main()
