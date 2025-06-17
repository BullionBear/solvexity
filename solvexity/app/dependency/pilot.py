from typing import Any
from hooklet.base import BasePilot
from hooklet.pilot import NatsPilot


async def get_pilot_from_config(config: dict[str, Any]) -> BasePilot:
    if config.get("type") == "nats":
        return NatsPilot(config.get("url", "nats://localhost:4222"))
    raise ValueError(f"Unknown pilot type: {config.get('type')}")