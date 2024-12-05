import os
import pytest
from decimal import Decimal
from solvexity.trader.context import ContextFactory
from solvexity.trader.config import ConfigLoader
import dotenv
import pymongo
from solvexity.dependency.notification import Color
import logging

logger = logging.getLogger(__name__)

dotenv.load_dotenv()


@pytest.fixture(scope="module")
def spot_trade_context():
    SOLVEXITY_MONGO_URI = os.getenv("SOLVEXITY_MONGO_URI")
    # Set up the context once per test module
    mongo_client = pymongo.MongoClient(SOLVEXITY_MONGO_URI)
    config_loader = ConfigLoader.from_db(mongo_client, "test")
    context_factory = config_loader["contexts"]
    yield context_factory.get_context("test_spot_trade")

def test_balance_retrieval(spot_trade_context):
    balance = spot_trade_context.get_balance("USDT")
    logger.info(f"Retrieved balance: {balance}")
    assert isinstance(balance, Decimal), "Balance should be a Decimal instance"
    assert balance >= Decimal('0'), "Balance should not be negative"