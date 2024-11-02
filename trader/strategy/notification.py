def trading_process_start(family: str, **kwargs) -> dict:
    description = f"**Family**: {family}\n" + "\n".join([f"**{key}**: \t{value}" for key, value in kwargs.items()])
    return {
        "title": "Process Started",
        "description": description,
        "color": 65280,  # Green color
    }

