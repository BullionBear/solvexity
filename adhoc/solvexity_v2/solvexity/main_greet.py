from concurrent import futures
import grpc
import time

from solvexity.generated.greet import greet_pb2
from solvexity.generated.greet import greet_pb2_grpc

# Implement the service defined in proto
class GreeterServicer(greet_pb2_grpc.GreeterServicer):
    def SayHello(self, request, context):
        name = request.name
        reply_message = f"Hello, {name}!"
        print(f"Received request for name: {name}")
        return greet_pb2.HelloReply(message=reply_message)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    greet_pb2_grpc.add_GreeterServicer_to_server(GreeterServicer(), server)
    server.add_insecure_port('[::]:50054')
    print("Starting gRPC server on port 50054...")
    server.start()
    try:
        while True:
            time.sleep(86400)  # keep server alive
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
