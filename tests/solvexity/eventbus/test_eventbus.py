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
    
    def test_subscribe_new_topic(self, eventbus):
        """Test subscribing to a new topic."""
        callback = Mock()
        unsubscribe = eventbus.subscribe("test_topic", callback)
        
        assert "test_topic" in eventbus.subscribers
        assert len(eventbus.subscribers["test_topic"]) == 1
        assert eventbus.subscribers["test_topic"][0] == callback
        assert callable(unsubscribe)
    
    def test_subscribe_existing_topic(self, eventbus):
        """Test subscribing to an existing topic."""
        callback1 = Mock()
        callback2 = Mock()
        
        eventbus.subscribe("test_topic", callback1)
        eventbus.subscribe("test_topic", callback2)
        
        assert len(eventbus.subscribers["test_topic"]) == 2
        assert callback1 in eventbus.subscribers["test_topic"]
        assert callback2 in eventbus.subscribers["test_topic"]
    
    def test_subscribe_multiple_topics(self, eventbus):
        """Test subscribing to multiple topics."""
        callback1 = Mock()
        callback2 = Mock()
        
        eventbus.subscribe("topic1", callback1)
        eventbus.subscribe("topic2", callback2)
        
        assert "topic1" in eventbus.subscribers
        assert "topic2" in eventbus.subscribers
        assert len(eventbus.subscribers) == 2
        assert eventbus.subscribers["topic1"] == [callback1]
        assert eventbus.subscribers["topic2"] == [callback2]


class TestEventBusUnsubscribe:
    """Test EventBus unsubscribe functionality."""
    
    def test_unsubscribe_callback(self, eventbus):
        """Test unsubscribing a callback."""
        callback = Mock()
        unsubscribe = eventbus.subscribe("test_topic", callback)
        
        # Verify callback is subscribed
        assert callback in eventbus.subscribers["test_topic"]
        
        # Unsubscribe
        unsubscribe()
        
        # Verify callback is removed
        assert callback not in eventbus.subscribers["test_topic"]
        assert len(eventbus.subscribers["test_topic"]) == 0
    
    def test_unsubscribe_multiple_callbacks(self, eventbus):
        """Test unsubscribing one callback when multiple exist."""
        callback1 = Mock()
        callback2 = Mock()
        
        unsubscribe1 = eventbus.subscribe("test_topic", callback1)
        eventbus.subscribe("test_topic", callback2)
        
        # Verify both callbacks are subscribed
        assert len(eventbus.subscribers["test_topic"]) == 2
        
        # Unsubscribe only callback1
        unsubscribe1()
        
        # Verify only callback1 is removed
        assert callback1 not in eventbus.subscribers["test_topic"]
        assert callback2 in eventbus.subscribers["test_topic"]
        assert len(eventbus.subscribers["test_topic"]) == 1
    
    def test_unsubscribe_nonexistent_callback(self, eventbus):
        """Test unsubscribing a callback that doesn't exist."""
        callback = Mock()
        unsubscribe = eventbus.subscribe("test_topic", callback)
        
        # Unsubscribe
        unsubscribe()
        
        # Try to unsubscribe again (should raise ValueError)
        with pytest.raises(ValueError):
            unsubscribe()
        
        # Verify callback is still not in the list
        assert callback not in eventbus.subscribers["test_topic"]


class TestEventBusPublish:
    """Test EventBus publish functionality."""
    
    @pytest.mark.asyncio
    async def test_publish_sync_callback(self, eventbus, sample_event):
        """Test publishing to a synchronous callback."""
        callback = Mock()
        eventbus.subscribe("test_topic", callback)
        
        await eventbus.publish("test_topic", sample_event)
        
        callback.assert_called_once_with(sample_event)
    
    @pytest.mark.asyncio
    async def test_publish_async_callback(self, eventbus, sample_event):
        """Test publishing to an asynchronous callback."""
        async def async_callback(event):
            return "async_result"
        
        callback = AsyncMock(side_effect=async_callback)
        eventbus.subscribe("test_topic", callback)
        
        await eventbus.publish("test_topic", sample_event)
        
        callback.assert_called_once_with(sample_event)
    
    @pytest.mark.asyncio
    async def test_publish_multiple_callbacks(self, eventbus, sample_event):
        """Test publishing to multiple callbacks."""
        callback1 = Mock()
        callback2 = Mock()
        
        eventbus.subscribe("test_topic", callback1)
        eventbus.subscribe("test_topic", callback2)
        
        await eventbus.publish("test_topic", sample_event)
        
        callback1.assert_called_once_with(sample_event)
        callback2.assert_called_once_with(sample_event)
    
    @pytest.mark.asyncio
    async def test_publish_no_subscribers(self, eventbus, sample_event):
        """Test publishing when no subscribers exist."""
        # Should not raise any exception
        await eventbus.publish("test_topic", sample_event)
    
    @pytest.mark.asyncio
    async def test_publish_different_topic(self, eventbus, sample_event):
        """Test publishing to a topic with no subscribers."""
        callback = Mock()
        eventbus.subscribe("different_topic", callback)
        
        await eventbus.publish("test_topic", sample_event)
        
        # Callback should not be called for different topic
        callback.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_publish_mixed_sync_async_callbacks(self, eventbus, sample_event):
        """Test publishing to a mix of sync and async callbacks."""
        sync_callback = Mock()
        
        async def async_callback(event):
            return "async_result"
        
        async_mock = AsyncMock(side_effect=async_callback)
        
        eventbus.subscribe("test_topic", sync_callback)
        eventbus.subscribe("test_topic", async_mock)
        
        await eventbus.publish("test_topic", sample_event)
        
        sync_callback.assert_called_once_with(sample_event)
        async_mock.assert_called_once_with(sample_event)





class TestEventBusIntegration:
    """Test EventBus integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_subscribe_publish_unsubscribe_cycle(self, eventbus, sample_event):
        """Test complete subscribe-publish-unsubscribe cycle."""
        callback = Mock()
        
        # Subscribe
        unsubscribe = eventbus.subscribe("test_topic", callback)
        
        # Publish
        await eventbus.publish("test_topic", sample_event)
        callback.assert_called_once_with(sample_event)
        
        # Reset mock
        callback.reset_mock()
        
        # Unsubscribe
        unsubscribe()
        
        # Publish again - should not call callback
        await eventbus.publish("test_topic", sample_event)
        callback.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_multiple_topics_and_events(self, eventbus):
        """Test handling multiple topics and events."""
        topic1_callback = Mock()
        topic2_callback = Mock()
        
        eventbus.subscribe("topic1", topic1_callback)
        eventbus.subscribe("topic2", topic2_callback)
        
        event1 = Event(
            time_ms=1234567890,
            data={"value": "value1"}
        )
        
        event2 = Event(
            time_ms=1234567891,
            data={"value": "value2"}
        )
        
        # Publish events
        await eventbus.publish("topic1", event1)
        await eventbus.publish("topic2", event2)
        
        # Give the event loop a chance to process any async tasks
        await asyncio.sleep(0.01)
        
        topic1_callback.assert_called_once_with(event1)
        topic2_callback.assert_called_once_with(event2)
    
    @pytest.mark.asyncio
    async def test_callback_exception_handling(self, eventbus, sample_event):
        """Test that exceptions in callbacks don't break the event bus."""
        def failing_callback(event):
            raise ValueError("Callback error")
        
        def working_callback(event):
            return "success"
        
        working_mock = Mock(side_effect=working_callback)
        
        # Add working callback first, then failing callback
        eventbus.subscribe("test_topic", working_mock)
        eventbus.subscribe("test_topic", failing_callback)
        
        # Should raise the exception from the failing callback
        with pytest.raises(ValueError, match="Callback error"):
            await eventbus.publish("test_topic", sample_event)
        
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
        eventbus.subscribe("test_topic", working_mock)
        eventbus.subscribe("test_topic", failing_mock)
        
        # Should raise the exception from the failing async callback
        with pytest.raises(ValueError, match="Async callback error"):
            await eventbus.publish("test_topic", sample_event)
        
        # Working callback should be called before the exception
        working_mock.assert_called_once_with(sample_event)
        failing_mock.assert_called_once_with(sample_event)


class TestEventBusEdgeCases:
    """Test EventBus edge cases and error conditions."""
    
    @pytest.mark.asyncio
    async def test_subscribe_none_callback(self, eventbus):
        """Test subscribing with None callback."""
        # EventBus doesn't validate callback type, so this should work
        # but will fail when trying to call the callback
        unsubscribe = eventbus.subscribe("test_topic", None)
        
        # Creating an event to test the callback
        event = Event(
            time_ms=1234567890,
            data={"value": "test_value"}
        )
        
        # This should raise a TypeError when trying to call None
        with pytest.raises(TypeError):
            await eventbus.publish("test_topic", event)
    
    @pytest.mark.asyncio
    async def test_publish_none_event(self, eventbus):
        """Test publishing None event."""
        # EventBus doesn't validate the event parameter
        # It just passes it to callbacks, which would fail if they try to access attributes
        callback = Mock()
        eventbus.subscribe("test_topic", callback)
        
        # This should not raise an exception in EventBus
        await eventbus.publish("test_topic", None)
        
        # But the callback should be called with None
        callback.assert_called_once_with(None)
    

    
    @pytest.mark.asyncio
    async def test_subscribe_empty_topic(self, eventbus):
        """Test subscribing with empty topic string."""
        callback = Mock()
        unsubscribe = eventbus.subscribe("", callback)
        
        assert "" in eventbus.subscribers
        assert callback in eventbus.subscribers[""]
        
        # Test publishing to empty topic
        event = Event(
            time_ms=1234567890,
            data={"value": "test_value"}
        )
        
        await eventbus.publish("", event)
        callback.assert_called_once_with(event)
    
    def test_multiple_unsubscribes(self, eventbus):
        """Test multiple unsubscribes of the same callback."""
        callback = Mock()
        unsubscribe = eventbus.subscribe("test_topic", callback)
        
        # First unsubscribe
        unsubscribe()
        assert callback not in eventbus.subscribers["test_topic"]
        
        # Second unsubscribe should raise ValueError
        with pytest.raises(ValueError):
            unsubscribe()
        assert callback not in eventbus.subscribers["test_topic"]
