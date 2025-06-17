import argparse
import yaml
from fastapi import FastAPI, HTTPException, Depends
from contextlib import asynccontextmanager
from pydantic import BaseModel
from hooklet.pilot import NatsPilot
from solvexity.app.deployer import Deployer
from solvexity.trader.factory import TraderFactory
from solvexity.logger import SolvexityLogger
from solvexity.app.dependency.deployer import DeployerSingleton

logger = SolvexityLogger().get_logger(__name__)

# Load configuration
def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--config", type=str, default="config.yaml")
args = parser.parse_args()

# Load configuration
config = load_config(args.config)
app_config = config.get("app", {
    "host": "0.0.0.0",
    "port": 8000
})
deployer_config = config.get("deployer", {})

# Initialize the deployer with configuration
DeployerSingleton.from_config(deployer_config)

nodes_config = config.get("nodes", [])

# Use the newer lifespan approach for FastAPI lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize connections and resources at startup
    deployer = DeployerSingleton.get_deployer()
    await deployer.__aenter__()
    logger.info("Connected to NATS server")

    for node_config in nodes_config:
        await deployer.deploy(node_config.get("type"), node_config.get("config"))
    
    yield
    
    # Cleanup at shutdown
    await deployer.__aexit__(None, None, None)
    logger.info("Closed connections and shut down services")

# Define the FastAPI app with lifespan
app = FastAPI(lifespan=lifespan)

# Pydantic models for request validation
class DeployRequest(BaseModel):
    node_id: str
    node_type: str
    config: dict

class UndeployRequest(BaseModel):
    node_id: str

@app.post("/deploy")
async def deploy_node(request: DeployRequest, deployer: Deployer = Depends(DeployerSingleton.get_deployer)):
    """
    Deploy an Eventrix instance using registered Eventrix types.
    """
    logger.info(f"Deploying node with ID: {request.node_id}, Type: {request.node_type}")
    try:
        
        
        if request.node_type not in deployer.available_nodes:
            raise HTTPException(
                status_code=400, 
                detail=f"Node type '{request.node_type}' is not registered. "
                      f"Available types: {deployer.available_nodes}"
            )
    
        # Get the Eventrix class from the registry
        result = await deployer.deploy(request.node_type, request.config)
        # Deploy the eventrix instance
        
        
        return {
            "success": result,
            "node_id": request.node_id,
            "message": f"Successfully deployed {request.node_type}"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to deploy eventrix: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to deploy eventrix: {str(e)}")

@app.delete("/deploy")
async def undeploy_node(request: UndeployRequest, deployer: Deployer = Depends(DeployerSingleton.get_deployer)):
    """
    Undeploy a node.
    """
    logger.info(f"Undeploying node with ID: {request.node_id}")
    try:
        result = await deployer.undeploy(request.node_id)
        return {
            "success": result,
            "node_id": request.node_id,
            "message": f"Successfully undeployed node {request.node_id}"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to undeploy node: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to undeploy node: {str(e)}")

@app.get("/deploy/{node_id}")
def get_node_status(node_id: str, deployer: Deployer = Depends(DeployerSingleton.get_deployer)):
    """
    Get the status of a deployed node.
    """
    logger.info(f"Received status request for node_id: {node_id}")
    try:
        status = deployer.get_status(node_id)
        return {
            "node_id": node_id,
            "status": status
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get status for node {node_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@app.get("/deployments")
def get_all_deployments(deployer: Deployer = Depends(DeployerSingleton.get_deployer)):
    """
    Get all deployed nodes.
    """
    logger.info("Received request for all deployments")
    deployments = deployer.get_all_deployments()
    logger.info(f"Current deployments: {[d.get('id') for d in deployments]}")
    return {"deployments": deployments}

@app.get("/nodes")
def get_available_nodes():
    """
    Get a list of all available nodes that can be deployed.
    """
    logger.info("Received request for available Eventrix types")
    types = list(TraderFactory.available_nodes)
    return {"available_types": types}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=app_config["host"], port=app_config["port"])