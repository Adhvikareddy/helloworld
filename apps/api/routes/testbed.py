from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

router = APIRouter()

# In-memory store for active channel testbed parameters
_testbed_state: Dict[str, float] = {
    "disturbance": 0.0
}

class ChannelTestbedRequest(BaseModel):
    disturbance: float = Field(..., ge=0.0, le=1.0, description="Noise parameter p in [0.0, 1.0]")
    operator_signature: Optional[str] = Field(None, description="Operator signature for lab control")

class ChannelTestbedResponse(BaseModel):
    status: str
    disturbance: float

@router.post("/channel", response_model=ChannelTestbedResponse)
def set_channel_disturbance(req: ChannelTestbedRequest):
    _testbed_state["disturbance"] = req.disturbance
    return ChannelTestbedResponse(
        status="CONFIGURED",
        disturbance=req.disturbance
    )

@router.get("/channel", response_model=ChannelTestbedResponse)
def get_channel_disturbance():
    return ChannelTestbedResponse(
        status="ACTIVE",
        disturbance=_testbed_state["disturbance"]
    )

def get_active_disturbance() -> float:
    return _testbed_state["disturbance"]
