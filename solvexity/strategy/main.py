import asyncio
import logging
import signal
import sys
import nats
from nats.aio.msg import Msg
from nats.js.api import ConsumerConfig, DeliverPolicy, AckPolicy, ReplayPolicy

from solvexity.logging import setup_logging
from solvexity.model.trade import Trade
import solvexity.strategy as strategy


setup_logging()

logger = logging.getLogger(__name__)

# Global shutdown event
shutdown_event = asyncio.Event()

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {sig}, initiating graceful shutdown...")
    shutdown_event.set()


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
            rate_limit_bps=10_000_000, # 10 Mbps
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
    bot = strategy.Pipeline(
        bar_type=strategy.BarType.QUOTE_VOLUME, 
        buf_size=30, 
        reference_cutoff=100000
    )
    
    try:
        logger.info("Attempting to connect to NATS...")
        # Connect to NATS
        nc = await nats.connect(servers=["nats://localhost:4222"])
        logger.info("Connected to NATS")
        
        # Get JetStream context
        js = nc.jetstream()
        logger.info("JetStream context created")
        
        # Set up JetStream consumer
        await setup_jetstream_consumer(js)
        consumer_created = True

        async def trade_handler(msg: Msg):
            trade = Trade.from_protobuf_bytes(msg.data)
            await bot.on_trade(trade)
        
        # Subscribe to the fanout subject (push-based consumer)
        await nc.subscribe("fanout.binance.spot.btcusdt", cb=trade_handler)
        logger.info("Subscribed to fanout.binance.spot.btcusdt")
        
        logger.info("Waiting for trade messages... Press Ctrl+C to stop")
        
        # Wait for shutdown signal instead of infinite loop
        await shutdown_event.wait()
        logger.info("Shutdown signal received, cleaning up...")
        
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
    finally:
        logger.info("Entering finally block...")
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