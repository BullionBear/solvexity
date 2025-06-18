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
    def get_pilot(cls) -> BasePilot:
        if cls._pilot is None:
            raise ValueError("Pilot not set")
        return cls._pilot



class DeployerSingleton:
    _deployer: Deployer | None = None

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> None:
        pilot_config = config.get("pilot", {})
        PilotSingleton.from_config(pilot_config)
        cls._deployer = Deployer(PilotSingleton.get_pilot())

    @classmethod
    def get_deployer(cls) -> Deployer:
        if cls._deployer is None:
            raise ValueError("Deployer not set")
        return cls._deployer