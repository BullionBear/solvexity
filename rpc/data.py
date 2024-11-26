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


api_key = ''
api_secret = ''

@method
def futures_position_information():
    c = Client(api_key, api_secret)
    return Success(c.futures_position_information())

@method
def futures_order_book(symbol, limit=5):
    c = Client(api_key, api_secret)
    return Success(c.futures_order_book(symbol=symbol, limit=limit))

@method
def futures_account_trades(symbol, limit=5):
    c = Client(api_key, api_secret)
    return Success(c.futures_account_trades(symbol=symbol, limit=limit))


@app.post("/")
async def index(request: Request):
    return Response(dispatch(await request.body()))

if __name__ == "__main__":
    shutdown = helper.Shutdown(signal.SIGINT, signal.SIGTERM)
    # Run the FastAPI app with the custom logger
    uvicorn.run()
    shutdown.wait_for_shutdown()
