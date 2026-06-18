import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from common.mongo_client import get_db


class CastingRepository:
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
        db = get_db()
        db.castings.insert_one(task)
        return task

    @staticmethod
    def get_by_id(casting_id: str) -> Optional[Dict]:
        db = get_db()
        return db.castings.find_one({"id": casting_id}, {"_id": 0})

    @staticmethod
    def list_all(limit: int = 100) -> List[Dict]:
        db = get_db()
        return list(db.castings.find({}, {"_id": 0}).sort("created_at", -1).limit(limit))

    @staticmethod
    def update_status(casting_id: str, status: str) -> bool:
        update = {"status": status}
        if status == "completed":
            update["completed_at"] = datetime.now()
        db = get_db()
        result = db.castings.update_one({"id": casting_id}, {"$set": update})
        return result.modified_count > 0
