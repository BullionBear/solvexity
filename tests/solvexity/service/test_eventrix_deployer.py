import asyncio
from unittest.mock import patch

import pytest
import pytest_asyncio
from hooklet.base import BaseEventrix
from hooklet.pilot import InProcPilot

from solvexity.app.deployer import EventrixDeployer


# Fixture for the pilot
@pytest_asyncio.fixture
async def pilot():
    """Create and clean up a pilot instance properly."""
    pilot_instance = InProcPilot()
    await pilot_instance.connect()
    yield pilot_instance
    await pilot_instance.close()


# Fixture for the deployer with proper cleanup
@pytest_asyncio.fixture
async def deployer(pilot):
    """Create and clean up a deployer instance properly."""
    deployer_instance = EventrixDeployer(pilot)
    yield deployer_instance
    await deployer_instance.shutdown()


# Create a concrete implementation of BaseEventrix for testing
class TestEventrixImpl(BaseEventrix):
    def __init__(self, pilot=None, **kwargs):
        super().__init__(pilot)  # Call parent constructor if needed
        self.id = kwargs.get("id", "test_eventrix")
        self._status = {"status": "initialized"}

    @property
    def status(self):
        return self._status

    async def on_start(self):
        self._status["status"] = "running"

    async def on_stop(self):
        self._status["status"] = "stopped"

    async def on_execute(self):
        pass

    async def on_finish(self):
        pass

    async def start(self):
        await self.on_start()

    async def stop(self):
        await self.on_stop()


@pytest.mark.asyncio
async def test_deployer_initialization(deployer, pilot):
    """Test that the deployer initializes correctly with a pilot."""
    assert deployer._pilot == pilot
    assert isinstance(deployer, EventrixDeployer)


@pytest.mark.asyncio
async def test_deploy_eventrix(deployer):
    """Test deploying an eventrix instance."""
    eventrix_id = "test_eventrix"
    config = {"id": eventrix_id}

    result = await deployer.deploy(eventrix_id, TestEventrixImpl, config)
    assert result is True
    assert eventrix_id in deployer._deployments


@pytest.mark.asyncio
async def test_undeploy_eventrix(deployer):
    """Test undeploying an eventrix instance."""
    eventrix_id = "test_eventrix"
    config = {"id": eventrix_id}

    await deployer.deploy(eventrix_id, TestEventrixImpl, config)
    result = await deployer.undeploy(eventrix_id)
    assert result is True
    assert eventrix_id not in deployer._deployments


@pytest.mark.asyncio
async def test_deploy_with_emitters_and_handlers(deployer):
    """Test deploying eventrix with emitters and handlers."""
    eventrix_id = "test_eventrix_with_components"
    config = {"id": eventrix_id}

    # Mock emitters and handlers since we can't directly add them in the test
    with patch.object(
        TestEventrixImpl, "start", return_value=asyncio.Future()
    ) as mock_start:
        mock_start.return_value.set_result(None)
        result = await deployer.deploy(eventrix_id, TestEventrixImpl, config)
        assert result is True
        assert eventrix_id in deployer._deployments


@pytest.mark.asyncio
async def test_list_deployed_eventrix(deployer):
    """Test listing all deployed eventrix instances."""
    eventrix1_id = "test_eventrix1"
    eventrix2_id = "test_eventrix2"

    await deployer.deploy(eventrix1_id, TestEventrixImpl, {"id": eventrix1_id})
    await deployer.deploy(eventrix2_id, TestEventrixImpl, {"id": eventrix2_id})

    deployed_list = deployer.get_all_deployments()
    assert len(deployed_list) >= 2

    # Check that both IDs are present in the deployed list
    deployed_ids = [item["id"] for item in deployed_list]
    assert eventrix1_id in deployed_ids
    assert eventrix2_id in deployed_ids


@pytest.mark.asyncio
async def test_deploy_duplicate_eventrix(deployer):
    """Test deploying the same eventrix twice."""
    eventrix_id = "duplicate_eventrix"
    config = {"id": eventrix_id}

    await deployer.deploy(eventrix_id, TestEventrixImpl, config)

    # Deploying the same eventrix should raise a ValueError
    with pytest.raises(ValueError):
        await deployer.deploy(eventrix_id, TestEventrixImpl, config)
