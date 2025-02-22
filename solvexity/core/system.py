# Relative Path: solvexity/core/system.py

import abc

########################
# Event Bus (Kafka/Redis)
########################
class EventBus:
    def __init__(self):
        self.subscribers = {}

    def subscribe(self, event_type, callback):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event_type, data):
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                callback(data)

########################
# Abstract Service Class
########################
class AbstractService(abc.ABC):
    def __init__(self, event_bus):
        self.event_bus = event_bus

    @abc.abstractmethod
    def start(self):
        pass

########################
# Trading Pipeline
########################
class TradingPipeline:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        
        self.market_data_service = MarketDataService(event_bus)
        self.strategy_service = StrategyExecutionService(event_bus)
        self.risk_management_service = RiskManagementService(event_bus)
        self.order_execution_service = OrderExecutionService(event_bus)

        self.event_bus.subscribe("market_data", self.strategy_service.on_market_data)
        self.event_bus.subscribe("trade_signal", self.risk_management_service.on_trade_signal)
        self.event_bus.subscribe("validated_trade", self.order_execution_service.execute_order)

    def start_pipeline(self):
        self.market_data_service.start()

########################
# Market Data Service
########################
class MarketDataService(AbstractService):
    def start(self):
        while True:
            market_data = self.get_real_time_data()
            self.event_bus.publish("market_data", market_data)

    def get_real_time_data(self):
        # Fetch from exchange API or WebSocket
        return {"symbol": "BTC/USD", "price": 50000, "timestamp": 1700000000}

########################
# Strategy Execution Service
########################
class StrategyExecutionService(AbstractService):
    def start(self):
        pass  # No continuous loop needed, handled via event bus

    def on_market_data(self, data):
        trade_signal = self.analyze_data(data)
        if trade_signal:
            self.event_bus.publish("trade_signal", trade_signal)

    def analyze_data(self, data):
        # Example strategy: simple moving average
        if data["price"] > 49500:
            return {"action": "BUY", "symbol": data["symbol"], "price": data["price"]}
        return None

########################
# Risk Management Service
########################
class RiskManagementService(AbstractService):
    def start(self):
        pass  # No continuous loop needed, handled via event bus

    def on_trade_signal(self, trade_signal):
        if self.validate_risk(trade_signal):
            self.event_bus.publish("validated_trade", trade_signal)

    def validate_risk(self, trade_signal):
        # Example: Limit max exposure
        return True if trade_signal["price"] < 51000 else False

########################
# Order Execution Service
########################
class OrderExecutionService(AbstractService):
    def start(self):
        pass  # No continuous loop needed, handled via event bus

    def execute_order(self, trade_signal):
        self.send_to_exchange(trade_signal)
        print(f"Executed {trade_signal['action']} {trade_signal['symbol']} at {trade_signal['price']}")

    def send_to_exchange(self, trade_signal):
        # API Call to broker/exchange
        pass

########################
# System Initialization
########################
event_bus = EventBus()
pipeline = TradingPipeline(event_bus)
pipeline.start_pipeline()