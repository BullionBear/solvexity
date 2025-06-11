from typing import Any, Dict, List, Optional
import aiohttp
import hmac
import hashlib
import time
import json


class BinanceRestConnector:
    """Binance REST API connector for making direct API calls."""
    
    BASE_URL = "https://api.binance.com"
    TESTNET_URL = "https://testnet.binance.vision"
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, 
                 use_testnet: bool = False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = self.TESTNET_URL if use_testnet else self.BASE_URL
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Generate signature for authenticated requests."""
        query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        return hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['X-MBX-APIKEY'] = self.api_key
        return headers
        
    async def get_ticker_24hr(self, symbol: str) -> Dict[str, Any]:
        """Get 24hr ticker information."""
        endpoint = f"/api/v3/ticker/24hr"
        params = {'symbol': symbol}
        
        async with self.session.get(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=self._get_headers()
        ) as response:
            return await response.json()
            
    async def get_depth(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """Get order book depth."""
        endpoint = f"/api/v3/depth"
        params = {
            'symbol': symbol,
            'limit': limit
        }
        
        async with self.session.get(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=self._get_headers()
        ) as response:
            return await response.json()
            
    async def get_trades(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent trades."""
        endpoint = f"/api/v3/trades"
        params = {
            'symbol': symbol,
            'limit': limit
        }
        
        async with self.session.get(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=self._get_headers()
        ) as response:
            return await response.json()
            
    async def create_order(self, symbol: str, side: str, order_type: str,
                         quantity: float, price: Optional[float] = None,
                         time_in_force: Optional[str] = None) -> Dict[str, Any]:
        """Create a new order."""
        endpoint = "/api/v3/order"
        params = {
            'symbol': symbol,
            'side': side.upper(),
            'type': order_type.upper(),
            'quantity': quantity,
            'timestamp': int(time.time() * 1000)
        }
        
        if price and order_type.upper() != 'MARKET':
            params['price'] = price
            
        if time_in_force:
            params['timeInForce'] = time_in_force
            
        # Add signature for authenticated request
        params['signature'] = self._generate_signature(params)
        
        async with self.session.post(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=self._get_headers()
        ) as response:
            return await response.json()
            
    async def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Cancel an existing order."""
        endpoint = "/api/v3/order"
        params = {
            'symbol': symbol,
            'orderId': order_id,
            'timestamp': int(time.time() * 1000)
        }
        
        # Add signature for authenticated request
        params['signature'] = self._generate_signature(params)
        
        async with self.session.delete(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=self._get_headers()
        ) as response:
            return await response.json()
            
    async def get_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """Get order status."""
        endpoint = "/api/v3/order"
        params = {
            'symbol': symbol,
            'orderId': order_id,
            'timestamp': int(time.time() * 1000)
        }
        
        # Add signature for authenticated request
        params['signature'] = self._generate_signature(params)
        
        async with self.session.get(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=self._get_headers()
        ) as response:
            return await response.json()
            
    async def get_account(self) -> Dict[str, Any]:
        """Get account information."""
        endpoint = "/api/v3/account"
        params = {
            'timestamp': int(time.time() * 1000)
        }
        
        # Add signature for authenticated request
        params['signature'] = self._generate_signature(params)
        
        async with self.session.get(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=self._get_headers()
        ) as response:
            return await response.json()
