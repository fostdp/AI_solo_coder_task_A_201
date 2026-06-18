from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any

class SensorData(BaseModel):
    casting_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    wax_temperature: float = Field(..., ge=0, le=2000)
    pouring_temperature: float = Field(..., ge=0, le=2000)
    shell_permeability: float = Field(..., ge=0, le=100)
    filling_progress: float = Field(..., ge=0, le=100)

class SimulationStatus(BaseModel):
    casting_id: str
    status: str
    filling_progress: float
    elapsed_time: int
    total_steps: int
    current_step: int

class TemperaturePoint(BaseModel):
    x: float
    y: float
    z: float
    temperature: float

class TemperatureField(BaseModel):
    step: int
    points: List[TemperaturePoint]
    max_temperature: float
    min_temperature: float

class DefectPrediction(BaseModel):
    id: str
    casting_id: str
    position: Dict[str, float]
    niyama_value: float
    volume: float
    severity: str
    defect_type: str
    detected_at: datetime

class AlertModel(BaseModel):
    id: str
    casting_id: str
    alert_type: str
    severity: str
    message: str
    data: Dict[str, Any]
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)

class CastingTask(BaseModel):
    id: str
    name: str
    status: str
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    parameters: Dict[str, Any]
