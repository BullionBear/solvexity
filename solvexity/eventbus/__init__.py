"""
Lightweight, async-based, topic-based eventbus abstract.

This module provides abstract base classes for implementing event-driven architectures
with topic-based message routing and async support.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Set, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)





@dataclass
class Event:
    """Represents an event with topic, data, and metadata."""
    topic: str
    data: Any
    source: Optional[str] = None
    timestamp: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp is None:
            import time
            self.timestamp = time.time()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Subscription:
    """Represents a subscription to a topic."""
    topic: str
    handler: Callable[[Event], Any]
    subscriber_id: Optional[str] = None
    subscription_id: Optional[str] = None
    is_async: bool = True


class EventBusError(Exception):
    """Base exception for eventbus errors."""
    pass


class TopicNotFoundError(EventBusError):
    """Raised when a topic is not found."""
    pass


class SubscriptionError(EventBusError):
    """Raised when there's an error with subscriptions."""
    pass


class EventBus(ABC):
    """
    Abstract base class for topic-based eventbus implementations.
    
    This class defines the interface for a lightweight, async-based eventbus
    that supports topic-based message routing without wildcard pattern matching.
    """
    
    def __init__(self):
        self._subscriptions: Dict[str, List[Subscription]] = {}
        self._running: bool = False
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
    
    @abstractmethod
    async def publish(self, event: Event) -> None:
        """
        Publish an event to a topic.
        
        Args:
            event: The event to publish
            
        Raises:
            TopicNotFoundError: If the topic doesn't exist and creation is not allowed
        """
        pass
    
    @abstractmethod
    async def subscribe(
        self, 
        topic: str, 
        handler: Callable[[Event], Any],
        subscriber_id: Optional[str] = None
    ) -> str:
        """
        Subscribe to a topic with a handler.
        
        Args:
            topic: The topic to subscribe to
            handler: The handler function to call when events are received
            subscriber_id: Optional identifier for the subscriber
            
        Returns:
            Subscription ID
            
        Raises:
            SubscriptionError: If subscription fails
        """
        pass
    
    @abstractmethod
    async def unsubscribe(self, topic: str, subscription_id: str) -> bool:
        """
        Unsubscribe from a topic.
        
        Args:
            topic: The topic to unsubscribe from
            subscription_id: The subscription ID to remove
            
        Returns:
            True if unsubscribed successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_subscribers(self, topic: str) -> List[Subscription]:
        """
        Get all subscribers for a topic.
        
        Args:
            topic: The topic to get subscribers for
            
        Returns:
            List of subscriptions for the topic
        """
        pass
    
    @abstractmethod
    async def list_topics(self) -> List[str]:
        """
        List all available topics.
        
        Returns:
            List of topic names
        """
        pass
    
    async def start(self) -> None:
        """Start the eventbus processing."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._process_events())
        logger.info("EventBus started")
    
    async def stop(self) -> None:
        """Stop the eventbus processing."""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("EventBus stopped")
    
    async def _process_events(self) -> None:
        """Process events from the queue."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._handle_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")
    
    async def _handle_event(self, event: Event) -> None:
        """Handle a single event by calling all registered handlers."""
        async with self._lock:
            subscribers = self._subscriptions.get(event.topic, [])
        
        # Process subscribers in FIFO order (order they were added)
        for subscription in subscribers:
            try:
                if subscription.is_async:
                    await subscription.handler(event)
                else:
                    # Run sync handlers in thread pool
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, subscription.handler, event)
            except Exception as e:
                logger.error(f"Error in event handler for topic '{event.topic}': {e}")
    
    def _generate_subscription_id(self, topic: str, subscriber_id: Optional[str] = None) -> str:
        """Generate a unique subscription ID."""
        import uuid
        base_id = subscriber_id or str(uuid.uuid4())
        return f"{topic}:{base_id}"
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()


class SimpleEventBus(EventBus):
    """
    Simple implementation of the EventBus abstract class.
    
    This implementation provides basic topic-based event routing with async support.
    """
    
    async def publish(self, event: Event) -> None:
        """Publish an event to a topic."""
        if not self._running:
            raise EventBusError("EventBus is not running")
        
        await self._event_queue.put(event)
    
    async def subscribe(
        self, 
        topic: str, 
        handler: Callable[[Event], Any],
        subscriber_id: Optional[str] = None
    ) -> str:
        """Subscribe to a topic with a handler."""
        async with self._lock:
            if topic not in self._subscriptions:
                self._subscriptions[topic] = []
            
            subscription_id = self._generate_subscription_id(topic, subscriber_id)
            subscription = Subscription(
                topic=topic,
                handler=handler,
                subscriber_id=subscriber_id,
                subscription_id=subscription_id,
                is_async=asyncio.iscoroutinefunction(handler)
            )
            
            self._subscriptions[topic].append(subscription)
            logger.info(f"Subscribed to topic '{topic}' with ID '{subscription_id}'")
            
            return subscription_id
    
    async def unsubscribe(self, topic: str, subscription_id: str) -> bool:
        """Unsubscribe from a topic."""
        async with self._lock:
            if topic not in self._subscriptions:
                return False
            
            subscribers = self._subscriptions[topic]
            for i, subscription in enumerate(subscribers):
                if subscription.subscription_id == subscription_id:
                    del subscribers[i]
                    logger.info(f"Unsubscribed from topic '{topic}' with ID '{subscription_id}'")
                    return True
            
            return False
    
    async def get_subscribers(self, topic: str) -> List[Subscription]:
        """Get all subscribers for a topic."""
        async with self._lock:
            return self._subscriptions.get(topic, []).copy()
    
    async def list_topics(self) -> List[str]:
        """List all available topics."""
        async with self._lock:
            return list(self._subscriptions.keys())


# Convenience functions for easy usage
async def create_eventbus() -> EventBus:
    """Create a new EventBus instance."""
    return SimpleEventBus()


@asynccontextmanager
async def eventbus_context():
    """Context manager for EventBus lifecycle management."""
    bus = await create_eventbus()
    try:
        await bus.start()
        yield bus
    finally:
        await bus.stop()


# Export main classes and functions
__all__ = [
    'EventBus',
    'SimpleEventBus', 
    'Event',
    'Subscription',
    'EventBusError',
    'TopicNotFoundError',
    'SubscriptionError',
    'create_eventbus',
    'eventbus_context'
]
