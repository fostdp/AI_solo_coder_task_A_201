import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from common.mongo_client import init_db
from common.config_loader import load_all_configs
from dtu_receiver.router import router as sensor_router
from filling_simulator.router import router as simulation_router
from defect_predictor.router import router as defects_router
from alarm_ws.router import router as alerts_router
from routers.castings_v2 import router as castings_router
from routers.websocket_v2 import router as ws_router
from orchestrator_v2 import orchestrator
from dtu_receiver.mqtt_receiver import mqtt_receiver

from pydantic import BaseModel


class StartRequest(BaseModel):
    casting_id: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_all_configs()
    init_db()
    await orchestrator.initialize()
    await mqtt_receiver.initialize()
    mqtt_receiver.start()
    print("System started successfully - modular architecture with Redis Pub/Sub + MQTT")
    yield
    mqtt_receiver.stop()
    print("System shutdown complete")


app = FastAPI(
    title="古代失蜡法精密铸造充型仿真与缺陷预测系统",
    description="曾侯乙尊盘失蜡法工艺复原研究数字化仿真平台",
    version="2.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "status": "running",
        "name": "Lost Wax Casting Simulation System",
        "modules": ["dtu_receiver", "filling_simulator", "defect_predictor", "alarm_ws"],
        "communication": "Redis Pub/Sub + MQTT",
        "version": "2.1.0",
    }


@app.get("/health")
async def health_check():
    from common.mongo_client import get_db
    from dtu_receiver.mqtt_receiver import mqtt_receiver

    status = "healthy"
    checks = {
        "api": "ok",
        "mqtt": "connected" if mqtt_receiver.is_connected else "disconnected",
    }

    try:
        db = get_db()
        db.command("ping")
        checks["mongodb"] = "ok"
    except Exception:
        checks["mongodb"] = "unhealthy"
        status = "degraded"

    return {"status": status, "checks": checks}


@app.post("/api/simulation/start")
async def start_simulation(req: StartRequest):
    from common.casting_repo import CastingRepository
    task = CastingRepository.get_by_id(req.casting_id)
    if not task:
        raise HTTPException(status_code=404, detail="Casting task not found")
    await orchestrator.start_simulation(req.casting_id)
    return {"status": "started", "casting_id": req.casting_id}


@app.post("/api/simulation/stop")
async def stop_simulation():
    await orchestrator.stop_simulation()
    return {"status": "stopped"}


@app.get("/api/simulation/status")
async def get_simulation_status():
    return orchestrator.get_status()


app.include_router(sensor_router)
app.include_router(simulation_router)
app.include_router(defects_router)
app.include_router(alerts_router)
app.include_router(castings_router)
app.include_router(ws_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
