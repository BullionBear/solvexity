import helper.logging as logging
import random
import string
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
from app.core import settings

# Configure the logger
logging.setup_logging()
logger = logging.getLogger('server')


# Store active WebSocket connections
connected_clients: List[WebSocket] = []

# Middleware to log requests


# Lifespan function to handle startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    logger.info(f"Starting up..., mongo_uri: {settings.SOLVEXITY_MONGO_URI}")
    logger.info(f"Service: {settings.SOLVEXITY_SERVICE}")
    yield
    # Shutdown code
    logger.info("Shutting down...")
    for websocket in connected_clients:
        await websocket.close(code=1001)  # Normal closure
    connected_clients.clear()
    logger.info("All WebSocket connections closed.")

# Initialize FastAPI with the lifespan function
app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def log_requests(request, call_next):
    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(f"rid={idem} start request path={request.url.path}")
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f"rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}")

    return response

# HTTP Endpoint
@app.get("/")
async def read_root():
    return {"message": "Hello, HTTP!"}

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
    uvicorn.run(app, host="0.0.0.0", port=30819, log_config=logging.LOGGING_CONFIG)
