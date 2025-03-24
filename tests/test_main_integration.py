import pytest
import os
import redis
import sqlalchemy
from concurrent import futures
import grpc
from google.protobuf.timestamp_pb2 import Timestamp
import datetime
import solvexity.analytic as ans
import solvexity.generated.solvexity.solvexity_pb2_grpc as solvexity_pb2_grpc
import solvexity.generated.solvexity.solvexity_pb2 as solvexity_pb2
from solvexity.main import SolvexityServicer

@pytest.fixture(scope='module')
def grpc_add_to_server():
    return solvexity_pb2_grpc.add_SolvexityServicer_to_server

@pytest.fixture(scope='module')
def grpc_servicer():
    # Set up your dependencies here
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    sql_engine = sqlalchemy.create_engine(os.getenv("SQL_URL"))
    feed = ans.Feed(redis_client, sql_engine)
    solver = ans.Solver(feed)
    return SolvexityServicer(solver)

@pytest.fixture(scope='module')
def grpc_stub_cls(grpc_channel):
    return solvexity_pb2_grpc.SolvexityStub

@pytest.mark.integration
def test_solve_method(grpc_stub):
    # Create a timestamp for the request
    pbts = Timestamp()
    pbts.FromDatetime(datetime.datetime(2024, 12, 25, 8, 0, 0, tzinfo=datetime.timezone.utc))
    # Create the request object
    request = solvexity_pb2.SolveRequest(
        symbol="BTCUSDT",
        timestamp=pbts
    )

    # Make the gRPC call
    response = grpc_stub.Solve(request)

    # Assert the response
    assert response.status == solvexity_pb2.SUCCESS
    assert "Solution processed for symbol: BTCUSDT" in response.message
    assert isinstance(response.timestamp, Timestamp)
