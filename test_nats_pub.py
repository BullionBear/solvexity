#!/usr/bin/env python3
"""
NATS Publisher Test Script

This script connects to NATS and publishes test messages to demonstrate
the publishing functionality.
"""

import asyncio
import json
import time
from typing import Any

import nats
from solvexity.eventbus.event import Event


class NatsPublisher:
    def __init__(self, nats_urls: list[str] = None):
        self.nats_urls = nats_urls or ["nats://localhost:4222"]
        self.nc = None

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
            await self.nc.close()
            print("Disconnected from NATS")

    async def publish_event(self, subject: str, event: Event):
        """Publish an event to a NATS subject"""
        if not self.nc:
            raise RuntimeError("Not connected to NATS")
        
        # Serialize the event to JSON
        message = event.model_dump_json()
        await self.nc.publish(subject, message.encode())
        print(f"Published event to '{subject}': {event.uid}")

    async def publish_raw_message(self, subject: str, data: Any):
        """Publish raw data to a NATS subject"""
        if not self.nc:
            raise RuntimeError("Not connected to NATS")
        
        if isinstance(data, (dict, list)):
            message = json.dumps(data).encode()
        elif isinstance(data, str):
            message = data.encode()
        else:
            message = str(data).encode()
            
        await self.nc.publish(subject, message)
        print(f"Published raw message to '{subject}': {data}")


async def main():
    """Main function to demonstrate NATS publishing"""
    publisher = NatsPublisher()
    
    try:
        # Connect to NATS
        await publisher.connect()
        
        # Test 1: Publish structured events
        print("\n=== Publishing structured events ===")
        for i in range(3):
            event = Event(data={
                "message": f"Hello NATS {i}",
                "timestamp": time.time(),
                "sequence": i
            })
            await publisher.publish_event("test.events", event)
            await asyncio.sleep(1)
        
        # Test 2: Publish raw messages
        print("\n=== Publishing raw messages ===")
        raw_messages = [
            "Simple string message",
            {"type": "order", "symbol": "BTCUSDT", "side": "buy", "quantity": 0.001},
            ["list", "of", "values"],
            42
        ]
        
        for msg in raw_messages:
            await publisher.publish_raw_message("test.raw", msg)
            await asyncio.sleep(0.5)
        
        # Test 3: Publish to different subjects
        print("\n=== Publishing to different subjects ===")
        subjects = ["trade.btc", "trade.eth", "alerts.high", "alerts.low"]
        for subject in subjects:
            event = Event(data={"subject": subject, "value": time.time()})
            await publisher.publish_event(subject, event)
            await asyncio.sleep(0.3)
        
        print("\n=== Publishing completed ===")
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await publisher.disconnect()


if __name__ == "__main__":
    print("NATS Publisher Test Script")
    print("Make sure NATS server is running on localhost:4222")
    print("Press Ctrl+C to stop\n")
    
    asyncio.run(main())
