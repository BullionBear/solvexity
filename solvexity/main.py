from concurrent import futures
import redis
import os
import sqlalchemy
import grpc
import solvexity.analytic as ans
import solvexity.generated.solvexity.solvexity_pb2 as solvexity_pb2
import solvexity.generated.solvexity.solvexity_pb2_grpc as solvexity_pb2_grpc
from google.protobuf.timestamp_pb2 import Timestamp
import datetime

from dotenv import load_dotenv

load_dotenv()

class SolvexityServicer(solvexity_pb2_grpc.SolvexityServicer):
    def __init__(self, solver: ans.Solver):
        self.solver = solver
    
    def Solve(self, request: solvexity_pb2.SolveRequest, context: grpc.ServicerContext) -> solvexity_pb2.SolveResponse:
        try:
            dt = request.timestamp.ToDatetime()
            ts = int(dt.timestamp() * 1000)
            print(f"Received request for symbol: {request.symbol} at {dt}")
            res = self.solver.solve(request.symbol, ts)
            return solvexity_pb2.SolveResponse(status=solvexity_pb2.SUCCESS, message=f"result {res}")
        except Exception as e:
            context.set_details(str(e))
            context.set_code(grpc.StatusCode.INTERNAL)  # or appropriate error code
            return solvexity_pb2.SolveResponse(status=solvexity_pb2.FAILURE, message="error")

def serve():
    # Resource allocation
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    sql_engine = sqlalchemy.create_engine(os.getenv("SQL_URL"))
    feed = ans.Feed(redis_client, sql_engine)
    solver = ans.Solver(feed)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    solvexity_pb2_grpc.add_SolvexityServicer_to_server(SolvexityServicer(solver), server)
    server.add_insecure_port('[::]:50052')
    print("Solvexity gRPC Server started on port 50052...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
