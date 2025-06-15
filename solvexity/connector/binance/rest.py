import hashlib
import hmac
import time
import urllib.parse
from typing import Any, Dict, List, Optional, Union

import aiohttp
from aiocache import cached
from aiocache.serializers import JsonSerializer

from solvexity.logger import SolvexityLogger


class BinanceRestClient:
    """Binance REST API client for making direct API calls."""

    BASE_URL = "https://api.binance.com"
    TESTNET_URL = "https://testnet.binance.vision"  # Fixed the URL

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        use_testnet: bool = False,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = self.TESTNET_URL if use_testnet else self.BASE_URL
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = SolvexityLogger().get_logger(__name__)

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def _generate_signature(self, data: Dict[str, Any]) -> str:
        """Generate HMAC-SHA256 signature for the request data.

        Args:
            data: Dictionary of parameters to be signed.

        Returns:
            The hexadecimal digest of the signed data.
        """
        query_string = urllib.parse.urlencode(data)
        return hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _get_headers(self) -> Dict[str, str]:
        """Get default headers including API key if available."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        if self.api_key:
            headers["X-MBX-APIKEY"] = self.api_key
        return headers

    async def _request(
        self, method: str, endpoint: str, signed: bool = False, **kwargs
    ) -> Union[Dict, List]:
        """Make an API request.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint (without base URL)
            signed: Whether the request needs to be signed
            **kwargs: Additional parameters for the request

        Returns:
            JSON response from the API

        Raises:
            aiohttp.ClientError: If the request fails
        """
        if not self.session:
            raise RuntimeError(
                "Session not initialized. Use async with context manager."
            )

        url = f"{self.base_url}{endpoint}"
        params = kwargs.get("params", {})
        data = kwargs.get("data", {})

        if signed:
            if not self.api_secret:
                raise ValueError("API secret is required for signed requests.")

            # Add timestamp for signed requests
            timestamp = int(time.time() * 1000)

            if method in ["GET", "DELETE"]:
                # For GET and DELETE requests, add timestamp to query parameters
                params["timestamp"] = timestamp
                signature = self._generate_signature(params)
                params["signature"] = signature
            else:
                # For POST requests, add timestamp to request body
                data["timestamp"] = timestamp
                signature = self._generate_signature(data)
                data["signature"] = signature

        headers = self._get_headers()

        self.logger.debug(f"Making {method} request to {url}")  # Debug log
        self.logger.debug(f"Params: {params}")  # Debug log
        self.logger.debug(f"Data: {data}")  # Debug log
        self.logger.debug(f"Headers: {headers}")  # Debug log

        async with self.session.request(
            method,
            url,
            params=params if method in ["GET", "DELETE"] else None,
            data=data if method not in ["GET", "DELETE"] else None,
            headers=headers,
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def get_account_information(self) -> Dict:
        """Get current account  (USER_DATA).

        Returns:
            Account information including balances
        """
        return await self._request("GET", "/api/v3/account", signed=True)

    async def test_connectivity(self) -> Dict:
        """Test connectivity to the REST API.

        Returns:
            Empty dict if successful
        """
        return await self._request("GET", "/api/v3/ping")

    async def get_server_time(self) -> Dict:
        """Get server time.

        Returns:
            Dictionary with server time in milliseconds
        """
        return await self._request("GET", "/api/v3/time")

    @cached(ttl=86400, serializer=JsonSerializer())
    async def get_exchange_info(self) -> Dict:
        """Get current exchange trading rules and symbol information.

        Returns:
            Exchange information including symbols, filters, and rate limits
        """
        return await self._request("GET", "/api/v3/exchangeInfo")

    async def create_order(
        self,
        symbol: str,
        side: str,
        type: str,
        quantity: str,
        price: Optional[str] = None,
        time_in_force: Optional[str] = None,
        client_order_id: Optional[str] = None,
        new_order_resp_type: Optional[str] = None,
        stop_price: Optional[float] = None,
    ) -> Dict:
        """Create a new order (TRADE).

        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            side: BUY or SELL
            type: Order type (LIMIT, MARKET, etc.)
            quantity: Order quantity
            price: Optional price (required for limit orders)
            time_in_force: Optional time in force (e.g., GTC, IOC, FOK)
            new_order_resp_type: Optional response type (ACK, RESULT, FULL)
            stop_price: Optional stop price for stop orders

        Returns:
            Order creation response
        """
        data = {
            "symbol": symbol,
            "side": side,
            "type": type,
            "quantity": quantity,
        }
        if price is not None:
            data["price"] = price
        if time_in_force is not None:
            data["timeInForce"] = time_in_force
        if client_order_id is not None:
            data["newClientOrderId"] = client_order_id
        if new_order_resp_type is not None:
            data["newOrderRespType"] = new_order_resp_type
        if stop_price is not None:
            data["stopPrice"] = stop_price

        return await self._request("POST", "/api/v3/order", signed=True, data=data)

    async def get_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        orig_client_order_id: Optional[str] = None,
    ) -> Dict:
        """Get order information.

        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            order_id: Order ID
            orig_client_order_id: Original client order ID

        Returns:
            Order information
        """
        params = {"symbol": symbol}
        if order_id is not None:
            params["orderId"] = order_id
        if orig_client_order_id is not None:
            params["origClientOrderId"] = orig_client_order_id
        return await self._request("GET", "/api/v3/order", signed=True, params=params)

    async def cancel_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        orig_client_order_id: Optional[str] = None,
    ) -> Dict:
        """Cancel an order.

        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            order_id: Order ID
            orig_client_order_id: Original client order ID

        Returns:
            Order cancellation response
        """
        params = {"symbol": symbol}
        if order_id is not None:
            params["orderId"] = order_id
        if orig_client_order_id is not None:
            params["origClientOrderId"] = orig_client_order_id

        return await self._request(
            "DELETE", "/api/v3/order", signed=True, params=params
        )

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get open orders.

        Args:
            symbol: Optional trading pair (e.g., BTCUSDT)

        Returns:
            List of open orders
        """
        params = {}
        if symbol is not None:
            params["symbol"] = symbol
        return await self._request(
            "GET", "/api/v3/openOrders", signed=True, params=params
        )

    async def cancel_all_orders(self, symbol: str) -> Dict:
        """Cancel all open orders.

        Args:
            symbol: Trading pair (e.g., BTCUSDT)

        Returns:
            Order cancellation response
        """
        return await self._request(
            "DELETE", "/api/v3/openOrders", signed=True, params={"symbol": symbol}
        )

    async def get_my_trades(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        from_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """Get user's trades.

        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            order_id: Order ID
            start_time: Start time
            end_time: End time
            from_id: From ID
            limit: Optional limit for the trades (default: 500)

        Returns:
            List of trades
        """
        params = {"symbol": symbol}
        if order_id is not None:
            params["orderId"] = order_id
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if from_id is not None:
            params["fromId"] = from_id
        if limit is not None:
            params["limit"] = limit
        return await self._request(
            "GET", "/api/v3/myTrades", signed=True, params=params
        )

    async def generate_listen_key(self) -> Dict:
        """Generate a new listen key.

        Returns:
            Dictionary with listen key
        """
        return await self._request("POST", "/api/v3/userDataStream", signed=False)

    async def keep_alive_listen_key(self, listen_key: str) -> Dict:
        """Keep a listen key alive.

        Args:
            listen_key: Listen key

        Returns:
            None
        """
        return await self._request(
            "PUT",
            "/api/v3/userDataStream",
            signed=False,
            data={"listenKey": listen_key},
        )

    async def delete_listen_key(self, listen_key: str) -> Dict:
        """Delete a listen key.

        Args:
            listen_key: Listen key

        Returns:
            None
        """
        return await self._request(
            "DELETE",
            "/api/v3/userDataStream",
            signed=False,
            data={"listenKey": listen_key},
        )

    async def get_depth(self, symbol: str, limit: Optional[int] = None) -> Dict:
        """Get order book depth.

        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            limit: Optional limit for the order book (default: 100)

        Returns:
            Order book depth
        """
        params = {"symbol": symbol}
        if limit is not None:
            params["limit"] = limit
        return await self._request("GET", "/api/v3/depth", signed=False, params=params)

    async def get_recent_trades(
        self, symbol: str, limit: Optional[int] = None
    ) -> List[Dict]:
        """Get recent trades.

        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            limit: Optional limit for the trades (default: 500)
        """
        params = {"symbol": symbol}
        if limit is not None:
            params["limit"] = limit
        return await self._request("GET", "/api/v3/trades", signed=False, params=params)

    async def get_agg_trades(
        self,
        symbol: str,
        from_id: Optional[int] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """Get aggregate trades.

        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            from_id: From ID
            start_time: Start time
            end_time: End time
            limit: Optional limit for the trades (default: 500)

        Returns:
            List of aggregate trades
        """
        params = {"symbol": symbol}
        if from_id is not None:
            params["fromId"] = from_id
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if limit is not None:
            params["limit"] = limit
        return await self._request(
            "GET", "/api/v3/aggTrades", signed=False, params=params
        )

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        time_zone: Optional[int] = 0,
        limit: Optional[int] = 500,
    ) -> List[List[float]]:
        """Get klines.

        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            interval: Interval (e.g., 1m, 1h, 1d)
            limit: Optional limit for the klines (default: 500)
            start_time: Start time
            end_time: End time
            time_zone: Time zone (default: 0)
            limit: Optional limit for the klines (default: 500)

        Returns:
            List of klines
        """
        params = {"symbol": symbol, "interval": interval}
        if limit is not None:
            params["limit"] = limit
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        if time_zone is not None:
            params["timeZone"] = time_zone
        return await self._request("GET", "/api/v3/klines", signed=False, params=params)
