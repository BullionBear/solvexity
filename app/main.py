from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Type
from hooklet.base import BaseEventrix
from hooklet.pilot import NatsPilot
from solvexity.eventrix.collection.ccxt_ochlv_emitter import CCXTOCHLVEmitter, CCTXOCHLVConfig
from solvexity.eventrix.config import ConfigType
from solvexity.service.deployer import EventrixDeployer

# Define the FastAPI app
app = FastAPI()

pilot = NatsPilot(nats_url="nats://localhost:4222")
deployer = EventrixDeployer(pilot)

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
    # Map eventrix_type string to actual class (you need to define this mapping)
    eventrix_type_mapping: dict[str, tuple[Type[BaseEventrix], Type[ConfigType]]] = {
        "CCXTOCHLVEmitter": (CCXTOCHLVEmitter, CCTXOCHLVConfig),  # Example mapping
        # Add more mappings here
    }

    if request.eventrix_type not in eventrix_type_mapping:
        raise HTTPException(status_code=400, detail="Invalid Eventrix type.")

    eventrix_type, eventrix_config_type = eventrix_type_mapping[request.eventrix_type]
    eventrix_config = eventrix_config_type(**request.config)

    try:
        await deployer.deploy(request.eventrix_id, eventrix_type, eventrix_config)
        return {"message": f"Eventrix '{request.eventrix_id}' deployed successfully."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/undeploy")
async def undeploy_eventrix(request: UndeployRequest):
    """
    Undeploy an Eventrix instance.
    """
    try:
        await deployer.undeploy(request.eventrix_id)
        return {"message": f"Eventrix '{request.eventrix_id}' undeployed successfully."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/status/{eventrix_id}")
def get_eventrix_status(eventrix_id: str):
    """
    Get the status of a deployed Eventrix instance.
    """
    try:
        status = deployer.get_status(eventrix_id)
        return {"eventrix_id": eventrix_id, "status": status}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/deployments")
def get_all_deployments():
    """
    Get all deployed Eventrix instances.
    """
    deployments = deployer.get_all_deployments()
    return {"deployments": deployments}