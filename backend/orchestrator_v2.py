import asyncio
from typing import Dict, Any, List, Optional
from common.redis_bus import get_message_bus
from common.config_loader import get_total_steps
from dtu_receiver.service import dtu_service
from filling_simulator.service import filling_simulator
from defect_predictor.service import defect_predictor
from alarm_ws.engine import alert_engine


class SystemOrchestrator:
    def __init__(self):
        self._ws_connections: List = []
        self._bus = None
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        self._bus = await get_message_bus()

        await dtu_service.initialize()
        await filling_simulator.initialize()
        await defect_predictor.initialize()
        await alert_engine.initialize()

        await self._bus.subscribe("sensor_data", self._broadcast_to_ws)
        await self._bus.subscribe("filling_result", self._broadcast_to_ws)
        await self._bus.subscribe("heat_result", self._broadcast_to_ws)
        await self._bus.subscribe("niyama_result", self._broadcast_to_ws)
        await self._bus.subscribe("defect_result", self._broadcast_to_ws)
        await self._bus.subscribe("alerts", self._broadcast_to_ws)
        await self._bus.start_listening()

        self._initialized = True

    async def start_simulation(self, casting_id: str):
        filling_simulator.current_casting_id = casting_id
        defect_predictor.current_casting_id = casting_id
        await filling_simulator.start(casting_id)
        if self._bus:
            await self._bus.publish("simulation_control", {
                "action": "start",
                "casting_id": casting_id,
            })

    async def stop_simulation(self):
        await filling_simulator.stop()
        if self._bus:
            await self._bus.publish("simulation_control", {
                "action": "stop",
            })

    def add_ws(self, ws):
        self._ws_connections.append(ws)

    def remove_ws(self, ws):
        if ws in self._ws_connections:
            self._ws_connections.remove(ws)

    async def _broadcast_to_ws(self, data: Dict[str, Any]):
        msg_type = data.get("type", "unknown")
        broadcast_data = self._transform_message(data)

        for ws in list(self._ws_connections):
            try:
                await ws.send_json(broadcast_data)
            except Exception:
                self.remove_ws(ws)

    def _transform_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        msg_type = data.get("type", "unknown")

        if msg_type == "sensor_data":
            return {"type": "sensor_update", "data": data.get("data", {})}

        if msg_type == "filling_result":
            return {
                "type": "simulation_step",
                "casting_id": data.get("casting_id"),
                "step": data.get("step"),
                "total_steps": get_total_steps(),
                "filling_ratio": data.get("filling", {}).get("filling_ratio", 0),
            }

        if msg_type == "heat_result":
            return {
                "type": "simulation_step",
                "casting_id": data.get("casting_id"),
                "step": data.get("step"),
                "total_steps": get_total_steps(),
                "heat": data.get("heat", {}),
            }

        if msg_type == "niyama_result":
            return {
                "type": "simulation_step",
                "casting_id": data.get("casting_id"),
                "step": data.get("step"),
                "total_steps": get_total_steps(),
                "niyama": data.get("niyama", {}),
            }

        if msg_type == "defect_result":
            return {
                "type": "simulation_step",
                "casting_id": data.get("casting_id"),
                "step": data.get("step"),
                "total_steps": get_total_steps(),
                "defects": data.get("defects", []),
            }

        if msg_type == "alert":
            return data.get("data", {})

        return data

    def get_status(self) -> Dict:
        return filling_simulator.get_status()


orchestrator = SystemOrchestrator()
