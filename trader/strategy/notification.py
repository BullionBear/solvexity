def on_trading_start(family: str, **kwargs) -> dict:
    description = f"**Family**: {family}\n" + "\n".join([f"**{key}**: \t{value}" for key, value in kwargs.items()])
    return {
        "title": "On Trading Start",
        "description": description,
        "color": 65280,  # Green color
    }

