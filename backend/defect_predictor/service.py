import asyncio
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from common.redis_bus import get_message_bus
from common.config_loader import get_grid_size
from .shrinkage import ShrinkageAnalyzer
from common.mongo_client import get_db


class DefectPredictorService:
    def __init__(self):
        self.grid_size: Tuple[int, int, int] = get_grid_size()
        self.analyzer = ShrinkageAnalyzer(self.grid_size)
        self.current_casting_id: Optional[str] = None
        self._bus = None

    async def initialize(self):
        self._bus = await get_message_bus()
        await self._bus.subscribe("heat_result", self.on_heat_result)
        await self._bus.subscribe("simulation_control", self.on_control)
        await self._bus.start_listening()

    async def on_control(self, msg: Dict[str, Any]):
        action = msg.get("action")
        casting_id = msg.get("casting_id")
        if action == "start" and casting_id:
            self.current_casting_id = casting_id
            self.analyzer.reset()

    async def on_heat_result(self, msg: Dict[str, Any]):
        casting_id = msg.get("casting_id")
        if casting_id != self.current_casting_id:
            return

        step = msg.get("step")
        heat_data = msg.get("heat", {})
        temp_field = np.array(msg.get("temperature_field", []), dtype=np.float32)
        temp_grad = np.array(msg.get("temperature_gradient", []), dtype=np.float32)
        cooling_rate = np.array(msg.get("cooling_rate", []), dtype=np.float32)

        if temp_field.size == 0:
            return

        if temp_grad.size == 0:
            temp_grad = np.zeros(self.grid_size + (3,), dtype=np.float32)
        else:
            try:
                temp_grad = temp_grad.reshape(self.grid_size + (3,))
            except ValueError:
                temp_grad = np.zeros(self.grid_size + (3,), dtype=np.float32)

        if cooling_rate.size == 0:
            cooling_rate = np.ones(self.grid_size, dtype=np.float32) * 0.5
        else:
            try:
                cooling_rate = cooling_rate.reshape(self.grid_size)
            except ValueError:
                cooling_rate = np.ones(self.grid_size, dtype=np.float32) * 0.5

        try:
            temp_field = temp_field.reshape(self.grid_size)
        except ValueError:
            return

        niyama_result = self.analyzer.niyama_calc.niyama_field.tolist()
        if self.analyzer.niyama_calc.local_threshold_field is not None:
            niyama_threshold_field = self.analyzer.niyama_calc.local_threshold_field.tolist()
        else:
            niyama_threshold_field = None

        defects = self.analyzer.predict(
            casting_id=self.current_casting_id,
            temperature_field=temp_field,
            temperature_gradient=temp_grad,
            cooling_rate=cooling_rate,
        )

        if defects:
            db = get_db()
            db.defects.insert_many(defects)

        total_shrinkage = self.analyzer.get_total_shrinkage_volume()

        if self._bus:
            await self._bus.publish("niyama_result", {
                "type": "niyama_result",
                "casting_id": self.current_casting_id,
                "step": step,
                "niyama": {
                    "points": self.analyzer.niyama_calc.niyama_field.tolist() if False else (
                        self._extract_niyama_points()
                    ),
                    "mean_niyama": float(np.mean(self.analyzer.niyama_calc.niyama_field)),
                    "niyama_field": niyama_result,
                    "threshold_field": niyama_threshold_field,
                },
            })
            await self._bus.publish("defect_result", {
                "type": "defect_result",
                "casting_id": self.current_casting_id,
                "step": step,
                "defects": defects,
                "total_shrinkage_volume": total_shrinkage,
            })

    def _extract_niyama_points(self) -> List[Dict]:
        points = []
        gx, gy, gz = self.grid_size
        for x in range(0, gx, 2):
            for y in range(0, gy, 2):
                for z in range(0, gz, 2):
                    local_th = (
                        float(self.analyzer.niyama_calc.local_threshold_field[x, y, z])
                        if self.analyzer.niyama_calc.local_threshold_field is not None
                        else self.analyzer.niyama_calc.niyama_threshold
                    )
                    points.append({
                        "x": float(x) / gx,
                        "y": float(y) / gy,
                        "z": float(z) / gz,
                        "niyama": float(self.analyzer.niyama_calc.niyama_field[x, y, z]),
                        "threshold": local_th,
                    })
        return points

    def get_defects(self, casting_id: str, severity: Optional[str] = None) -> List[Dict]:
        db = get_db()
        query = {"casting_id": casting_id}
        if severity:
            query["severity"] = severity
        return list(db.defects.find(query, {"_id": 0}).sort("severity", 1))

    def get_niyama_data(self, casting_id: str) -> List[Dict]:
        db = get_db()
        steps = list(
            db.simulations.find({"casting_id": casting_id}, {"_id": 0}).sort("step_number", 1)
        )
        result = []
        for s in steps:
            data = s.get("data", {})
            if "niyama" in data:
                result.append({
                    "step": s["step_number"],
                    "niyama": data.get("niyama", {}),
                })
        return result


defect_predictor = DefectPredictorService()
