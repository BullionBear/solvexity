def get_key(symbol: str, granular: str) -> str:
    return f"kline:{symbol}:{granular}"