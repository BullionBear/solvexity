import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import List
from pydantic import BaseModel

from solvexity.eventbus.eventbus import EventBus
from solvexity.eventbus.event import Event


@pytest.fixture
def eventbus():
    """Create a fresh EventBus instance for each test."""
    return EventBus()


@pytest.fixture
def sample_event():
    """Create a sample event for testing."""
    return Event(
        time_ms=1234567890,
        source="test_source",
        target="test_target",
        data={"value": "test_value"}
    )


class TestEventBusInitialization:
    """Test EventBus initialization and basic properties."""
    
    def test_init(self):
        """Test EventBus initialization."""
        eventbus = EventBus()
        assert isinstance(eventbus.subscribers, dict)
        assert len(eventbus.subscribers) == 0


class TestEventBusSubscribe:
    """Test EventBus subscribe functionality."""
    
    def test_subscribe_new_source(self, eventbus):
        """Test subscribing to a new source."""
        callback = Mock()
        unsubscribe = eventbus.subscribe("test_source", callback)
        
        assert "test_source" in eventbus.subscribers
        assert len(eventbus.subscribers["test_source"]) == 1
        assert eventbus.subscribers["test_source"][0] == callback
        assert callable(unsubscribe)
    
    def test_subscribe_existing_source(self, eventbus):
        """Test subscribing to an existing source."""
        callback1 = Mock()
        callback2 = Mock()
        
        eventbus.subscribe("test_source", callback1)
        eventbus.subscribe("test_source", callback2)
        
        assert len(eventbus.subscribers["test_source"]) == 2
        assert callback1 in eventbus.subscribers["test_source"]
        assert callback2 in eventbus.subscribers["test_source"]
    
    def test_subscribe_multiple_sources(self, eventbus):
        """Test subscribing to multiple sources."""
        callback1 = Mock()
        callback2 = Mock()
        
        eventbus.subscribe("source1", callback1)
        eventbus.subscribe("source2", callback2)
        
        assert "source1" in eventbus.subscribers
        assert "source2" in eventbus.subscribers
        assert len(eventbus.subscribers) == 2
        assert eventbus.subscribers["source1"] == [callback1]
        assert eventbus.subscribers["source2"] == [callback2]


class TestEventBusUnsubscribe:
    """Test EventBus unsubscribe functionality."""
    
    def test_unsubscribe_callback(self, eventbus):
        """Test unsubscribing a callback."""
        callback = Mock()
        unsubscribe = eventbus.subscribe("test_source", callback)
        
        # Verify callback is subscribed
        assert callback in eventbus.subscribers["test_source"]
        
        # Unsubscribe
        unsubscribe()
        
        # Verify callback is removed
        assert callback not in eventbus.subscribers["test_source"]
        assert len(eventbus.subscribers["test_source"]) == 0
    
    def test_unsubscribe_multiple_callbacks(self, eventbus):
        """Test unsubscribing one callback when multiple exist."""
        callback1 = Mock()
        callback2 = Mock()
        
        unsubscribe1 = eventbus.subscribe("test_source", callback1)
        eventbus.subscribe("test_source", callback2)
        
        # Verify both callbacks are subscribed
        assert len(eventbus.subscribers["test_source"]) == 2
        
        # Unsubscribe only callback1
        unsubscribe1()
        
        # Verify only callback1 is removed
        assert callback1 not in eventbus.subscribers["test_source"]
        assert callback2 in eventbus.subscribers["test_source"]
        assert len(eventbus.subscribers["test_source"]) == 1
    
    def test_unsubscribe_nonexistent_callback(self, eventbus):
        """Test unsubscribing a callback that doesn't exist."""
        callback = Mock()
        unsubscribe = eventbus.subscribe("test_source", callback)
        
        # Unsubscribe
        unsubscribe()
        
        # Try to unsubscribe again (should raise ValueError)
        with pytest.raises(ValueError):
            unsubscribe()
        
        # Verify callback is still not in the list
        assert callback not in eventbus.subscribers["test_source"]


class TestEventBusPublish:
    """Test EventBus publish functionality."""
    
    def test_publish_sync_callback(self, eventbus, sample_event):
        """Test publishing to a synchronous callback."""
        callback = Mock()
        eventbus.subscribe(sample_event.source, callback)
        
        eventbus.publish(sample_event)
        
        callback.assert_called_once_with(sample_event)
    
    def test_publish_async_callback(self, eventbus, sample_event):
        """Test publishing to an asynchronous callback."""
        async def async_callback(event):
            return "async_result"
        
        callback = AsyncMock(side_effect=async_callback)
        eventbus.subscribe(sample_event.source, callback)
        
        # Run in event loop to handle async callbacks
        asyncio.run(eventbus.publish_async(sample_event))
        
        callback.assert_called_once_with(sample_event)
    
    def test_publish_multiple_callbacks(self, eventbus, sample_event):
        """Test publishing to multiple callbacks."""
        callback1 = Mock()
        callback2 = Mock()
        
        eventbus.subscribe(sample_event.source, callback1)
        eventbus.subscribe(sample_event.source, callback2)
        
        eventbus.publish(sample_event)
        
        callback1.assert_called_once_with(sample_event)
        callback2.assert_called_once_with(sample_event)
    
    def test_publish_no_subscribers(self, eventbus, sample_event):
        """Test publishing when no subscribers exist."""
        # Should not raise any exception
        eventbus.publish(sample_event)
    
    def test_publish_different_source(self, eventbus, sample_event):
        """Test publishing to a source with no subscribers."""
        callback = Mock()
        eventbus.subscribe("different_source", callback)
        
        eventbus.publish(sample_event)
        
        # Callback should not be called for different source
        callback.assert_not_called()
    
    def test_publish_mixed_sync_async_callbacks(self, eventbus, sample_event):
        """Test publishing to a mix of sync and async callbacks."""
        sync_callback = Mock()
        
        async def async_callback(event):
            return "async_result"
        
        async_mock = AsyncMock(side_effect=async_callback)
        
        eventbus.subscribe(sample_event.source, sync_callback)
        eventbus.subscribe(sample_event.source, async_mock)
        
        # Run in event loop to handle async callbacks
        asyncio.run(eventbus.publish_async(sample_event))
        
        sync_callback.assert_called_once_with(sample_event)
        async_mock.assert_called_once_with(sample_event)


class TestEventBusPublishAsync:
    """Test EventBus publish_async functionality."""
    
    @pytest.mark.asyncio
    async def test_publish_async_sync_callback(self, eventbus, sample_event):
        """Test async publishing to a synchronous callback."""
        callback = Mock()
        eventbus.subscribe(sample_event.source, callback)
        
        await eventbus.publish_async(sample_event)
        
        callback.assert_called_once_with(sample_event)
    
    @pytest.mark.asyncio
    async def test_publish_async_async_callback(self, eventbus, sample_event):
        """Test async publishing to an asynchronous callback."""
        async def async_callback(event):
            return "async_result"
        
        callback = AsyncMock(side_effect=async_callback)
        eventbus.subscribe(sample_event.source, callback)
        
        await eventbus.publish_async(sample_event)
        
        callback.assert_called_once_with(sample_event)
    
    @pytest.mark.asyncio
    async def test_publish_async_multiple_callbacks(self, eventbus, sample_event):
        """Test async publishing to multiple callbacks."""
        callback1 = Mock()
        callback2 = Mock()
        
        eventbus.subscribe(sample_event.source, callback1)
        eventbus.subscribe(sample_event.source, callback2)
        
        await eventbus.publish_async(sample_event)
        
        callback1.assert_called_once_with(sample_event)
        callback2.assert_called_once_with(sample_event)
    
    @pytest.mark.asyncio
    async def test_publish_async_no_subscribers(self, eventbus, sample_event):
        """Test async publishing when no subscribers exist."""
        # Should not raise any exception
        await eventbus.publish_async(sample_event)
    
    @pytest.mark.asyncio
    async def test_publish_async_different_source(self, eventbus, sample_event):
        """Test async publishing to a source with no subscribers."""
        callback = Mock()
        eventbus.subscribe("different_source", callback)
        
        await eventbus.publish_async(sample_event)
        
        # Callback should not be called for different source
        callback.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_publish_async_mixed_sync_async_callbacks(self, eventbus, sample_event):
        """Test async publishing to a mix of sync and async callbacks."""
        sync_callback = Mock()
        
        async def async_callback(event):
            return "async_result"
        
        async_mock = AsyncMock(side_effect=async_callback)
        
        eventbus.subscribe(sample_event.source, sync_callback)
        eventbus.subscribe(sample_event.source, async_mock)
        
        await eventbus.publish_async(sample_event)
        
        sync_callback.assert_called_once_with(sample_event)
        async_mock.assert_called_once_with(sample_event)


class TestEventBusIntegration:
    """Test EventBus integration scenarios."""
    
    def test_subscribe_publish_unsubscribe_cycle(self, eventbus, sample_event):
        """Test complete subscribe-publish-unsubscribe cycle."""
        callback = Mock()
        
        # Subscribe
        unsubscribe = eventbus.subscribe(sample_event.source, callback)
        
        # Publish
        eventbus.publish(sample_event)
        callback.assert_called_once_with(sample_event)
        
        # Reset mock
        callback.reset_mock()
        
        # Unsubscribe
        unsubscribe()
        
        # Publish again - should not call callback
        eventbus.publish(sample_event)
        callback.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_multiple_sources_and_events(self, eventbus):
        """Test handling multiple sources and events."""
        source1_callback = Mock()
        source2_callback = Mock()
        
        eventbus.subscribe("source1", source1_callback)
        eventbus.subscribe("source2", source2_callback)
        
        event1 = Event(
            time_ms=1234567890,
            source="source1",
            target="target1",
            data={"value": "value1"}
        )
        
        event2 = Event(
            time_ms=1234567891,
            source="source2",
            target="target2",
            data={"value": "value2"}
        )
        
        # Publish events
        eventbus.publish(event1)
        eventbus.publish(event2)
        
        # Give the event loop a chance to process any async tasks
        await asyncio.sleep(0.01)
        
        source1_callback.assert_called_once_with(event1)
        source2_callback.assert_called_once_with(event2)
    
    def test_callback_exception_handling(self, eventbus, sample_event):
        """Test that exceptions in callbacks don't break the event bus."""
        def failing_callback(event):
            raise ValueError("Callback error")
        
        def working_callback(event):
            return "success"
        
        working_mock = Mock(side_effect=working_callback)
        
        # Add working callback first, then failing callback
        eventbus.subscribe(sample_event.source, working_mock)
        eventbus.subscribe(sample_event.source, failing_callback)
        
        # Should raise the exception from the failing callback
        with pytest.raises(ValueError, match="Callback error"):
            eventbus.publish(sample_event)
        
        # Working callback should be called before the exception
        working_mock.assert_called_once_with(sample_event)
    
    @pytest.mark.asyncio
    async def test_async_callback_exception_handling(self, eventbus, sample_event):
        """Test that exceptions in async callbacks don't break the event bus."""
        async def failing_async_callback(event):
            raise ValueError("Async callback error")
        
        def working_callback(event):
            return "success"
        
        working_mock = Mock(side_effect=working_callback)
        failing_mock = AsyncMock(side_effect=failing_async_callback)
        
        # Add working callback first, then failing callback
        eventbus.subscribe(sample_event.source, working_mock)
        eventbus.subscribe(sample_event.source, failing_mock)
        
        # Should raise the exception from the failing async callback
        with pytest.raises(ValueError, match="Async callback error"):
            await eventbus.publish_async(sample_event)
        
        # Working callback should be called before the exception
        working_mock.assert_called_once_with(sample_event)
        failing_mock.assert_called_once_with(sample_event)


class TestEventBusEdgeCases:
    """Test EventBus edge cases and error conditions."""
    
    def test_subscribe_none_callback(self, eventbus):
        """Test subscribing with None callback."""
        # EventBus doesn't validate callback type, so this should work
        # but will fail when trying to call the callback
        unsubscribe = eventbus.subscribe("test_source", None)
        
        # Creating an event to test the callback
        event = Event(
            time_ms=1234567890,
            source="test_source",
            target="test_target",
            data={"value": "test_value"}
        )
        
        # This should raise a TypeError when trying to call None
        with pytest.raises(TypeError):
            eventbus.publish(event)
    
    def test_publish_none_event(self, eventbus):
        """Test publishing None event."""
        with pytest.raises(AttributeError):
            eventbus.publish(None)
    
    @pytest.mark.asyncio
    async def test_publish_async_none_event(self, eventbus):
        """Test async publishing None event."""
        with pytest.raises(AttributeError):
            await eventbus.publish_async(None)
    
    def test_subscribe_empty_source(self, eventbus):
        """Test subscribing with empty source string."""
        callback = Mock()
        unsubscribe = eventbus.subscribe("", callback)
        
        assert "" in eventbus.subscribers
        assert callback in eventbus.subscribers[""]
        
        # Test publishing to empty source
        event = Event(
            time_ms=1234567890,
            source="",
            target="test_target",
            data={"value": "test_value"}
        )
        
        eventbus.publish(event)
        callback.assert_called_once_with(event)
    
    def test_multiple_unsubscribes(self, eventbus):
        """Test multiple unsubscribes of the same callback."""
        callback = Mock()
        unsubscribe = eventbus.subscribe("test_source", callback)
        
        # First unsubscribe
        unsubscribe()
        assert callback not in eventbus.subscribers["test_source"]
        
        # Second unsubscribe should raise ValueError
        with pytest.raises(ValueError):
            unsubscribe()
        assert callback not in eventbus.subscribers["test_source"]
