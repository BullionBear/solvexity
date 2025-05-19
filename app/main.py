from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel
import asyncio
import logging
from typing import Type, Dict
from hooklet.base import BaseEventrix
from hooklet.pilot import NatsPilot
from solvexity.eventrix.collection.ccxt_ochlv_emitter import CCXTOCHLVEmitter, CCTXOCHLVConfig
from solvexity.eventrix.config import ConfigType
from solvexity.service.deployer import EventrixDeployer

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more verbose logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the NatsPilot
pilot = NatsPilot(nats_url="nats://localhost:4222")
deployer = EventrixDeployer(pilot)

# Use the newer lifespan approach for FastAPI lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle application startup and shutdown events.
    """
    # Startup code
    logger.info("Starting application and connecting to NATS...")
    try:
        await pilot.connect()
        logger.info("NatsPilot started successfully")
    except Exception as e:
        logger.error(f"Failed to start NatsPilot: {type(e).__name__} - {str(e)}")
        raise

    logger.info("Application startup complete")
    yield

    # Shutdown code
    logger.info("Application shutdown initiated")
    
    # Print deployment state before shutdown for debugging
    logger.debug(f"Active deployments before shutdown: {deployer.get_all_deployments()}")
    
    # Shutdown the deployer first to stop all eventrix instances
    await deployer.shutdown()
    
    # Then stop the pilot
    try:
        await pilot.close()
        logger.info("Pilot stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping pilot: {type(e).__name__} - {str(e)}")
    
    # Ensure any remaining tasks are cleaned up
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        if not task.done():
            task.cancel()
            
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    
    logger.info("Application shutdown complete")

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
    logger.info(f"Received deploy request for eventrix_id: {request.eventrix_id}, type: {request.eventrix_type}")
    
    # Map eventrix_type string to actual class
    eventrix_type_mapping: Dict[str, tuple[Type[BaseEventrix], Type[ConfigType]]] = {
        "CCXTOCHLVEmitter": (CCXTOCHLVEmitter, CCTXOCHLVConfig),
        # Add more mappings here
    }

    if request.eventrix_type not in eventrix_type_mapping:
        logger.warning(f"Invalid Eventrix type requested: {request.eventrix_type}")
        raise HTTPException(status_code=400, detail=f"Invalid Eventrix type: {request.eventrix_type}")

    eventrix_type, eventrix_config_type = eventrix_type_mapping[request.eventrix_type]
    
    try:
        # Validate and create config
        eventrix_config = eventrix_config_type(**request.config)
        logger.debug(f"Created config: {eventrix_config}")
        
        # Deploy the eventrix
        await deployer.deploy(request.eventrix_id, eventrix_type, eventrix_config)
        
        # Verify deployment was successful
        deployments = deployer.get_all_deployments()
        deployment_ids = [d.get("id") for d in deployments]
        logger.info(f"Current deployments after adding {request.eventrix_id}: {deployment_ids}")
        
        return {
            "message": f"Eventrix '{request.eventrix_id}' deployed successfully.",
            "deployments": deployment_ids
        }
    except ValueError as e:
        logger.error(f"Failed to deploy {request.eventrix_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deploying {request.eventrix_id}: {type(e).__name__} - {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/undeploy")
async def undeploy_eventrix(request: UndeployRequest):
    """
    Undeploy an Eventrix instance.
    """
    logger.info(f"Received undeploy request for eventrix_id: {request.eventrix_id}")
    
    # Check current deployments before undeploying
    deployments = deployer.get_all_deployments()
    deployment_ids = [d.get("id") for d in deployments]
    logger.info(f"Current deployments before undeploying: {deployment_ids}")
    
    try:
        await deployer.undeploy(request.eventrix_id)
        logger.info(f"Successfully undeployed {request.eventrix_id}")
        
        # Verify deployment was removed
        updated_deployments = deployer.get_all_deployments()
        updated_ids = [d.get("id") for d in updated_deployments]
        logger.info(f"Current deployments after undeploying: {updated_ids}")
        
        return {
            "message": f"Eventrix '{request.eventrix_id}' undeployed successfully.",
            "deployments": updated_ids
        }
    except ValueError as e:
        logger.error(f"Failed to undeploy {request.eventrix_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error undeploying {request.eventrix_id}: {type(e).__name__} - {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/status/{eventrix_id}")
def get_eventrix_status(eventrix_id: str):
    """
    Get the status of a deployed Eventrix instance.
    """
    logger.info(f"Received status request for eventrix_id: {eventrix_id}")
    
    try:
        status = deployer.get_status(eventrix_id)
        return {"eventrix_id": eventrix_id, "status": status}
    except ValueError as e:
        logger.error(f"Status request failed for {eventrix_id}: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/deployments")
def get_all_deployments():
    """
    Get all deployed Eventrix instances.
    """
    logger.info("Received request for all deployments")
    deployments = deployer.get_all_deployments()
    logger.info(f"Current deployments: {[d.get('id') for d in deployments]}")
    return {"deployments": deployments}