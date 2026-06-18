from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers.sensor import router as sensor_router
from routers.simulation import router as simulation_router
from routers.defects import router as defects_router
from routers.alerts import router as alerts_router
from routers.castings import router as castings_router
from routers.websocket import router as ws_router

app = FastAPI(
    title="古代失蜡法精密铸造充型仿真与缺陷预测系统",
    description="曾侯乙尊盘失蜡法工艺复原研究数字化仿真平台",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    init_db()
    print("System started successfully")

@app.get("/")
async def root():
    return {"status": "running", "name": "Lost Wax Casting Simulation System"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

app.include_router(sensor_router)
app.include_router(simulation_router)
app.include_router(defects_router)
app.include_router(alerts_router)
app.include_router(castings_router)
app.include_router(ws_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
