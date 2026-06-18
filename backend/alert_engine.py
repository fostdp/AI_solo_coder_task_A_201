import uuid
from datetime import datetime
from typing import List, Dict
from config import settings
from services import AlertRepository
import numpy as np

class AlertService:
    def __init__(self):
        self.active_ws_connections: List = []

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

    def check_and_create_alerts(
        self,
        casting_id: str,
        filling_ratio: float,
        total_shrinkage_volume: float,
        defects: List[Dict],
    ) -> List[Dict]:
        new_alerts = []

        if filling_ratio < settings.MIN_FILLING_RATIO:
            alert = self._create_alert(
                casting_id=casting_id,
                alert_type="insufficient_filling",
                severity="critical" if filling_ratio < 0.8 else "error",
                message=f"充型不足: 当前充型率 {filling_ratio*100:.1f}%, 最低要求 {settings.MIN_FILLING_RATIO*100:.0f}%",
                data={"filling_ratio": filling_ratio, "min_required": settings.MIN_FILLING_RATIO},
            )
            new_alerts.append(alert)

        if total_shrinkage_volume > settings.MAX_SHRINKAGE_VOLUME:
            alert = self._create_alert(
                casting_id=casting_id,
                alert_type="shrinkage_volume_exceeded",
                severity="critical" if total_shrinkage_volume > 10 else "error",
                message=f"缩孔体积超限: 总体积 {total_shrinkage_volume:.2f}cm³, 阈值 {settings.MAX_SHRINKAGE_VOLUME}cm³",
                data={
                    "total_volume": total_shrinkage_volume,
                    "max_allowed": settings.MAX_SHRINKAGE_VOLUME,
                    "critical_defects": len([d for d in defects if d["severity"] == "critical"]),
                },
            )
            new_alerts.append(alert)

        for defect in defects:
            if defect["severity"] == "critical":
                alert = self._create_alert(
                    casting_id=casting_id,
                    alert_type="critical_defect",
                    severity="critical",
                    message=f"严重缺陷检测: {defect['defect_type']} 位置({defect['position']['x']:.2f},{defect['position']['y']:.2f},{defect['position']['z']:.2f}) 体积 {defect['volume']:.2f}cm³",
                    data={"defect": defect},
                )
                new_alerts.append(alert)

        for alert in new_alerts:
            AlertRepository.insert(alert)

        return new_alerts

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

    async def process_new_alerts(self, casting_id: str, filling_ratio: float, total_shrinkage_volume: float, defects: List[Dict]):
        new_alerts = self.check_and_create_alerts(casting_id, filling_ratio, total_shrinkage_volume, defects)
        for alert in new_alerts:
            await self.broadcast_alert(alert)
        return new_alerts


alert_service = AlertService()
