from typing import Type
from hooklet.base import BasePilot, BaseEventrix
from solvexity.eventrix.config import ConfigType

class EventrixDeployer:
    """
    EventrixRPC is a class that provides an interface for interacting with the Eventrix API.
    It allows users to send and receive messages, as well as manage connections.
    """

    def __init__(self, pilot: BasePilot):
        """
        Initializes the EventrixRPC instance.
        """
        self._pilot = pilot
        self._deployments: dict[str, tuple[BaseEventrix, ConfigType]] = {}


    async def deploy(self, eventrix_id: str, eventrix_type: Type[BaseEventrix], config: ConfigType):
        """
        Deploys an Eventrix instance.
        """
        if eventrix_id in self._deployments:
            raise ValueError(f"Eventrix with ID '{eventrix_id}' is already deployed.")

        eventrix_instance = eventrix_type(self._pilot, **dict(config))
        await eventrix_instance.start()
        self._deployments[eventrix_id] = (eventrix_instance, config)

    async def undeploy(self, eventrix_id: str):
        """
        Undeploys an existing Eventrix instance.
        """
        if eventrix_id not in self._deployments:
            raise ValueError(f"No deployed Eventrix found with ID '{eventrix_id}'.")

        eventrix_instance = self._deployments.pop(eventrix_id)
        await eventrix_instance.stop()

    def get_status(self, eventrix_id: str) -> dict:
        """
        Retrieves the status of a deployed Eventrix instance.
        """
        if eventrix_id not in self._deployments:
            raise ValueError(f"No deployed Eventrix found with ID '{eventrix_id}'.")

        eventrix_instance = self._deployments[eventrix_id]
        return eventrix_instance.status()

    def get_all_deployments(self) -> list[dict]:
        """
        Retrieves all deployed Eventrix instances with their IDs, types, and configs.
        """
        return [
            {
                "id": eventrix_id,
                "type": type(eventrix_instance).__name__,
                "config": dict(config),
            }
            for eventrix_id, (eventrix_instance, config) in self._deployments.items()
        ]