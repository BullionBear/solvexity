import asyncio
import logging
from typing import Any, Dict, Type

from hooklet.base import BasePilot
from solvexity.trader.base import ConfigNode
from solvexity.trader.factory import TraderFactory
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Deployer:
    """
    Deployer is a class that provides an interface for deploying, undeploying,
    and managing trader instances.
    """

    def __init__(self, pilot: BasePilot):
        """
        Initializes the Deployer instance.
        """
        self._pilot = pilot
        self._trader_factory = TraderFactory(pilot)
        self._deployments: list[tuple[ConfigNode, Dict[str, Any]]] = []
        self._shutdown_event = asyncio.Event()

    async def __aenter__(self):
        if not self._pilot.is_connected():
            await self._pilot.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown()

    def is_node_registered(self, node_id: str) -> bool:
        for node, _ in self._deployments:
            if node.node_id == node_id:
                return True
        return None

    async def deploy(
        self,
        node_type: str,
        config: dict[str, Any],
    ):
        """
        Deploys an Eventrix instance.
        """
        try:
            node = self._trader_factory.create(node_type, config)
            # Start the node
            await node.start()
            self._deployments.append((node, config))
            logger.info(f"Successfully deployed {node_type}: {node.node_id}")
            return True
        except Exception as e:
            logger.error(
                f"Failed to deploy {node_type}: {type(e).__name__} - {str(e)}"
            )
            # Clean up if initialization succeeded but start failed
            if node.node_id in self._deployments:
                node, _ = self._deployments.pop(node.node_id)
                try:
                    await node.stop()
                except Exception:
                    pass
            raise

    async def undeploy(self, node_id: str) -> bool:
        """
        Undeploys an existing node instance.
        """
        if node_id not in [node.node_id for node, _ in self._deployments]:
            return False

        try:
            node, _ = self._deployments.pop(node_id)
            await node.stop()
            logger.info(f"Successfully undeployed {node.node_id}")
            return True
        except Exception as e:
            logger.error(
                f"Failed to undeploy {node.node_id}: {type(e).__name__} - {str(e)}"
            )
            return False

    def get_status(self, node_id: str) -> dict:
        """
        Retrieves the status of a deployed Eventrix instance.
        """
        for node, _ in self._deployments:
            if node.node_id == node_id:
                return node.status
        return {}

    def get_all_deployments(self) -> list[dict]:
        """
        Retrieves all deployed Eventrix instances with their IDs, types, and configs.
        """
        return [
            {
                "id": node.node_id,
                "type": type(node).__name__,
                "status": node.status,
                "config": dict(config),
            }
            for node, config in self._deployments
        ]

    async def shutdown(self, timeout=10.0):
        """
        Shuts down all deployed config nodes within the specified timeout.
        """
        logger.info(f"Shutting down Deployer with {timeout}s timeout...")
        self._shutdown_event.set()

        # Create shutdown tasks
        shutdown_tasks = []
        for node, _ in self._deployments:
            try:
                shutdown_tasks.append(node.stop())
            except Exception:
                pass

        # Wait with timeout if there are any tasks
        if shutdown_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*shutdown_tasks, return_exceptions=True), timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"Shutdown timed out after {timeout}s")

        # Clear deployments
        self._deployments.clear()
        logger.info("Deployer shutdown complete")
