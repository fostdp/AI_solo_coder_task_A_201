import asyncio
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from common.redis_bus import get_message_bus
from common.config_loader import get_grid_size, get_temperature_range
from .filling_service import FillingSimulationService
from .heat import HeatTransferSolver
from common.mongo_client import get_db
import uuid
from datetime import datetime


class FillingSimulatorService:
    def __init__(self):
        self.grid_size: Tuple[int, int, int] = get_grid_size()
        self.filling_service = FillingSimulationService(self.grid_size)
        self.heat_service = HeatTransferSolver(self.grid_size)
        self.running = False
        self.current_casting_id: Optional[str] = None
        self.current_step = 0
        self._previous_temp_field: Optional[np.ndarray] = None
        self._bus = None

    async def initialize(self):
        self._bus = await get_message_bus()
        await self._bus.subscribe("sensor_data", self.on_sensor_data)
        await self._bus.subscribe("simulation_control", self.on_control)
        await self._bus.start_listening()

    async def on_control(self, msg: Dict[str, Any]):
        action = msg.get("action")
        casting_id = msg.get("casting_id")
        if action == "start" and casting_id:
            await self.start(casting_id)
        elif action == "stop":
            await self.stop()

    async def start(self, casting_id: str):
        self.current_casting_id = casting_id
        self.filling_service.reset()
        temp_range = get_temperature_range()
        self.heat_service.reset(initial_temp=temp_range["initial_ambient"])
        self.current_step = 0
        self.running = True
        self._previous_temp_field = None
        db = get_db()
        db.castings.update_one({"id": casting_id}, {"$set": {"status": "running"}})

    async def stop(self):
        self.running = False
        if self.current_casting_id:
            db = get_db()
            db.castings.update_one(
                {"id": self.current_casting_id},
                {"$set": {"status": "stopped", "completed_at": datetime.now()}},
            )

    async def on_sensor_data(self, msg: Dict[str, Any]):
        if not self.running or not self.current_casting_id:
            return

        sensor = msg.get("data", {})
        if sensor.get("casting_id") != self.current_casting_id:
            return

        await self.process_step(sensor)

    def _insert_step(self, step_record: Dict):
        db = get_db()
        record = {
            "id": str(uuid.uuid4()),
            "casting_id": self.current_casting_id,
            "step_number": self.current_step,
            "data": step_record,
            "created_at": datetime.now(),
        }
        db.simulations.insert_one(record)

    async def process_step(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        self.current_step += 1
        filling_target = sensor_data.get("filling_progress", 0) / 100.0
        pouring_temp = sensor_data.get("pouring_temperature", 1200.0)
        shell_perm = sensor_data.get("shell_permeability", 50.0)

        filling_result = self.filling_service.step(filling_target, pouring_temp)
        heat_result = self.heat_service.step(
            pouring_temp=pouring_temp,
            filling_field=filling_result["filling_field"],
            shell_permeability=shell_perm,
        )

        current_temp = np.array(heat_result["temperature_field"], dtype=np.float32)
        temp_gradient = self.heat_service.get_temperature_gradient()

        if self._previous_temp_field is not None:
            cooling_rate = self.heat_service.get_cooling_rate(self._previous_temp_field)
        else:
            cooling_rate = np.ones(self.grid_size, dtype=np.float32) * 0.5

        step_record = {
            "filling": {
                "filling_ratio": filling_result["filling_ratio"],
                "mean_velocity": filling_result["mean_velocity"],
                "mean_pressure": filling_result["mean_pressure"],
            },
            "temperature": {
                "points": heat_result["points"],
                "max_temperature": heat_result["max_temperature"],
                "min_temperature": heat_result["min_temperature"],
                "mean_temperature": heat_result["mean_temperature"],
            },
            "filling_ratio": filling_result["filling_ratio"],
        }

        self._insert_step(step_record)
        self._previous_temp_field = current_temp

        if self._bus:
            await self._bus.publish("filling_result", {
                "type": "filling_result",
                "casting_id": self.current_casting_id,
                "step": self.current_step,
                "filling": filling_result,
            })
            await self._bus.publish("heat_result", {
                "type": "heat_result",
                "casting_id": self.current_casting_id,
                "step": self.current_step,
                "heat": heat_result,
                "temperature_gradient": temp_gradient.tolist(),
                "cooling_rate": cooling_rate.tolist(),
                "temperature_field": current_temp.tolist(),
            })

        return step_record

    def get_status(self) -> Dict:
        return {
            "casting_id": self.current_casting_id,
            "status": "running" if self.running else "idle",
            "filling_progress": self.filling_service.get_filling_ratio() * 100,
            "current_step": self.current_step,
        }


filling_simulator = FillingSimulatorService()
