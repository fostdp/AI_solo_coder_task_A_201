import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from database import db

class CastingService:
    @staticmethod
    def create(name: str, parameters: Dict[str, Any]) -> Dict:
        task = {
            "id": str(uuid.uuid4()),
            "name": name,
            "status": "idle",
            "created_at": datetime.now(),
            "completed_at": None,
            "parameters": parameters,
        }
        db.castings.insert_one(task)
        return task

    @staticmethod
    def get_by_id(casting_id: str) -> Optional[Dict]:
        return db.castings.find_one({"id": casting_id}, {"_id": 0})

    @staticmethod
    def list_all(limit: int = 100) -> List[Dict]:
        return list(db.castings.find({}, {"_id": 0}).sort("created_at", -1).limit(limit))

    @staticmethod
    def update_status(casting_id: str, status: str) -> bool:
        update = {"status": status}
        if status == "completed":
            update["completed_at"] = datetime.now()
        result = db.castings.update_one({"id": casting_id}, {"$set": update})
        return result.modified_count > 0


class SensorService:
    @staticmethod
    def insert(data: Dict) -> Dict:
        data["id"] = str(uuid.uuid4())
        data["timestamp"] = data.get("timestamp", datetime.now())
        db.sensors.insert_one(data)
        return data

    @staticmethod
    def get_latest(casting_id: str) -> Optional[Dict]:
        return db.sensors.find_one(
            {"casting_id": casting_id},
            {"_id": 0},
            sort=[("timestamp", -1)],
        )

    @staticmethod
    def get_history(casting_id: str, limit: int = 100) -> List[Dict]:
        return list(
            db.sensors.find({"casting_id": casting_id}, {"_id": 0})
            .sort("timestamp", -1)
            .limit(limit)
        )


class SimulationRepository:
    @staticmethod
    def insert_step(casting_id: str, step_number: int, data: Dict) -> Dict:
        record = {
            "id": str(uuid.uuid4()),
            "casting_id": casting_id,
            "step_number": step_number,
            "data": data,
            "created_at": datetime.now(),
        }
        db.simulations.insert_one(record)
        return record

    @staticmethod
    def get_steps(casting_id: str) -> List[Dict]:
        return list(
            db.simulations.find({"casting_id": casting_id}, {"_id": 0}).sort("step_number", 1)
        )

    @staticmethod
    def get_latest_step(casting_id: str) -> Optional[Dict]:
        return db.simulations.find_one(
            {"casting_id": casting_id},
            {"_id": 0},
            sort=[("step_number", -1)],
        )


class DefectRepository:
    @staticmethod
    def insert_many(defects: List[Dict]) -> int:
        if not defects:
            return 0
        result = db.defects.insert_many(defects)
        return len(result.inserted_ids)

    @staticmethod
    def get_by_casting(casting_id: str) -> List[Dict]:
        return list(db.defects.find({"casting_id": casting_id}, {"_id": 0}).sort("severity", 1))


class AlertRepository:
    @staticmethod
    def insert(alert: Dict) -> Dict:
        db.alerts.insert_one(alert)
        return alert

    @staticmethod
    def get_unacknowledged(casting_id: str = None) -> List[Dict]:
        query = {"acknowledged": False}
        if casting_id:
            query["casting_id"] = casting_id
        return list(db.alerts.find(query, {"_id": 0}).sort("created_at", -1))

    @staticmethod
    def list_all(casting_id: str = None, limit: int = 100) -> List[Dict]:
        query = {}
        if casting_id:
            query["casting_id"] = casting_id
        return list(db.alerts.find(query, {"_id": 0}).sort("created_at", -1).limit(limit))

    @staticmethod
    def acknowledge(alert_id: str) -> bool:
        result = db.alerts.update_one(
            {"id": alert_id},
            {"$set": {"acknowledged": True, "acknowledged_at": datetime.now()}},
        )
        return result.modified_count > 0
