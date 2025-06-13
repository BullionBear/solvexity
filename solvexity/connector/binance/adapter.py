from .rest import BinanceRestClient
from .websocket import BinanceWebSocketClient
from solvexity.connector.base import ExchangeRestConnector, ExchangeWebSocketConnector

class BinanceRestAdapter(ExchangeRestConnector):
    def __init__(self, api_key: str, api_secret: str, use_testnet: bool = False):
        self.rest_client = BinanceRestClient(api_key, api_secret, use_testnet)

class BinanceWebSocketAdapter(ExchangeWebSocketConnector):
    def __init__(self, api_key: str, api_secret: str, use_testnet: bool = False):
        super().__init__(api_key, api_secret, use_testnet)
        self.websocket_client = BinanceWebSocketClient(api_key, api_secret, use_testnet)

    def connect(self):
        self.websocket_client.connect()

    def disconnect(self):
        self.websocket_client.disconnect()
