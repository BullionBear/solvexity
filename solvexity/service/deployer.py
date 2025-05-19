import asyncio
import logging
from typing import Type, Any
from hooklet.base import BasePilot, BaseEventrix

logger = logging.getLogger(__name__)

class EventrixDeployer:
    """
    EventrixDeployer is a class that provides an interface for deploying, undeploying, 
    and managing Eventrix instances.
    """

    def __init__(self, pilot: BasePilot):
        """
        Initializes the EventrixDeployer instance.
        """
        self._pilot = pilot
        self._deployments: dict[str, tuple[BaseEventrix, dict[str, Any]]] = {}
        self._shutdown_event = asyncio.Event()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown()

    async def deploy(self, eventrix_id: str, eventrix_type: Type[BaseEventrix], config: dict[str, Any]):
        """
        Deploys an Eventrix instance.
        """
        if eventrix_id in self._deployments:
            raise ValueError(f"Eventrix with ID '{eventrix_id}' is already deployed.")

        try:
            eventrix_instance = eventrix_type(self._pilot, **config)
            # Start the eventrix instance
            await eventrix_instance.start()
            self._deployments[eventrix_id] = (eventrix_instance, config)
            logger.info(f"Successfully deployed Eventrix: {eventrix_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to deploy Eventrix {eventrix_id}: {type(e).__name__} - {str(e)}")
            # Clean up if initialization succeeded but start failed
            if eventrix_id in self._deployments:
                eventrix_instance, _ = self._deployments.pop(eventrix_id)
                try:
                    await eventrix_instance.stop()
                except Exception:
                    pass
            raise

    async def undeploy(self, eventrix_id: str):
        """
        Undeploys an existing Eventrix instance.
        """
        if eventrix_id not in self._deployments:
            raise ValueError(f"No deployed Eventrix found with ID '{eventrix_id}'.")

        try:
            eventrix_instance, _ = self._deployments.pop(eventrix_id)
            await eventrix_instance.stop()
            logger.info(f"Successfully undeployed Eventrix: {eventrix_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to undeploy Eventrix {eventrix_id}: {type(e).__name__} - {str(e)}")
            raise

    def get_status(self, eventrix_id: str) -> dict:
        """
        Retrieves the status of a deployed Eventrix instance.
        """
        if eventrix_id not in self._deployments:
            raise ValueError(f"No deployed Eventrix found with ID '{eventrix_id}'.")

        eventrix_instance, _ = self._deployments[eventrix_id]
        return eventrix_instance.status

    def get_all_deployments(self) -> list[dict]:
        """
        Retrieves all deployed Eventrix instances with their IDs, types, and configs.
        """
        return [
            {
                "id": eventrix_id,
                "type": type(eventrix_instance).__name__,
                "status": eventrix_instance.status,
                "config": dict(config),
            }
            for eventrix_id, (eventrix_instance, config) in self._deployments.items()
        ]
    
    async def shutdown(self, timeout=10.0):
        """
        Shuts down all deployed Eventrix instances within the specified timeout.
        """
        logger.info(f"Shutting down EventrixDeployer with {timeout}s timeout...")
        self._shutdown_event.set()

        # Create shutdown tasks
        shutdown_tasks = []
        for eventrix_id, (eventrix_instance, _) in list(self._deployments.items()):
            try:
                task = asyncio.create_task(eventrix_instance.stop())
                shutdown_tasks.append(task)
            except Exception as e:
                logger.error(f"Error stopping eventrix {eventrix_id}: {type(e).__name__} - {str(e)}")

        # Wait with timeout if there are any tasks
        if shutdown_tasks:
            try:
                await asyncio.wait_for(asyncio.gather(*shutdown_tasks, return_exceptions=True), timeout)
            except asyncio.TimeoutError:
                logger.warning(f"Shutdown timed out after {timeout}s")

        # Clear deployments
        self._deployments.clear()
        logger.info("EventrixDeployer shutdown complete")