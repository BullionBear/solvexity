import asyncio
from solvexity.strategy.gateway import Gateway
from solvexity.strategy.strategy import Strategy

async def main():
    strategy = Strategy()
    async with Gateway(strategy) as gateway:
        await gateway.publish("on_market_data", Event(data={"message": "Hello, world!"}))



if __name__ == "__main__":
    asyncio.run(main())