from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from typing import Optional
from .engine import alert_engine


router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.get("")
async def get_alerts(
    casting_id: Optional[str] = None,
    unacknowledged_only: bool = False,
    limit: int = Query(100, ge=1, le=500),
):
    return alert_engine.get_alerts(casting_id, unacknowledged_only, limit)


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    result = alert_engine.acknowledge_alert(alert_id)
    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "acknowledged", "alert_id": alert_id}


@router.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket):
    await websocket.accept()
    alert_engine.add_ws_connection(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        alert_engine.remove_ws_connection(websocket)
