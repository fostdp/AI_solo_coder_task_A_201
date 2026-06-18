from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from .service import dtu_service


class SensorDataModel(BaseModel):
    casting_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    wax_temperature: float = Field(..., ge=0, le=2000)
    pouring_temperature: float = Field(..., ge=0, le=2000)
    shell_permeability: float = Field(..., ge=0, le=100)
    filling_progress: float = Field(..., ge=0, le=100)


router = APIRouter(prefix="/api/sensor", tags=["Sensor"])


@router.post("/data")
async def submit_sensor_data(data: SensorDataModel):
    result = await dtu_service.process_sensor_data(data.model_dump())
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("errors"))
    return result


@router.get("/latest")
async def get_latest_sensor_data(casting_id: str):
    latest = await dtu_service.get_latest(casting_id)
    if not latest:
        raise HTTPException(status_code=404, detail="No sensor data found")
    return latest


@router.get("/history")
async def get_sensor_history(casting_id: str, limit: int = Query(100, ge=1, le=1000)):
    return await dtu_service.get_history(casting_id, limit)
