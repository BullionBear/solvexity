from typing import Any
from hooklet.base import BasePilot
from hooklet.pilot import NatsPilot
from solvexity.app.deployer import Deployer


class PilotSingleton:
    _pilot: BasePilot | None = None

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> None:
        if config.get("type") == "nats":
            cls._pilot = NatsPilot(config.get("url", "nats://localhost:4222"))
        else:
            raise ValueError(f"Unknown pilot type: {config.get('type')}")

    @classmethod
    async def get_pilot(cls) -> BasePilot:
        if cls._pilot is None:
            raise ValueError("Pilot not set")
        if not cls._pilot.is_connected():
            await cls._pilot.connect()
        return cls._pilot



class DeployerSingleton:
    _deployer: Deployer | None = None

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> None:
        pilot = PilotSingleton.from_config(config.get("pilot", {}))
        cls._deployer = Deployer(pilot)

    @classmethod
    def get_deployer(cls) -> Deployer:
        if cls._deployer is None:
            raise ValueError("Deployer not set")
        return cls._deployer