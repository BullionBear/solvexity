import helper.logging as logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import pymongo
import signal
from trader.config import ConfigLoader
from typing import List
from app.core import settings
from helper.shutdown import Shutdown
import threading

# Configure the logger
logging.setup_logging()
logger = logging.getLogger('server')


# Store active WebSocket connections
connected_clients: List[WebSocket] = []

# Middleware to log requests


# Lifespan function to handle startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Resource
    shutdown = Shutdown(signal.SIGINT, signal.SIGTERM)
    # Startup code
    mongo_client = pymongo.MongoClient(settings.SOLVEXITY_MONGO_URI)
    # config_loader = ConfigLoader.from_db(mongo_client, "system")
    db = mongo_client.get_database("solvexity")
    collection = db['service']
    logger.info(f"Service: {settings.SOLVEXITY_SERVICE}")
    service_config = collection.find_one({"name": settings.SOLVEXITY_SERVICE}, {"_id": 0})
    logger.info(f"Service config: {service_config}")
    app.state.service_config = service_config
    config_loader = ConfigLoader.from_db(mongo_client, service_config["ref"])
    app.state.config_loader = config_loader
    threads = []
    if service_config["runtime"] == "trade":
        from app.runtime.trade import trading_runtime
        threads.append(threading.Thread(target=trading_runtime, args=(config_loader, shutdown, service_config["trader"], service_config["feed"])))
    elif service_config["runtime"] == "feed":
        from app.runtime.feed import feed_runtime
        threads.append(threading.Thread(target=feed_runtime, args=(config_loader, shutdown, service_config["config"]["feed"])))
    else:
        raise ValueError(f"Service runtime '{service_config['runtime']}' not supported. Available runtimes: ['trade', 'feed']")
    threads[0].start()
    yield
    # Shutdown code
    logger.info("Shutting down...")
    for websocket in connected_clients:
        await websocket.close(code=1001)  # Normal closure
    connected_clients.clear()
    logger.info("All WebSocket connections closed.")
    threads[0].join()

# Initialize FastAPI with the lifespan function
app = FastAPI(lifespan=lifespan)

# HTTP Endpoint
@app.get("/service")
async def config():
    return JSONResponse(app.state.service_config)

@app.get("/system")
async def config():
    return JSONResponse(app.state.config_loader.get_config())

# WebSocket Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received: {data}")
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    finally:
        connected_clients.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=30819)
