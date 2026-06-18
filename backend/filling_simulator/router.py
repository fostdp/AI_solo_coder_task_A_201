from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from .service import filling_simulator
from common.mongo_client import get_db


class StartRequest(BaseModel):
    casting_id: str


router = APIRouter(prefix="/api/simulation", tags=["Simulation"])


@router.post("/start")
async def start_simulation(req: StartRequest):
    db = get_db()
    task = db.castings.find_one({"id": req.casting_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Casting task not found")
    await filling_simulator.start(req.casting_id)
    return {"status": "started", "casting_id": req.casting_id}


@router.post("/stop")
async def stop_simulation():
    await filling_simulator.stop()
    return {"status": "stopped"}


@router.get("/status")
async def get_simulation_status():
    return filling_simulator.get_status()


@router.get("/filling")
async def get_filling_data(casting_id: str):
    db = get_db()
    steps = list(
        db.simulations.find({"casting_id": casting_id}, {"_id": 0}).sort("step_number", 1)
    )
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
    db = get_db()
    steps = list(
        db.simulations.find({"casting_id": casting_id}, {"_id": 0}).sort("step_number", 1)
    )
    return [
        {
            "step": s["step_number"],
            "temperature": s["data"].get("temperature", {}),
        }
        for s in steps
    ]
