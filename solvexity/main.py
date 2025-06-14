#!/usr/bin/env python3
"""
Run both ExampleEmitter and ExampleHandler in a single script.
"""

import asyncio
import logging
import signal

from hooklet.pilot import NatsPilot

from solvexity.trader.collection.ccxt_ochlv_emitter import CCXTOCHLVEmitter

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def handle_shutdown(shutdown_event):
    """Handle graceful shutdown when SIGINT is received."""
    logger.info("Shutting down...")
    shutdown_event.set()


async def main():
    nats_pilot = NatsPilot()
    await nats_pilot.connect()

    emitter = CCXTOCHLVEmitter(
        pilot=nats_pilot,
        exchange_name="binance",
        symbol="ADAUSDT",
        timeframe="1m",
        default_type="future",
        subject="ochlv.ADAUSDT",
        executor_id="solv.ochlv.ADAUSDT",
    )

    # Run both emitter and handler concurrently
    emitter_task = asyncio.create_task(emitter.start())

    try:
        logger.info("CCXTOCHLVEmitter are running. " "Press Ctrl+C to stop.")
        # Create an event for clean shutdown
        shutdown_event = asyncio.Event()

        # Set up a signal handler for keyboard interrupt
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(
            signal.SIGINT, lambda: asyncio.create_task(handle_shutdown(shutdown_event))
        )

        # Wait until shutdown is triggered
        await shutdown_event.wait()

        logger.info("CCXTOCHLVEmitter are running. Press Ctrl+C to stop.")
        # Create an event for clean shutdown
        shutdown_event = asyncio.Event()

        # Set up a signal handler for keyboard interrupt
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(
            signal.SIGINT, lambda: asyncio.create_task(handle_shutdown(shutdown_event))
        )

        # Wait until shutdown is triggered
        await shutdown_event.wait()

    except asyncio.CancelledError:
        logger.info("Task was cancelled, shutting down...")
    finally:
        # First, stop both components
        await emitter.stop()

        # Wait for their tasks to complete
        await asyncio.gather(emitter_task, return_exceptions=True)

        # Finally close the NATS connection
        await nats_pilot.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # This captures the KeyboardInterrupt at the top level
        # if it escapes from the main coroutine
        logger.info("Shutdown complete.")
