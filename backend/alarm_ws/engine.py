import asyncio
from typing import List, Dict, Any, Optional
from common.redis_bus import get_message_bus
from common.config_loader import get_alert_thresholds
from .repository import AlertRepository


class AlertEngine:
    def __init__(self):
        self.active_ws_connections: List = []
        self._bus = None

    async def initialize(self):
        self._bus = await get_message_bus()
        await self._bus.subscribe("defect_result", self.on_defect_result)
        await self._bus.subscribe("filling_result", self.on_filling_result)
        await self._bus.start_listening()

    def add_ws_connection(self, ws):
        self.active_ws_connections.append(ws)

    def remove_ws_connection(self, ws):
        if ws in self.active_ws_connections:
            self.active_ws_connections.remove(ws)

    async def broadcast_alert(self, alert: Dict):
        for ws in list(self.active_ws_connections):
            try:
                await ws.send_json(alert)
            except Exception:
                self.remove_ws_connection(ws)

    async def on_filling_result(self, msg: Dict[str, Any]):
        casting_id = msg.get("casting_id")
        filling = msg.get("filling", {})
        filling_ratio = filling.get("filling_ratio", 0)
        thresholds = get_alert_thresholds()

        if filling_ratio < thresholds["min_filling_ratio"]:
            alert = self._create_alert(
                casting_id=casting_id,
                alert_type="insufficient_filling",
                severity="critical" if filling_ratio < 0.8 else "error",
                message=f"充型不足: 当前充型率 {filling_ratio*100:.1f}%, 最低要求 {thresholds['min_filling_ratio']*100:.0f}%",
                data={"filling_ratio": filling_ratio, "min_required": thresholds["min_filling_ratio"]},
            )
            await self._process_alert(alert)

    async def on_defect_result(self, msg: Dict[str, Any]):
        casting_id = msg.get("casting_id")
        defects = msg.get("defects", [])
        total_shrinkage = msg.get("total_shrinkage_volume", 0)
        thresholds = get_alert_thresholds()

        if total_shrinkage > thresholds["max_shrinkage_volume"]:
            alert = self._create_alert(
                casting_id=casting_id,
                alert_type="shrinkage_volume_exceeded",
                severity="critical" if total_shrinkage > 10 else "error",
                message=f"缩孔体积超限: 总体积 {total_shrinkage:.2f}cm³, 阈值 {thresholds['max_shrinkage_volume']}cm³",
                data={
                    "total_volume": total_shrinkage,
                    "max_allowed": thresholds["max_shrinkage_volume"],
                    "critical_defects": len([d for d in defects if d["severity"] == "critical"]),
                },
            )
            await self._process_alert(alert)

        for defect in defects:
            if defect["severity"] == "critical":
                alert = self._create_alert(
                    casting_id=casting_id,
                    alert_type="critical_defect",
                    severity="critical",
                    message=f"严重缺陷检测: {defect['defect_type']} 位置({defect['position']['x']:.2f},{defect['position']['y']:.2f},{defect['position']['z']:.2f}) 体积 {defect['volume']:.2f}cm³",
                    data={"defect": defect},
                )
                await self._process_alert(alert)

    async def _process_alert(self, alert: Dict):
        AlertRepository.insert(alert)
        await self.broadcast_alert(alert)
        if self._bus:
            await self._bus.publish("alerts", {
                "type": "alert",
                "data": alert,
            })

    def _create_alert(
        self,
        casting_id: str,
        alert_type: str,
        severity: str,
        message: str,
        data: Dict,
    ) -> Dict:
        return {
            "id": str(uuid.uuid4()),
            "casting_id": casting_id,
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "data": data,
            "acknowledged": False,
            "acknowledged_at": None,
            "created_at": datetime.now(),
        }

    def get_alerts(self, casting_id: Optional[str] = None, unacknowledged_only: bool = False, limit: int = 100):
        if unacknowledged_only:
            return AlertRepository.get_unacknowledged(casting_id)
        return AlertRepository.list_all(casting_id, limit)

    def acknowledge_alert(self, alert_id: str) -> bool:
        return AlertRepository.acknowledge(alert_id)


alert_engine = AlertEngine()
