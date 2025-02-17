import grpc
from generated import helloworld_pb2, helloworld_pb2_grpc

class GreeterService(helloworld_pb2_grpc.GreeterServicer):
    def SayHello(self, request, context):
        return helloworld_pb2.HelloReply(message=f"Hello, {request.name}!")

def add_services(server):
    helloworld_pb2_grpc.add_GreeterServicer_to_server(GreeterService(), server)