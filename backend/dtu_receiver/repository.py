import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from common.mongo_client import get_db


class SensorRepository:
    @staticmethod
    def insert(data: Dict) -> Dict:
        data["id"] = str(uuid.uuid4())
        data["timestamp"] = data.get("timestamp", datetime.now())
        db = get_db()
        db.sensors.insert_one(data)
        return data

    @staticmethod
    def get_latest(casting_id: str) -> Optional[Dict]:
        db = get_db()
        return db.sensors.find_one(
            {"casting_id": casting_id},
            {"_id": 0},
            sort=[("timestamp", -1)],
        )

    @staticmethod
    def get_history(casting_id: str, limit: int = 100) -> List[Dict]:
        db = get_db()
        return list(
            db.sensors.find({"casting_id": casting_id}, {"_id": 0})
            .sort("timestamp", -1)
            .limit(limit)
        )
