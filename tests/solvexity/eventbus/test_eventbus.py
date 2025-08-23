"""
Tests for the EventBus implementation.
"""

import pytest
import asyncio
from typing import List, Any

from solvexity.eventbus import (
    EventBus,
    SimpleEventBus,
    Event,
    EventBusError,
    create_eventbus,
    eventbus_context
)


class TestEvent:
    """Test Event class."""
    
    def test_event_creation(self):
        """Test basic event creation."""
        event = Event("test_topic", {"data": "test"})
        assert event.topic == "test_topic"
        assert event.data == {"data": "test"}
        assert event.timestamp is not None
        assert event.metadata == {}
    
    def test_event_with_metadata(self):
        """Test event creation with metadata."""
        event = Event(
            topic="test_topic",
            data="test_data",
            source="test_source",
            metadata={"key": "value"}
        )
        assert event.source == "test_source"
        assert event.metadata == {"key": "value"}


class TestSimpleEventBus:
    """Test SimpleEventBus implementation."""
    
    @pytest.fixture
    async def eventbus(self):
        """Create a test eventbus."""
        bus = SimpleEventBus()
        await bus.start()
        yield bus
        await bus.stop()
    
    @pytest.mark.asyncio
    async def test_subscribe_and_publish(self, eventbus):
        """Test basic subscribe and publish functionality."""
        received_events = []
        
        async def test_handler(event: Event):
            received_events.append(event)
        
        # Subscribe to topic
        sub_id = await eventbus.subscribe("test_topic", test_handler)
        assert sub_id is not None
        
        # Publish event
        test_event = Event("test_topic", {"message": "hello"})
        await eventbus.publish(test_event)
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        assert len(received_events) == 1
        assert received_events[0].topic == "test_topic"
        assert received_events[0].data == {"message": "hello"}
    
    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, eventbus):
        """Test multiple subscribers on the same topic."""
        handler1_events = []
        handler2_events = []
        
        async def handler1(event: Event):
            handler1_events.append(event)
        
        async def handler2(event: Event):
            handler2_events.append(event)
        
        # Subscribe both handlers
        await eventbus.subscribe("test_topic", handler1)
        await eventbus.subscribe("test_topic", handler2)
        
        # Publish event
        test_event = Event("test_topic", {"message": "hello"})
        await eventbus.publish(test_event)
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        assert len(handler1_events) == 1
        assert len(handler2_events) == 1
        assert handler1_events[0].data == {"message": "hello"}
        assert handler2_events[0].data == {"message": "hello"}
    
    @pytest.mark.asyncio
    async def test_fifo_ordering(self, eventbus):
        """Test that events are processed in FIFO order."""
        processing_order = []
        
        async def first_handler(event: Event):
            processing_order.append("first")
        
        async def second_handler(event: Event):
            processing_order.append("second")
        
        async def third_handler(event: Event):
            processing_order.append("third")
        
        # Subscribe handlers in order
        await eventbus.subscribe("test_topic", first_handler)
        await eventbus.subscribe("test_topic", second_handler)
        await eventbus.subscribe("test_topic", third_handler)
        
        # Publish event
        test_event = Event("test_topic", {"message": "hello"})
        await eventbus.publish(test_event)
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Should be processed in FIFO order: first, second, third
        assert processing_order == ["first", "second", "third"]
    
    @pytest.mark.asyncio
    async def test_sync_handler(self, eventbus):
        """Test synchronous handler support."""
        received_events = []
        
        def sync_handler(event: Event):
            received_events.append(event)
        
        # Subscribe sync handler
        await eventbus.subscribe("test_topic", sync_handler)
        
        # Publish event
        test_event = Event("test_topic", {"message": "hello"})
        await eventbus.publish(test_event)
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        assert len(received_events) == 1
        assert received_events[0].data == {"message": "hello"}
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, eventbus):
        """Test unsubscribe functionality."""
        received_events = []
        
        async def test_handler(event: Event):
            received_events.append(event)
        
        # Subscribe
        sub_id = await eventbus.subscribe("test_topic", test_handler)
        
        # Publish first event
        await eventbus.publish(Event("test_topic", {"message": "first"}))
        await asyncio.sleep(0.1)
        
        # Unsubscribe
        success = await eventbus.unsubscribe("test_topic", sub_id)
        assert success is True
        
        # Publish second event (should not be received)
        await eventbus.publish(Event("test_topic", {"message": "second"}))
        await asyncio.sleep(0.1)
        
        # Should only have received the first event
        assert len(received_events) == 1
        assert received_events[0].data == {"message": "first"}
    
    @pytest.mark.asyncio
    async def test_list_topics(self, eventbus):
        """Test listing topics."""
        async def test_handler(event: Event):
            pass
        
        # Subscribe to multiple topics
        await eventbus.subscribe("topic1", test_handler)
        await eventbus.subscribe("topic2", test_handler)
        
        # List topics
        topics = await eventbus.list_topics()
        assert "topic1" in topics
        assert "topic2" in topics
        assert len(topics) == 2
    
    @pytest.mark.asyncio
    async def test_get_subscribers(self, eventbus):
        """Test getting subscribers for a topic."""
        async def test_handler(event: Event):
            pass
        
        # Subscribe
        await eventbus.subscribe("test_topic", test_handler)
        
        # Get subscribers
        subscribers = await eventbus.get_subscribers("test_topic")
        assert len(subscribers) == 1
        assert subscribers[0].topic == "test_topic"
    
    @pytest.mark.asyncio
    async def test_publish_before_start(self):
        """Test that publishing before start raises error."""
        bus = SimpleEventBus()
        
        with pytest.raises(EventBusError, match="EventBus is not running"):
            await bus.publish(Event("test_topic", {"message": "hello"}))
    
    @pytest.mark.asyncio
    async def test_handler_exception(self, eventbus):
        """Test that handler exceptions don't crash the eventbus."""
        received_events = []
        
        async def failing_handler(event: Event):
            raise Exception("Handler failed")
        
        async def working_handler(event: Event):
            received_events.append(event)
        
        # Subscribe both handlers
        await eventbus.subscribe("test_topic", failing_handler)
        await eventbus.subscribe("test_topic", working_handler)
        
        # Publish event
        test_event = Event("test_topic", {"message": "hello"})
        await eventbus.publish(test_event)
        
        # Wait for processing
        await asyncio.sleep(0.1)
        
        # Working handler should still receive the event
        assert len(received_events) == 1


class TestEventBusContext:
    """Test eventbus context manager."""
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test eventbus context manager."""
        received_events = []
        
        async def test_handler(event: Event):
            received_events.append(event)
        
        async with eventbus_context() as bus:
            # Subscribe
            await bus.subscribe("test_topic", test_handler)
            
            # Publish
            await bus.publish(Event("test_topic", {"message": "hello"}))
            
            # Wait for processing
            await asyncio.sleep(0.1)
        
        # Event should be processed
        assert len(received_events) == 1
        assert received_events[0].data == {"message": "hello"}


class TestCreateEventBus:
    """Test create_eventbus function."""
    
    @pytest.mark.asyncio
    async def test_create_eventbus(self):
        """Test create_eventbus function."""
        bus = await create_eventbus()
        assert isinstance(bus, SimpleEventBus)
        
        # Test basic functionality
        await bus.start()
        received_events = []
        
        async def test_handler(event: Event):
            received_events.append(event)
        
        await bus.subscribe("test_topic", test_handler)
        await bus.publish(Event("test_topic", {"message": "hello"}))
        await asyncio.sleep(0.1)
        
        await bus.stop()
        
        assert len(received_events) == 1
