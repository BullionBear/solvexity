from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List

app = FastAPI()

# Store active WebSocket connections
connected_clients: List[WebSocket] = []

# Lifespan function to handle startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    print("Starting up...")
    yield
    # Shutdown code
    print("Shutting down...")
    for websocket in connected_clients:
        await websocket.close(code=1001)  # Normal closure
    connected_clients.clear()
    print("All WebSocket connections closed.")

# Initialize FastAPI with the lifespan function
app = FastAPI(lifespan=lifespan)

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
            print(f"Received: {data}")
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    finally:
        connected_clients.remove(websocket)
