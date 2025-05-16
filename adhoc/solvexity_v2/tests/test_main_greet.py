import grpc
import grpc_testing
import pytest
from solvexity.generated.greet import greet_pb2
from solvexity.generated.greet import greet_pb2_grpc
from google.protobuf import empty_pb2

from solvexity.main_greet import GreeterServicer

@pytest.fixture
def grpc_test_env():
    servicers = {
        greet_pb2.DESCRIPTOR.services_by_name['Greeter']: GreeterServicer()
    }
    fake_time = grpc_testing.strict_real_time()
    server = grpc_testing.server_from_dictionary(servicers, fake_time)
    return server, fake_time

def test_say_hello(grpc_test_env):
    server, _ = grpc_test_env

    method_descriptor = greet_pb2.DESCRIPTOR.services_by_name['Greeter'].methods_by_name['SayHello']

    request = greet_pb2.HelloRequest(name='Bob')

    rpc = server.invoke_unary_unary(
        method_descriptor,
        invocation_metadata={},
        request=request,
        timeout=1
    )

    response, trailing_metadata, code, details = rpc.termination()

    assert code == grpc.StatusCode.OK
    assert response.message == "Hello, Bob!"
