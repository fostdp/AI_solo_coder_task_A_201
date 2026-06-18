from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from models import SensorData
from services import SensorService, CastingService
from orchestrator import orchestrator

router = APIRouter(prefix="/api/sensor", tags=["Sensor"])

@router.post("/data")
async def submit_sensor_data(data: SensorData):
    sensor_dict = data.model_dump()
    result = SensorService.insert(sensor_dict)
    if orchestrator.running and orchestrator.current_casting_id == data.casting_id:
        sim_result = await orchestrator.process_sensor_data(sensor_dict)
        return {"status": "ok", "sensor": result, "simulation": sim_result}
    return {"status": "ok", "sensor": result}

@router.get("/latest")
async def get_latest_sensor_data(casting_id: str):
    latest = SensorService.get_latest(casting_id)
    if not latest:
        raise HTTPException(status_code=404, detail="No sensor data found")
    return latest

@router.get("/history")
async def get_sensor_history(casting_id: str, limit: int = Query(100, ge=1, le=1000)):
    return SensorService.get_history(casting_id, limit)
