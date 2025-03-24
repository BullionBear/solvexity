import os
import grpc
import grpc_testing
import pytest
import datetime
import redis
import sqlalchemy

from google.protobuf.timestamp_pb2 import Timestamp

import solvexity.generated.solvexity.solvexity_pb2 as solvexity_pb2
import solvexity.generated.solvexity.solvexity_pb2_grpc as solvexity_pb2_grpc
import solvexity.analytic as ans
from solvexity.main import SolvexityServicer  # Adjust to your actual module path

from dotenv import load_dotenv
load_dotenv()


@pytest.fixture(scope="module")
def feed():
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    sql_engine = sqlalchemy.create_engine(os.getenv("SQL_URL"))
    return ans.Feed(redis_client, sql_engine)


@pytest.fixture(scope="module")
def solver(feed):
    return ans.Solver(feed)


@pytest.fixture
def grpc_test_server(solver):
    servicer = SolvexityServicer(solver)

    services = {
        solvexity_pb2.DESCRIPTOR.services_by_name['Solvexity']: servicer
    }
    fake_time = grpc_testing.strict_real_time()
    server = grpc_testing.server_from_dictionary(services, fake_time)
    return server, fake_time

@pytest.mark.integration
def test_solve_valid_symbol(grpc_test_server):
    server, _ = grpc_test_server

    method = solvexity_pb2.DESCRIPTOR.services_by_name['Solvexity'].methods_by_name['Solve']

    ts = Timestamp()
    ts.FromDatetime(datetime.datetime.now(datetime.timezone.utc))

    request = solvexity_pb2.SolveRequest(symbol="BTCUSDT", timestamp=ts)

    rpc = server.invoke_unary_unary(
        method_descriptor=method,
        invocation_metadata={},
        request=request,
        timeout=5
    )

    response, trailing_metadata, code, details = rpc.termination()

    assert code == grpc.StatusCode.OK
    assert response.status == solvexity_pb2.SUCCESS
    assert "BTCUSDT" in response.message
    assert isinstance(response.timestamp, Timestamp)
