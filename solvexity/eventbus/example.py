"""
Example usage of the EventBus implementation.

This file demonstrates how to use the lightweight, async-based, topic-based eventbus.
"""

import asyncio
import logging
from typing import Any

from solvexity.eventbus import (
    EventBus, 
    SimpleEventBus, 
    Event, 
    create_eventbus,
    eventbus_context
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def trade_handler(event: Event) -> None:
    """Handle trade events."""
    logger.info(f"Trade handler received: {event.topic} - {event.data}")
    # Simulate some processing time
    await asyncio.sleep(0.1)


async def price_handler(event: Event) -> None:
    """Handle price events."""
    logger.info(f"Price handler received: {event.topic} - {event.data}")
    # Simulate some processing time
    await asyncio.sleep(0.05)


def sync_handler(event: Event) -> None:
    """Synchronous event handler."""
    logger.info(f"Sync handler received: {event.topic} - {event.data}")


async def high_priority_handler(event: Event) -> None:
    """High priority event handler."""
    logger.info(f"High priority handler received: {event.topic} - {event.data}")


async def example_basic_usage():
    """Basic usage example."""
    logger.info("=== Basic Usage Example ===")
    
    # Create and start the eventbus
    bus = SimpleEventBus()
    await bus.start()
    
    try:
        # Subscribe to topics
        await bus.subscribe("trades", trade_handler)
        await bus.subscribe("prices", price_handler)
        await bus.subscribe("alerts", sync_handler)  # Sync handler
        
        # Publish some events
        await bus.publish(Event("trades", {"symbol": "BTCUSDT", "price": 50000}))
        await bus.publish(Event("prices", {"symbol": "ETHUSDT", "price": 3000}))
        await bus.publish(Event("alerts", {"message": "Price alert triggered"}))
        
        # Wait for events to be processed
        await asyncio.sleep(0.5)
        
    finally:
        await bus.stop()


async def example_with_fifo():
    """Example with FIFO ordering."""
    logger.info("=== FIFO Example ===")
    
    async with eventbus_context() as bus:
        # Subscribe handlers (order matters for FIFO)
        await bus.subscribe("orders", high_priority_handler)
        await bus.subscribe("orders", trade_handler)
        await bus.subscribe("orders", sync_handler)
        
        # Publish events
        await bus.publish(Event("orders", {"order_id": "123", "action": "buy"}))
        
        # Wait for processing
        await asyncio.sleep(0.3)


async def example_with_metadata():
    """Example with event metadata."""
    logger.info("=== Metadata Example ===")
    
    async with eventbus_context() as bus:
        await bus.subscribe("market_data", trade_handler)
        
        # Create event with metadata
        event = Event(
            topic="market_data",
            data={"volume": 1000, "timestamp": 1234567890},
            source="binance",
            metadata={"exchange": "binance", "channel": "spot"}
        )
        
        await bus.publish(event)
        await asyncio.sleep(0.2)


async def example_subscription_management():
    """Example of subscription management."""
    logger.info("=== Subscription Management Example ===")
    
    async with eventbus_context() as bus:
        # Subscribe and get subscription ID
        sub_id = await bus.subscribe("test", trade_handler, subscriber_id="test_handler")
        
        # List topics
        topics = await bus.list_topics()
        logger.info(f"Available topics: {topics}")
        
        # Get subscribers for a topic
        subscribers = await bus.get_subscribers("test")
        logger.info(f"Subscribers for 'test': {len(subscribers)}")
        
        # Publish event
        await bus.publish(Event("test", {"message": "Hello World"}))
        await asyncio.sleep(0.2)
        
        # Unsubscribe
        success = await bus.unsubscribe("test", sub_id)
        logger.info(f"Unsubscribed successfully: {success}")
        
        # Publish another event (should not be handled)
        await bus.publish(Event("test", {"message": "This should not be processed"}))
        await asyncio.sleep(0.2)


async def example_multiple_consumers():
    """Example with multiple consumers on the same topic."""
    logger.info("=== Multiple Consumers Example ===")
    
    async def consumer1(event: Event) -> None:
        logger.info(f"Consumer 1: {event.data}")
    
    async def consumer2(event: Event) -> None:
        logger.info(f"Consumer 2: {event.data}")
    
    async def consumer3(event: Event) -> None:
        logger.info(f"Consumer 3: {event.data}")
    
    async with eventbus_context() as bus:
        # Multiple consumers on the same topic
        await bus.subscribe("broadcast", consumer1)
        await bus.subscribe("broadcast", consumer2)
        await bus.subscribe("broadcast", consumer3)
        
        # Publish event - all consumers should receive it
        await bus.publish(Event("broadcast", {"message": "Broadcast to all consumers"}))
        await asyncio.sleep(0.3)


async def main():
    """Run all examples."""
    await example_basic_usage()
    await asyncio.sleep(1)
    
    await example_with_fifo()
    await asyncio.sleep(1)
    
    await example_with_metadata()
    await asyncio.sleep(1)
    
    await example_subscription_management()
    await asyncio.sleep(1)
    
    await example_multiple_consumers()
    await asyncio.sleep(1)
    
    logger.info("All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
