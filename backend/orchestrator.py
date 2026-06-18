import numpy as np
from typing import Dict, List, Optional, Tuple
from simulation.filling import FillingSimulationService
from simulation.heat_transfer import HeatTransferService
from simulation.defect_prediction import DefectPredictionService
from services import SimulationRepository, DefectRepository, CastingService
from alert_engine import alert_service
import asyncio

class SimulationOrchestrator:
    def __init__(self, grid_size: Tuple[int, int, int] = (16, 16, 16)):
        self.grid_size = grid_size
        self.filling_service = FillingSimulationService(grid_size)
        self.heat_service = HeatTransferService(grid_size)
        self.defect_service = DefectPredictionService(grid_size)
        self.running = False
        self.current_casting_id: Optional[str] = None
        self.total_steps = 60
        self.current_step = 0
        self.start_time = None
        self._ws_connections: List = []
        self._previous_temp_field: Optional[np.ndarray] = None

    async def start(self, casting_id: str):
        self.current_casting_id = casting_id
        self.filling_service.reset()
        self.heat_service.reset(initial_temp=25.0)
        self.defect_service.reset()
        self.current_step = 0
        self.running = True
        self._previous_temp_field = None
        CastingService.update_status(casting_id, "running")

    async def stop(self):
        self.running = False
        if self.current_casting_id:
            CastingService.update_status(self.current_casting_id, "stopped")

    def add_ws(self, ws):
        self._ws_connections.append(ws)

    def remove_ws(self, ws):
        if ws in self._ws_connections:
            self._ws_connections.remove(ws)

    async def broadcast_ws(self, data: Dict):
        for ws in list(self._ws_connections):
            try:
                await ws.send_json(data)
            except Exception:
                self.remove_ws(ws)

    async def process_sensor_data(self, sensor_data: Dict) -> Dict:
        if not self.running or not self.current_casting_id:
            return {"error": "simulation not running"}

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

        niyama_result = self.defect_service.calculate_niyama(
            temperature_field=current_temp,
            temperature_gradient=temp_gradient,
            cooling_rate=cooling_rate,
        )

        defects = self.defect_service.predict_defects(
            casting_id=self.current_casting_id,
            temperature_field=current_temp,
        )

        if defects:
            DefectRepository.insert_many([d for d in defects])

        filling_ratio = filling_result["filling_ratio"]
        total_shrinkage = self.defect_service.get_total_shrinkage_volume()

        new_alerts = await alert_service.process_new_alerts(
            self.current_casting_id, filling_ratio, total_shrinkage, defects
        )

        step_record = {
            "filling": {
                "filling_ratio": filling_ratio,
                "mean_velocity": filling_result["mean_velocity"],
                "mean_pressure": filling_result["mean_pressure"],
            },
            "temperature": {
                "points": heat_result["points"],
                "max_temperature": heat_result["max_temperature"],
                "min_temperature": heat_result["min_temperature"],
                "mean_temperature": heat_result["mean_temperature"],
            },
            "niyama": {
                "points": niyama_result["points"],
                "mean_niyama": niyama_result["mean_niyama"],
            },
            "defects": defects,
            "filling_ratio": filling_ratio,
        }
        SimulationRepository.insert_step(self.current_casting_id, self.current_step, step_record)

        if filling_ratio >= 0.99 and self.current_step >= self.total_steps:
            await self.stop()
            CastingService.update_status(self.current_casting_id, "completed")

        broadcast_data = {
            "type": "simulation_step",
            "casting_id": self.current_casting_id,
            "step": self.current_step,
            "total_steps": self.total_steps,
            "filling_ratio": filling_ratio,
            "heat": heat_result,
            "niyama": niyama_result,
            "defects": defects,
            "alerts": new_alerts,
        }
        await self.broadcast_ws(broadcast_data)

        self._previous_temp_field = current_temp
        return step_record

    def get_status(self) -> Dict:
        return {
            "casting_id": self.current_casting_id,
            "status": "running" if self.running else "idle",
            "filling_progress": self.filling_service.get_filling_ratio() * 100,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
        }


orchestrator = SimulationOrchestrator()
