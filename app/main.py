from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel
from hooklet.pilot import NatsPilot
from solvexity.service.deployer import EventrixDeployer
from solvexity.service.registry import eventrix_registry
from hooklet.logger import get_logger

logger = get_logger(__name__)


# Initialize the NatsPilot
pilot = NatsPilot(nats_url="nats://localhost:4222")
deployer = EventrixDeployer(pilot)

# Use the newer lifespan approach for FastAPI lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize connections and resources at startup
    
    await pilot.connect()
    logger.info("Connected to NATS server")
    
    yield
    
    # Cleanup at shutdown
    await deployer.shutdown()
    await pilot.close()
    logger.info("Closed connections and shut down services")

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
    Deploy an Eventrix instance using registered Eventrix types.
    """
    logger.info(f"Deploying eventrix with ID: {request.eventrix_id}, Type: {request.eventrix_type}")
    try:
        # Get the Eventrix class from the registry
        eventrix_class = eventrix_registry.get(request.eventrix_type)
        
        if not eventrix_class:
            raise HTTPException(
                status_code=400, 
                detail=f"Eventrix type '{request.eventrix_type}' is not registered. "
                      f"Available types: {list(eventrix_registry.get_all().keys())}"
            )
        
        # Deploy the eventrix instance
        result = await deployer.deploy(
            request.eventrix_id, 
            eventrix_class, 
            request.config
        )
        
        return {
            "success": result,
            "eventrix_id": request.eventrix_id,
            "message": f"Successfully deployed {request.eventrix_type}"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to deploy eventrix: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to deploy eventrix: {str(e)}")

@app.delete("/deploy")
async def undeploy_eventrix(request: UndeployRequest):
    """
    Undeploy an Eventrix instance.
    """
    logger.info(f"Undeploying eventrix with ID: {request.eventrix_id}")
    try:
        result = await deployer.undeploy(request.eventrix_id)
        return {
            "success": result,
            "eventrix_id": request.eventrix_id,
            "message": f"Successfully undeployed eventrix {request.eventrix_id}"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to undeploy eventrix: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to undeploy eventrix: {str(e)}")

@app.get("/deploy/{eventrix_id}")
def get_eventrix_status(eventrix_id: str):
    """
    Get the status of a deployed Eventrix instance.
    """
    logger.info(f"Received status request for eventrix_id: {eventrix_id}")
    try:
        status = deployer.get_status(eventrix_id)
        return {
            "eventrix_id": eventrix_id,
            "status": status
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get status for eventrix {eventrix_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@app.get("/deployments")
def get_all_deployments():
    """
    Get all deployed Eventrix instances.
    """
    logger.info("Received request for all deployments")
    deployments = deployer.get_all_deployments()
    logger.info(f"Current deployments: {[d.get('id') for d in deployments]}")
    return {"deployments": deployments}

@app.get("/eventrix-types")
def get_available_eventrix_types():
    """
    Get a list of all available Eventrix types that can be deployed.
    """
    logger.info("Received request for available Eventrix types")
    types = list(eventrix_registry.get_all().keys())
    return {"available_types": types}