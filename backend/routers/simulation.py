from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from orchestrator import orchestrator
from services import SimulationRepository, CastingService

router = APIRouter(prefix="/api/simulation", tags=["Simulation"])

class StartRequest(BaseModel):
    casting_id: str

@router.post("/start")
async def start_simulation(req: StartRequest):
    task = CastingService.get_by_id(req.casting_id)
    if not task:
        raise HTTPException(status_code=404, detail="Casting task not found")
    await orchestrator.start(req.casting_id)
    return {"status": "started", "casting_id": req.casting_id}

@router.post("/stop")
async def stop_simulation():
    await orchestrator.stop()
    return {"status": "stopped"}

@router.get("/status")
async def get_simulation_status():
    return orchestrator.get_status()

@router.get("/filling")
async def get_filling_data(casting_id: str):
    steps = SimulationRepository.get_steps(casting_id)
    return [
        {
            "step": s["step_number"],
            "filling_ratio": s["data"].get("filling_ratio", 0),
            "filling": s["data"].get("filling", {}),
        }
        for s in steps
    ]

@router.get("/temperature")
async def get_temperature_data(casting_id: str):
    steps = SimulationRepository.get_steps(casting_id)
    return [
        {
            "step": s["step_number"],
            "temperature": s["data"].get("temperature", {}),
        }
        for s in steps
    ]
