import pytest
import asyncio
from unittest.mock import patch
from typing import Any, Dict

from hooklet.pilot import InProcPilot
from hooklet.eventrix.collection import ExampleEmitter, ExampleHandler
from hooklet.base import BaseEventrix

from solvexity.service.deployer import EventrixDeployer


# Fixture for the pilot
@pytest.fixture
async def pilot():
    """Create and clean up a pilot instance properly."""
    pilot_instance = InProcPilot()
    await pilot_instance.connect()
    yield pilot_instance
    await pilot_instance.close()


# Fixture for the deployer with proper cleanup
@pytest.fixture
async def deployer(pilot):
    """Create and clean up a deployer instance properly."""
    deployer_instance = EventrixDeployer(pilot)
    yield deployer_instance
    await deployer_instance.shutdown()

