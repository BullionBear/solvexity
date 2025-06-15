class ExchangeConnectorError(Exception):
    """Base exception for all exchange connector errors."""

    pass


class OrderValidationError(ExchangeConnectorError):
    """Base exception for order validation errors."""

    pass


class MarketOrderWithPriceError(OrderValidationError):
    """Raised when a market order is created with a price parameter."""

    def __init__(self, message: str = "Market orders cannot have a price parameter"):
        super().__init__(message)


class OrderIdOrClientOrderIdRequiredError(OrderValidationError):
    """Raised when order id or client order id is required."""

    def __init__(self, message: str = "Order id or client order id is required"):
        super().__init__(message)


class InvalidOrderQuantityError(OrderValidationError):
    """Raised when order quantity is invalid (e.g., zero or negative)."""

    def __init__(self, message: str = "Order quantity must be positive"):
        super().__init__(message)


class InvalidOrderPriceError(OrderValidationError):
    """Raised when order price is invalid (e.g., zero or negative for limit orders)."""

    def __init__(self, message: str = "Order price must be positive for limit orders"):
        super().__init__(message)


class InsufficientBalanceError(OrderValidationError):
    """Raised when there is insufficient balance to place an order."""

    def __init__(self, message: str = "Insufficient balance to place order"):
        super().__init__(message)
