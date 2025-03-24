from concurrent import futures
import grpc
import solvexity.generated.solvexity.solvexity_pb2 as solvexity_pb2
import solvexity.generated.solvexity.solvexity_pb2_grpc as solvexity_pb2_grpc
from google.protobuf.timestamp_pb2 import Timestamp
import datetime

class SolvexityServicer(solvexity_pb2_grpc.SolvexityServicer):
    def Solve(self, request, context):
        print(f"Received request for symbol: {request.symbol} at {request.timestamp}")
        
        # Example logic: check if the symbol is valid
        if request.symbol:
            status = solvexity_pb2.SUCCESS
            message = f"Solution processed for symbol: {request.symbol}"
        else:
            status = solvexity_pb2.FAIL
            message = "Invalid symbol"
        
        # Create response timestamp
        current_time = datetime.datetime.now(datetime.timezone.utc)
        response_timestamp = Timestamp()
        response_timestamp.FromDatetime(current_time)
        
        return solvexity_pb2.SolveResponse(
            status=status,
            message=message,
            timestamp=response_timestamp
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    solvexity_pb2_grpc.add_SolvexityServicer_to_server(SolvexityServicer(), server)
    server.add_insecure_port('[::]:50052')
    print("Solvexity gRPC Server started on port 50052...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
