import os
import pytest
import redis
import sqlalchemy
from solvexity.analytic.feed import Feed
from solvexity.analytic.solver import Solver

from dotenv import load_dotenv

load_dotenv()

@pytest.fixture(scope="module")
def redis_client():
    r = redis.Redis(host='localhost', port=6379, db=0)  # Use a test Redis instance
    yield r
    r.flushdb()  # Clean up after test

@pytest.fixture(scope="module")
def sql_engine():
    sql_url = os.getenv("SQL_URL")
    engine = sqlalchemy.create_engine(sql_url)
    yield engine
    engine.dispose()

@pytest.fixture(scope="module")
def feed(redis_client, sql_engine):
    feed = Feed(cache=redis_client, sql_engine=sql_engine)
    yield feed
    feed.close()

@pytest.mark.integration
def test_solver_solve(feed):
    solver = Solver(feed)
    solver.solve("BTCUSDT", 1641379200000)
    assert True