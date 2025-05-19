from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel
import asyncio
import logging
from typing import Type, Dict
from hooklet.base import BaseEventrix
from hooklet.pilot import NatsPilot
from solvexity.eventrix.collection.ccxt_ochlv_emitter import CCXTOCHLVEmitter
from solvexity.service.deployer import EventrixDeployer

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Changed to DEBUG for more verbose logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the NatsPilot
pilot = NatsPilot(nats_url="nats://localhost:4222")
deployer = EventrixDeployer(pilot)

# Use the newer lifespan approach for FastAPI lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

# Define the FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# Pydantic models for request validation
class DeployRequest(BaseModel):
    eventrix_id: str
    eventrix_type: str
    config: dict

class UndeployRequest(BaseModel):
    eventrix_id: str

@app.post("/deploy")
async def deploy_eventrix(request: DeployRequest):
    """
    Deploy an Eventrix instance.
    """
    

@app.delete("/deploy")
async def undeploy_eventrix(request: UndeployRequest):
    """
    Undeploy an Eventrix instance.
    """
    

@app.get("/deploy/{eventrix_id}")
def get_eventrix_status(eventrix_id: str):
    """
    Get the status of a deployed Eventrix instance.
    """
    logger.info(f"Received status request for eventrix_id: {eventrix_id}")


@app.get("/deployments")
def get_all_deployments():
    """
    Get all deployed Eventrix instances.
    """
    logger.info("Received request for all deployments")
    deployments = deployer.get_all_deployments()
    logger.info(f"Current deployments: {[d.get('id') for d in deployments]}")
    return {"deployments": deployments}