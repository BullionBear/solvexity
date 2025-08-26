import asyncio
import time
import logging
from solvexity.eventbus.event import Event
from solvexity.eventbus.eventbus import EventBus

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_callback_2(event: Event):
    logger.info("test_sync_callback")
    await asyncio.sleep(2) 
    logger.info(event)

async def main():
    eventbus = EventBus()
    eventbus.subscribe("test", test_callback_2)
    await eventbus.publish_async("test", Event(data={"message": "Hello, world 1!"}))
    await eventbus.publish_async("test", Event(data={"message": "Hello, world 2!"}))
    await eventbus.publish_async("test", Event(data={"message": "Hello, world 3!"}))
    await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(main())