from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
from orchestrator_v2 import orchestrator
from alarm_ws.engine import alert_engine

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/simulation")
async def simulation_websocket(websocket: WebSocket):
    await websocket.accept()
    orchestrator.add_ws(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except Exception:
                pass
    except WebSocketDisconnect:
        orchestrator.remove_ws(websocket)


@router.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket):
    await websocket.accept()
    alert_engine.add_ws_connection(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        alert_engine.remove_ws_connection(websocket)
