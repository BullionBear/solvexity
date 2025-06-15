from solvexity.connector.base import ExchangeConnector
from hooklet.eventrix.base import BaseNode

class TradeFeed(BaseNode):
    def __init__(self, connector: ExchangeConnector):
        self.connector = connector

    async def get_trades(self):
        return await self.connector.get_trades()