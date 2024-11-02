def on_trading_start(family: str, **kwargs) -> dict:
    description = f"**Family**: {family}\n" + "\n".join([f"**{key}**: \t{value}" for key, value in kwargs.items()])
    return {
        "title": "On Trading Start",
        "description": description,
        "color": 65280,  # Green color
    }

def on_trading_finish(family: str, **kwargs) -> dict:
    description = f"**Family**: {family}\n" + "\n".join([f"**{key}**: \t{value}" for key, value in kwargs.items()])
    return {
        "title": "On Trading Finish",
        "description": description,
        "color": 65280,  # Green color
    }

def on_order_sent(family: str, **kwargs) -> dict:
    description = f"**Family**: {family}\n" + "\n".join([f"**{key}**: \t{value}" for key, value in kwargs.items()])
    return {
        "title": "On Order Sent",
        "description": description,
        "color": 16776960,  # Yellow color
    }

def on_error(family: str, error: str, **kwargs) -> dict:
    description = f"**Family**: {family}\n" + f"**Error**: {error}\n" + "\n".join([f"**{key}**: \t{value}" for key, value in kwargs.items()])
    return {
        "title": "On Error",
        "description": description,
        "color": 16711680,  # Red color
    }