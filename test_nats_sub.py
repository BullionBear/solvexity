#!/usr/bin/env python3
"""
NATS Subscriber Test Script

This script connects to NATS and subscribes to test subjects to demonstrate
the subscription functionality.
"""

import asyncio
import json
from typing import Optional

import nats
from nats.aio.msg import Msg
from solvexity.eventbus.event import Event


class NatsSubscriber:
    def __init__(self, nats_urls: list[str] = None):
        self.nats_urls = nats_urls or ["nats://localhost:4222"]
        self.nc = None
        self.subscriptions = []

    async def connect(self):
        """Connect to NATS server"""
        try:
            self.nc = await nats.connect(servers=self.nats_urls)
            print(f"Connected to NATS at {self.nats_urls}")
        except Exception as e:
            print(f"Failed to connect to NATS: {e}")
            raise

    async def disconnect(self):
        """Disconnect from NATS server"""
        if self.nc:
            # Unsubscribe from all subscriptions
            for sub in self.subscriptions:
                await sub.unsubscribe()
            await self.nc.close()
            print("Disconnected from NATS")

    async def subscribe_to_events(self, subject: str):
        """Subscribe to structured events on a subject"""
        if not self.nc:
            raise RuntimeError("Not connected to NATS")

        async def event_handler(msg: Msg):
            try:
                # Try to parse as Event
                data = json.loads(msg.data.decode())
                event = Event(**data)
                print(f"📧 Event from '{msg.subject}': {event.uid} | {event.data}")
            except Exception as e:
                print(f"❌ Failed to parse event from '{msg.subject}': {e}")
                print(f"   Raw data: {msg.data.decode()}")

        sub = await self.nc.subscribe(subject, cb=event_handler)
        self.subscriptions.append(sub)
        print(f"📬 Subscribed to events on '{subject}'")

    async def subscribe_to_raw_messages(self, subject: str):
        """Subscribe to raw messages on a subject"""
        if not self.nc:
            raise RuntimeError("Not connected to NATS")

        async def message_handler(msg: Msg):
            try:
                # Try to parse as JSON first
                data = json.loads(msg.data.decode())
                print(f"📦 JSON from '{msg.subject}': {data}")
            except json.JSONDecodeError:
                # Fall back to string
                data = msg.data.decode()
                print(f"📄 Text from '{msg.subject}': {data}")
            except Exception as e:
                print(f"❌ Error handling message from '{msg.subject}': {e}")

        sub = await self.nc.subscribe(subject, cb=message_handler)
        self.subscriptions.append(sub)
        print(f"📬 Subscribed to raw messages on '{subject}'")

    async def subscribe_with_wildcard(self, pattern: str):
        """Subscribe using wildcard patterns"""
        if not self.nc:
            raise RuntimeError("Not connected to NATS")

        async def wildcard_handler(msg: Msg):
            print(f"🔍 Wildcard match '{pattern}' -> '{msg.subject}': {msg.data.decode()[:100]}...")

        sub = await self.nc.subscribe(pattern, cb=wildcard_handler)
        self.subscriptions.append(sub)
        print(f"📬 Subscribed to wildcard pattern '{pattern}'")

    async def request_response_example(self, subject: str, data: str):
        """Demonstrate request-response pattern"""
        if not self.nc:
            raise RuntimeError("Not connected to NATS")

        try:
            # Send request and wait for response (with timeout)
            response = await self.nc.request(subject, data.encode(), timeout=5.0)
            print(f"🔄 Request-Response '{subject}': {response.data.decode()}")
        except asyncio.TimeoutError:
            print(f"⏰ Request to '{subject}' timed out")
        except Exception as e:
            print(f"❌ Request error: {e}")


async def main():
    """Main function to demonstrate NATS subscription"""
    subscriber = NatsSubscriber()
    
    try:
        # Connect to NATS
        await subscriber.connect()
        
        # Subscribe to different types of messages
        await subscriber.subscribe_to_events("test.events")
        await subscriber.subscribe_to_raw_messages("test.raw")
        
        # Subscribe to trading-related subjects
        await subscriber.subscribe_to_events("trade.>")  # Wildcard for all trade subjects
        await subscriber.subscribe_to_events("alerts.>")  # Wildcard for all alert subjects
        
        # Subscribe with specific wildcard patterns
        await subscriber.subscribe_with_wildcard("*.btc")
        await subscriber.subscribe_with_wildcard("trade.*")
        
        print("\n🎧 Listening for messages... Press Ctrl+C to stop")
        print("=" * 60)
        
        # Keep the subscriber running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await subscriber.disconnect()


async def setup_request_responder():
    """Set up a simple request responder for testing"""
    nc = await nats.connect("nats://localhost:4222")
    
    async def request_handler(msg):
        response_data = f"Echo: {msg.data.decode()} (processed at {asyncio.get_event_loop().time()})"
        await msg.respond(response_data.encode())
    
    await nc.subscribe("test.request", cb=request_handler)
    print("🔧 Request responder set up on 'test.request'")
    return nc


if __name__ == "__main__":
    print("NATS Subscriber Test Script")
    print("Make sure NATS server is running on localhost:4222")
    print("Run the publisher script in another terminal to see messages")
    print("Press Ctrl+C to stop\n")
    
    asyncio.run(main())
