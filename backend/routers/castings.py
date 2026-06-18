from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from services import CastingService

router = APIRouter(prefix="/api/castings", tags=["Castings"])

class CreateCastingRequest(BaseModel):
    name: str
    parameters: Dict[str, Any]

@router.get("")
async def list_castings():
    return CastingService.list_all()

@router.post("")
async def create_casting(req: CreateCastingRequest):
    task = CastingService.create(req.name, req.parameters)
    return task

@router.get("/{casting_id}")
async def get_casting(casting_id: str):
    task = CastingService.get_by_id(casting_id)
    if not task:
        raise HTTPException(status_code=404, detail="Casting not found")
    return task
