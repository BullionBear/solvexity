import asyncio
import logging
import signal
import sys
import nats
from nats.aio.msg import Msg
from nats.js.api import ConsumerConfig, DeliverPolicy, AckPolicy, ReplayPolicy

from solvexity.logging import setup_logging
from solvexity.model.trade import Trade
import solvexity.model.protobuf.trade_pb2 as pb2_trade

setup_logging()

logger = logging.getLogger(__name__)

# Global shutdown event
shutdown_event = asyncio.Event()

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {sig}, initiating graceful shutdown...")
    shutdown_event.set()

def process_trade(trade: Trade):
    """Process the deserialized trade data"""
    # Example processing logic
    logger.debug(f"Processing trade ID: {trade.id}")
    logger.debug(f"Trade details: {trade.model_dump()}")
    
    # Add your trade processing logic here
    # For example:
    # - Update price feeds
    # - Calculate indicators
    # - Trigger trading signals
    # - Store in database
    # - Send alerts

async def trade_handler(msg: Msg):
    """Handler for trade data messages"""
    try:
        # Deserialize protobuf data
        pb_trade = pb2_trade.Trade()
        pb_trade.ParseFromString(msg.data)
        
        # Convert to Pydantic Trade model
        trade = Trade.from_protobuf(pb_trade)
        
        # Log the structured trade data
        logger.info(f"Trade received: {trade.symbol.base}{trade.symbol.quote} "
                   f"{trade.side.name} {trade.quantity} @ {trade.price} "
                   f"({trade.exchange.name}, {trade.instrument.name})")
        
        # Process the trade data
        process_trade(trade)
        
    except Exception as e:
        logger.error(f"Failed to deserialize trade data: {e}")
        logger.error(f"Raw data length: {len(msg.data)} bytes")
    
    # Since ack_policy is "none", we don't need to ack the message

async def setup_jetstream_consumer(js):
    """Set up JetStream consumer for trade data"""
    try:
        # Create consumer configuration
        consumer_config = ConsumerConfig(
            name="TRADE_FANOUT_BTCUSDT",
            description="Pub-sub consumer for trade data broadcasting",
            durable_name="TRADE_FANOUT_BTCUSDT",
            deliver_policy=DeliverPolicy.ALL,
            ack_policy=AckPolicy.NONE,
            ack_wait=0,
            max_deliver=1,
            filter_subject="trade.binance.spot.btcusdt",
            replay_policy=ReplayPolicy.INSTANT,
            sample_freq="",
            rate_limit_bps=0,
            max_ack_pending=0,
            idle_heartbeat=0,
            flow_control=False,
            deliver_subject="fanout.binance.spot.btcusdt",
            deliver_group=""
        )
        
        # Create or update the consumer
        consumer_info = await js.add_consumer(
            stream="TRADE",
            config=consumer_config
        )
        
        logger.info(f"Created JetStream consumer: {consumer_info.name}")
        return consumer_info
        
    except Exception as e:
        logger.error(f"Failed to create JetStream consumer: {e}")
        raise

async def cleanup_consumer(js, stream_name: str, consumer_name: str):
    """Remove the JetStream consumer on exit"""
    try:
        await js.delete_consumer(stream=stream_name, consumer=consumer_name)
        logger.info(f"Removed JetStream consumer: {consumer_name}")
    except Exception as e:
        logger.error(f"Failed to remove JetStream consumer {consumer_name}: {e}")

async def main():
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    nc = None
    js = None
    consumer_created = False
    
    try:
        # Connect to NATS
        nc = await nats.connect(servers=["nats://localhost:4222"])
        logger.info("Connected to NATS")
        
        # Get JetStream context
        js = nc.jetstream()
        logger.info("JetStream context created")
        
        # Set up JetStream consumer
        await setup_jetstream_consumer(js)
        consumer_created = True
        
        # Subscribe to the fanout subject (push-based consumer)
        await nc.subscribe("fanout.binance.spot.btcusdt", cb=trade_handler)
        logger.info("Subscribed to fanout.binance.spot.btcusdt")
        
        logger.info("Waiting for trade messages... Press Ctrl+C to stop")
        
        # Wait for shutdown signal instead of infinite loop
        await shutdown_event.wait()
        logger.info("Shutdown signal received, cleaning up...")
        
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
    finally:
        # Clean up the consumer before closing connection
        if js and consumer_created:
            await cleanup_consumer(js, "TRADE", "TRADE_FANOUT_BTCUSDT")
        
        if nc:
            await nc.close()
            logger.info("Disconnected from NATS")
        
        logger.info("Shutdown complete")


if __name__ == "__main__":
    logger.info("NATS JetStream Trade Consumer")
    logger.info("Make sure NATS server with JetStream is running on localhost:4222")
    logger.info("This consumer subscribes to fanout.binance.spot.btcusdt")
    logger.info("Press Ctrl+C to stop\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # This should not happen with our signal handling, but just in case
        logger.info("Program interrupted")
    finally:
        logger.info("Exiting...")
        sys.exit(0)