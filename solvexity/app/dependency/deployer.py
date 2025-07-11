import asyncio
from solvexity.logger import SolvexityLogger
from typing import Any, Dict
from hooklet.base import Pilot
from hooklet.base.node import Node, EventType
from solvexity.trader.factory import TraderFactory
from hooklet.pilot import NatsPilot

logger = SolvexityLogger().get_logger(__name__)

class Deployer:
    """
    Deployer is a class that provides an interface for deploying, undeploying,
    and managing trader instances.
    """

    def __init__(self, pilot: Pilot):
        """
        Initializes the Deployer instance.
        """
        self._pilot = pilot
        self._trader_factory = TraderFactory(pilot)
        self._deployments: list[tuple[Node, Dict[str, Any]]] = []
        self._shutdown_event = asyncio.Event()

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "Deployer":
        logger.info(f"Deployer from config: {config}")
        pilot_config = config.get("pilot", {})
        if pilot_config.get("type") == "nats":
            urls = pilot_config.get("urls", ["nats://localhost:4222"])
            options = pilot_config.get("options", {})
            
            nats_config = {
                "allow_reconnect": False,  # Don't retry on initial connection failure
                "connect_timeout": 5,      # 5 second timeout for connection attempts
                **options  # Allow config to override these defaults
            }
            
            pilot = NatsPilot(urls, **nats_config)
        else:
            raise ValueError(f"Unknown pilot type: {config.get('type')}")
        return cls(pilot)

    async def __aenter__(self):
        if not self._pilot.is_connected():
            logger.info("Attempting to connect to NATS server...")
            await self._pilot.connect()
            logger.info("Successfully connected to NATS server")
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
    ) -> bool:
        """
        Deploys a ConfigNode instance.
        """
        try:
            node = self._trader_factory.create(node_type, config)
            # Start the node
            node.register(event_type=EventType.ERROR, coroutine=node.close()) # circuit breaker
            await node.start()
            self._deployments.append((node, config))
            logger.info(f"Successfully deployed {node_type}: {node.name}")
            return True
        except Exception as e:
            logger.error(
                f"Failed to deploy {node_type}: {type(e).__name__} - {str(e)}", exc_info=True
            )
            return False

    async def undeploy(self, node_id: str) -> bool:
        """
        Undeploys an existing node instance.
        """
        try:
            node, _ = next((node for node, _ in self._deployments if node.node_id == node_id), None)
            if node is None:
                logger.error(f"Node {node_id} not found")
                return False
            await node.stop()
            logger.info(f"Successfully undeployed {node.node_id}")
            return True
        except Exception as e:
            logger.error(
                f"Failed to undeploy {node.node_id}: {type(e).__name__} - {str(e)}"
            )
            return False


    def get_all_deployments(self) -> list[dict]:
        """
        Retrieves all deployed Eventrix instances with their IDs, types, and configs.
        """
        return [
            {
                "id": node.node_id,
                "type": type(node).__name__,
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
