import argparse
from binance.client import Client
from fastapi import FastAPI, Request, Response
import helper
import signal
from jsonrpcserver import Result, Success, dispatch, method
from trader.config import ConfigLoader
import uvicorn

app = FastAPI()

@method
def ping() -> Result:
    return Success("pong")

@method
def add(a: int, b: int) -> Result:
    return Success(a + b)


@app.post("/")
async def index(request: Request):
    return Response(dispatch(await request.body()))

if __name__ == "__main__":
    shutdown = helper.Shutdown(signal.SIGINT, signal.SIGTERM)
    # Run the FastAPI app with the custom logger
    uvicorn.run()
    shutdown.wait_for_shutdown()
