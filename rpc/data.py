from pprint import pprint
from binance.client import Client
from fastapi import FastAPI, Request, Response
from jsonrpcserver import Result, Success, dispatch, method
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
    from helper.logging import LOGGING_CONFIG

    # Run the FastAPI app with the custom logger
    uvicorn.run(
        app="__main__:app",  # Reference to the app variable
        host="0.0.0.0",
        port=5000,
        log_config=LOGGING_CONFIG,
        log_level="info",
    )
