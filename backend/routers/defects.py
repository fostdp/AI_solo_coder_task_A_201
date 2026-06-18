from fastapi import APIRouter, Query
from typing import Optional
from services import DefectRepository, SimulationRepository

router = APIRouter(prefix="/api/defects", tags=["Defects"])

@router.get("/predictions")
async def get_defect_predictions(casting_id: str, severity: Optional[str] = None):
    defects = DefectRepository.get_by_casting(casting_id)
    if severity:
        defects = [d for d in defects if d.get("severity") == severity]
    return defects

@router.get("/niyama")
async def get_niyama_data(casting_id: str):
    steps = SimulationRepository.get_steps(casting_id)
    return [
        {
            "step": s["step_number"],
            "niyama": s["data"].get("niyama", {}),
        }
        for s in steps
    ]
