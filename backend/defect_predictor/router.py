from fastapi import APIRouter, Query
from typing import Optional
from .service import defect_predictor


router = APIRouter(prefix="/api/defects", tags=["Defects"])


@router.get("/predictions")
async def get_defect_predictions(casting_id: str, severity: Optional[str] = None):
    return defect_predictor.get_defects(casting_id, severity)


@router.get("/niyama")
async def get_niyama_data(casting_id: str):
    return defect_predictor.get_niyama_data(casting_id)
