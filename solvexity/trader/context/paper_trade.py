from typing import Optional
from decimal import Decimal
from threading import Thread
from solvexity.dependency.notification import Notification, Color
from solvexity.trader.core import TradeContext, Feed
from solvexity.trader.model import KLine, Trade, Order
import solvexity.helper.logging as logging
import solvexity.helper as helper

logger = logging.get_logger()

class PaperTradeContext(TradeContext):
    """
    A paper trade context for trading strategies.  The execution of trades is simulated in this context in simple strategies.
    """
    def __init__(self, feed: Feed, notification: Notification,  init_balance: dict[str, str]):
        """
        Args:
            init_balance (dict): The initial balance for the backtest context, e.g. {"BTC": '1', "USDT": '10000'}
            redis (redis.Redis): The Redis client instance for querying kline data
        """
        self.balance = {k: {"free": Decimal(v), "locked": Decimal('0')} for k, v in init_balance.items()}
        logger.info(f"Initial balance: {self.balance}")
        self.feed: Feed = feed
        self.notification = notification
        self._trade_id = 1
        self.trade: list[Trade] = []

        self._order_id = 1
        self._order: dict[int, Order] = {}

        self._thread = Thread(target=self._order_manager)
        self._thread.start()

    def _order_manager(self):
        for _ in self.feed.receive('1m'):
            dealt_orders = []
            for _, order in self._order.items():
                kline = self.feed.latest_n_klines(order.symbol, '1m', 1)[0]
                symbol = order.symbol
                if order.side == "BUY" and order.price >= kline[0].close:
                    self.trade.append(Trade(symbol=symbol, 
                                            id=self._trade_id, 
                                            order_id=order.order_id, 
                                            order_list_id=-1, 
                                            price=min(order.price, kline[0].close), 
                                            qty=order.original_quantity, 
                                            quote_qty=min(order.price, kline[0].close) * order.original_quantity,
                                            commission=0, 
                                            commission_asset="BNB", 
                                            time=self._get_time(), 
                                            is_buyer=True, 
                                            is_maker=True, 
                                            is_best_match=True))
                    self._trade_id += 1
                    content = helper.to_content({
                        "context": self.__class__.__name__,
                        "type": "limit",
                        "symbol": symbol,
                        "side": "buy",
                        "size": order.qty,
                        "ref price": order.price
                    })
                    self.notify(self.__class__.__name__, "OnLimitBuyDealt", content, Color.GREEN)
                    dealt_orders.append(order.order_id)
                if order.side == "SELL" and order.price <= kline[0].close:
                    self.trade.append(Trade(symbol=symbol, 
                                            id=self._trade_id, 
                                            order_id=order.order_id, 
                                            order_list_id=-1, 
                                            price=max(order.price, kline[0].close), 
                                            qty=order.original_quantity, 
                                            quote_qty=max(order.price, kline[0].close) * order.original_quantity,
                                            commission=0, 
                                            commission_asset="BNB", 
                                            time=self._get_time(), 
                                            is_buyer=False, 
                                            is_maker=True, 
                                            is_best_match=True))
                    self._trade_id += 1
                    content = helper.to_content({
                        "context": self.__class__.__name__,
                        "type": "limit",
                        "symbol": symbol,
                        "side": "sell",
                        "size": order.qty,
                        "ref price": order.price
                    })
                    self.notify(self.__class__.__name__, "OnLimitSellDealt", content, Color.PURPLE)
                    dealt_orders.append(order.order_id)
            for order_id in dealt_orders:
                self._order.pop(order_id)
        return

    def market_buy(self, symbol: str, size: Decimal):
        ask, _ = self.get_askbid(symbol)
        size, ask = helper.symbol_filter(symbol, size, ask)
        base, quote = symbol[:-4], symbol[-4:] # e.g. BTCUSDT -> BTC, USDT
        self.balance[base]['free'] += size
        self.balance[quote]['free'] -= size * ask
        content = helper.to_content({
            "context": self.__class__.__name__,
            "type": "market",
            "symbol": symbol,
            "side": "buy",
            "size": size,
            "ref price": ask
        })
        self.notify(self.__class__.__name__, "OnMarketBuy", content, Color.CYAN)
        logger.info(f"Context market buy: {symbol}, size: {str(size)}, price: {str(ask)}")
        logger.info(f"Current balance: {self.balance}")
        self.trade.append(Trade(symbol=symbol, 
                                id=self._trade_id, 
                                order_id=self._order_id, 
                                order_list_id=-1, 
                                price=float(ask), 
                                qty=float(size), 
                                quote_qty=float(size * ask), 
                                commission=0, 
                                commission_asset="BNB", 
                                time=self._get_time(), 
                                is_buyer=True, 
                                is_maker=False, 
                                is_best_match=True))
        self._order_id += 1
        self._trade_id += 1

    def market_sell(self, symbol: str, size: Decimal):
        _, bid = self.get_askbid(symbol)
        size, bid = helper.symbol_filter(symbol, size, bid)
        base, quote = symbol[:-4], symbol[-4:]
        self.balance[base]['free'] -= size
        self.balance[quote]['free'] += size * bid
        content = helper.to_content({
            "context": self.__class__.__name__,
            "type": "market",
            "symbol": symbol,
            "side": "sell",
            "size": size,
            "ref price": bid
        })
        self.notify(self.__class__.__name__, "OnMarketSell", content, Color.MAGENTA)
        logger.info(f"Context market sell: {symbol}, size: {str(size)}, price: {str(bid)}")
        logger.info(f"Current balance: {self.balance}")
        self.trade.append(Trade(symbol=symbol, 
                                id=self._trade_id, 
                                order_id=self._order_id, 
                                order_list_id=-1, 
                                price=bid, 
                                qty=size, 
                                quote_qty=size * bid, 
                                commission=0, 
                                commission_asset="BNB", 
                                time=self._get_time(), 
                                is_buyer=False, 
                                is_maker=False, 
                                is_best_match=True))
        self._order_id += 1
        self._trade_id += 1

    def limit_buy(self, symbol: str, size: Decimal, price: Decimal):
        self._order[self._order_id] = Order(
            symbol=symbol,
            order_id=self._order_id,
            order_list_id=-1,
            client_order_id=str(self._order_id),
            price=str(price),
            original_quantity=str(size),
            executed_quantity=Decimal('0'),
            cumulative_quote_quantity=Decimal('0'),
            status="NEW",
            time_in_force="GTC",
            order_type="LIMIT",
            side="BUY",
            stop_price=Decimal('0'),
            iceberg_quantity=Decimal('0'),
            time=self._get_time(),
            update_time=self._get_time(),
            is_working=True,
            original_quote_order_quantity=Decimal('0'),
            working_time=self._get_time(),
            self_trade_prevention_mode="NONE"
        )
        content = helper.to_content({
                        "context": self.__class__.__name__,
                        "type": "limit",
                        "symbol": symbol,
                        "side": "buy",
                        "size": size,
                        "ref price": price
                    })
        self.notify(self.__class__.__name__, "OnLimitBuySent", content, Color.PURPLE)
        self._order_id += 1
        
    
    def limit_sell(self, symbol: str, size: Decimal, price: Decimal):
        self._order[self._order_id] = Order(
            symbol=symbol,
            order_id=self._order_id,
            order_list_id=-1,
            client_order_id=str(self._order_id),
            price=price,
            original_quantity=size,
            executed_quantity=Decimal('0'),
            cumulative_quote_quantity=Decimal('0'),
            status="NEW",
            time_in_force="GTC",
            order_type="LIMIT",
            side="SELL",
            stop_price=Decimal('0'),
            iceberg_quantity=Decimal('0'),
            time=self._get_time(),
            update_time=self._get_time(),
            is_working=True,
            original_quote_order_quantity=Decimal('0'),
            working_time=self._get_time(),
            self_trade_prevention_mode="NONE"
        )
        content = helper.to_content({
                        "context": self.__class__.__name__,
                        "type": "limit",
                        "symbol": symbol,
                        "side": "sell",
                        "size": size,
                        "ref price": price
                    })
        self.notify(self.__class__.__name__, "OnLimitSellSent", content, Color.PURPLE)
        self._order_id += 1

    def get_order(self, order_id: str):
        return self._order[order_id]
    
    def cancel_order(self, symbol, order_id):
        if order_id in self._order and self._order[order_id].symbol == symbol:
            self._order.pop(order_id)
            

    def get_balance(self, token: str) -> Decimal:
        return self.balance[token]['free'] + self.balance[token]['locked']
    
    def get_avaliable_balance(self, token: str) -> Decimal:
        return self.balance[token]['free']

    def _get_time(self) -> int:
        return self.feed.time()
        
    def get_askbid(self, symbol: str) -> tuple[Decimal, Decimal]:
        lastest_kline = self.feed.latest_n_klines(symbol, '1m', 1)[0]
        return Decimal(lastest_kline.close), Decimal(lastest_kline.close)
    
    def notify(self, username: str, title: str, content: Optional[str], color: Color):
        self.notification.notify(username, title, content, color, self.feed.time())

    def get_klines(self, symbol: str, limit: int, granular: str) -> list[KLine]:
        return self.feed.latest_n_klines(symbol, granular, limit)
    
    def get_trades(self, symbol, limit) -> list[Trade]:
        trades = filter(lambda x: x.symbol == symbol, self.trade)
        return list(trades)[-limit:]
    
    def recv(self):
        return self.feed.receive('1m')
    
    def close(self):
        if self._thread.is_alive():
            self._thread.join()
        
    