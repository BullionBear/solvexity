import os
import pytest
from decimal import Decimal
from solvexity.trader.config import ConfigLoader
import dotenv
import pymongo
import logging

logger = logging.getLogger(__name__)

dotenv.load_dotenv()


@pytest.fixture(scope="module")
def max_drawdown_signal():
    SOLVEXITY_MONGO_URI = os.getenv("SOLVEXITY_MONGO_URI")
    # Set up the context once per test module
    mongo_client = pymongo.MongoClient(SOLVEXITY_MONGO_URI)
    config_loader = ConfigLoader.from_db(mongo_client, "test")
    context_factory = config_loader["signals"]
    yield context_factory.get_context("max_drawdown")


def test_max_drawdown_signal(max_drawdown_signal):
    signal = max_drawdown_signal.solve()
    assert signal >= 0, "Signal should be greater than or equal to 0"