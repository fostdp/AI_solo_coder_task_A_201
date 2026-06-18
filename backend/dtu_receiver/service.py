import asyncio
from typing import Dict, Any, Optional
from common.redis_bus import get_message_bus
from .validator import sensor_validator
from .repository import SensorRepository


class DtuReceiverService:
    def __init__(self):
        self._bus = None

    async def initialize(self):
        self._bus = await get_message_bus()

    async def process_sensor_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        validation = sensor_validator.validate(data)
        if not validation["valid"]:
            return {"status": "error", "errors": validation["errors"]}

        normalized = sensor_validator.normalize(data)
        saved = SensorRepository.insert(normalized)

        if self._bus:
            await self._bus.publish("sensor_data", {
                "type": "sensor_data",
                "data": saved,
            })

        return {"status": "ok", "sensor": saved}

    async def get_latest(self, casting_id: str) -> Optional[Dict]:
        return SensorRepository.get_latest(casting_id)

    async def get_history(self, casting_id: str, limit: int = 100):
        return SensorRepository.get_history(casting_id, limit)


dtu_service = DtuReceiverService()
