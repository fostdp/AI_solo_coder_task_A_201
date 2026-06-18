from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from services import AlertRepository
from alert_engine import alert_service

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

@router.get("")
async def get_alerts(casting_id: Optional[str] = None, unacknowledged_only: bool = False, limit: int = Query(100, ge=1, le=500)):
    if unacknowledged_only:
        return AlertRepository.get_unacknowledged(casting_id)
    return AlertRepository.list_all(casting_id, limit)

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    result = AlertRepository.acknowledge(alert_id)
    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "acknowledged", "alert_id": alert_id}
