import grpc
import time
from concurrent import futures

# Import generated gRPC code from the compiled `.proto` files
from generated import helloworld_pb2_grpc
from server.services.helloworld_service import GreeterService  # Custom service implementation

# Define the gRPC server
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Register services
    helloworld_pb2_grpc.add_GreeterServicer_to_server(GreeterService(), server)

    # Bind the server to a port
    server.add_insecure_port('[::]:50051')
    
    print("gRPC Server is running on port 50051...")
    
    server.start()
    
    try:
        while True:
            time.sleep(86400)  # Keep the server running
    except KeyboardInterrupt:
        print("Shutting down server...")
        server.stop(0)

# Run the gRPC server
if __name__ == '__main__':
    serve()
