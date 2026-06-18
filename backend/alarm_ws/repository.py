import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from common.mongo_client import get_db
from common.config_loader import get_alert_thresholds


class AlertRepository:
    @staticmethod
    def insert(alert: Dict) -> Dict:
        db = get_db()
        db.alerts.insert_one(alert)
        return alert

    @staticmethod
    def get_unacknowledged(casting_id: str = None) -> List[Dict]:
        db = get_db()
        query = {"acknowledged": False}
        if casting_id:
            query["casting_id"] = casting_id
        return list(db.alerts.find(query, {"_id": 0}).sort("created_at", -1))

    @staticmethod
    def list_all(casting_id: str = None, limit: int = 100) -> List[Dict]:
        db = get_db()
        query = {}
        if casting_id:
            query["casting_id"] = casting_id
        return list(db.alerts.find(query, {"_id": 0}).sort("created_at", -1).limit(limit))

    @staticmethod
    def acknowledge(alert_id: str) -> bool:
        db = get_db()
        result = db.alerts.update_one(
            {"id": alert_id},
            {"$set": {"acknowledged": True, "acknowledged_at": datetime.now()}},
        )
        return result.modified_count > 0
