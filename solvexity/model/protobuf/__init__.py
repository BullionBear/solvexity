# Generated protobuf modules

# Import all generated protobuf modules
try:
    from .shared_pb2 import *
    from .trade_pb2 import *
except ImportError as e:
    print(f"Warning: Could not import protobuf modules: {e}")

# Re-export common classes for easier access
__all__ = [
    # Enums from shared.proto
    'Instrument', 'Exchange', 'Side', 'TimeInForce', 'OrderType',
    # Messages from shared.proto
    'Symbol',
    # Messages from trade.proto
    'Trade',
]
