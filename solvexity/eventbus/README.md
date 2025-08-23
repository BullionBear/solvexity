# EventBus Module

A lightweight, async-based, topic-based eventbus implementation for Python.

## Features

- **Async-first design**: Built with asyncio for high-performance event processing
- **Topic-based routing**: Subscribe to specific topics for targeted event handling
- **FIFO ordering**: Events are processed in First In, First Out order for each topic
- **Mixed sync/async handlers**: Support both synchronous and asynchronous event handlers
- **Context manager support**: Easy lifecycle management with async context managers
- **Thread-safe**: Built-in locking for concurrent operations
- **Error isolation**: Handler exceptions don't crash the eventbus
- **Lightweight**: No external dependencies beyond Python standard library

## Quick Start

```python
import asyncio
from solvexity.eventbus import EventBus, Event, EventPriority, eventbus_context

async def trade_handler(event):
    print(f"Trade: {event.data}")

async def main():
    # Using context manager (recommended)
    async with eventbus_context() as bus:
        # Subscribe to topics
        await bus.subscribe("trades", trade_handler)
        
        # Publish events
        await bus.publish(Event("trades", {"symbol": "BTCUSDT", "price": 50000}))
        
        # Wait for processing
        await asyncio.sleep(0.1)

asyncio.run(main())
```

## Core Components

### Event

Represents an event with topic, data, and metadata:

```python
from solvexity.eventbus import Event, EventPriority

# Basic event
event = Event("trades", {"price": 50000})

# Event with metadata
event = Event(
    topic="market_data",
    data={"volume": 1000},
    source="binance",
    metadata={"exchange": "binance"}
)
```

### EventBus

The main eventbus interface:

```python
from solvexity.eventbus import SimpleEventBus

bus = SimpleEventBus()
await bus.start()

# Subscribe
sub_id = await bus.subscribe("topic", handler)

# Publish
await bus.publish(Event("topic", data))

# Unsubscribe
await bus.unsubscribe("topic", sub_id)

await bus.stop()
```

### FIFO Ordering

Events are processed in First In, First Out order for each topic. The order in which handlers are subscribed determines the order in which they receive events.

## Handler Types

### Async Handlers

```python
async def async_handler(event):
    await process_event(event)
    print(f"Processed: {event.data}")
```

### Sync Handlers

```python
def sync_handler(event):
    print(f"Sync processed: {event.data}")
```

The eventbus automatically detects handler type and runs sync handlers in a thread pool.

## Advanced Usage

### Multiple Subscribers

```python
async def handler1(event):
    print(f"Handler 1: {event.data}")

async def handler2(event):
    print(f"Handler 2: {event.data}")

await bus.subscribe("topic", handler1)
await bus.subscribe("topic", handler2)

# Both handlers will receive the event
await bus.publish(Event("topic", {"message": "hello"}))
```

### FIFO Ordering

```python
await bus.subscribe("orders", first_handler)
await bus.subscribe("orders", second_handler)
await bus.subscribe("orders", third_handler)

# Handlers will be called in order: first, second, third
await bus.publish(Event("orders", {"order_id": "123"}))
```

### Subscription Management

```python
# Subscribe with custom ID
sub_id = await bus.subscribe("topic", handler, subscriber_id="my_handler")

# List all topics
topics = await bus.list_topics()

# Get subscribers for a topic
subscribers = await bus.get_subscribers("topic")

# Unsubscribe
success = await bus.unsubscribe("topic", sub_id)
```

### Error Handling

```python
async def failing_handler(event):
    raise Exception("Handler failed")

async def working_handler(event):
    print("Working handler")

# Both handlers are called, exceptions are logged but don't crash the eventbus
await bus.subscribe("topic", failing_handler)
await bus.subscribe("topic", working_handler)
```

## Context Manager

Use the context manager for automatic lifecycle management:

```python
async with eventbus_context() as bus:
    await bus.subscribe("topic", handler)
    await bus.publish(Event("topic", data))
    # EventBus automatically started and stopped
```

## Custom Implementations

You can create custom eventbus implementations by extending the `EventBus` abstract class:

```python
from solvexity.eventbus import EventBus, Event

class CustomEventBus(EventBus):
    async def publish(self, event: Event) -> None:
        # Custom publish logic
        pass
    
    async def subscribe(self, topic: str, handler, subscriber_id=None) -> str:
        # Custom subscribe logic
        pass
    
    # ... implement other abstract methods
```

## Testing

The module includes comprehensive tests. Run them with:

```bash
python -m pytest tests/solvexity/eventbus/ -v
```

## Example

See `example.py` for a complete demonstration of all features.
