from pymongo import MongoClient, ASCENDING, DESCENDING
from typing import Optional

_client: Optional[MongoClient] = None
_db = None


def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        from pydantic_settings import BaseSettings

        class _MongoSettings(BaseSettings):
            MONGODB_URL: str = "mongodb://localhost:27017"
            DATABASE_NAME: str = "lost_wax_casting"

            class Config:
                env_file = ".env"

        settings = _MongoSettings()
        _client = MongoClient(settings.MONGODB_URL)
    return _client


def get_db():
    global _db
    if _db is None:
        from pydantic_settings import BaseSettings

        class _MongoSettings(BaseSettings):
            MONGODB_URL: str = "mongodb://localhost:27017"
            DATABASE_NAME: str = "lost_wax_casting"

            class Config:
                env_file = ".env"

        settings = _MongoSettings()
        _db = get_mongo_client()[settings.DATABASE_NAME]
    return _db


def init_db():
    db = get_db()
    collections = {
        "castings": [("created_at", DESCENDING)],
        "sensors": [
            ("casting_id", ASCENDING),
            ("timestamp", DESCENDING),
        ],
        "simulations": [
            ("casting_id", ASCENDING),
            ("step_number", ASCENDING),
        ],
        "defects": [
            ("casting_id", ASCENDING),
            ("severity", ASCENDING),
        ],
        "alerts": [
            ("casting_id", ASCENDING),
            ("acknowledged", ASCENDING),
            ("created_at", DESCENDING),
        ],
    }

    for name, indexes in collections.items():
        if name not in db.list_collection_names():
            db.create_collection(name)
        collection = db[name]
        existing = [idx["name"] for idx in collection.list_indexes()]
        for field, order in indexes:
            idx_name = f"{field}_{order}"
            if idx_name not in existing:
                collection.create_index([(field, order)])

    if "timestamp_1" not in [i["name"] for i in db["sensors"].list_indexes()]:
        db["sensors"].create_index([("timestamp", ASCENDING)], expireAfterSeconds=2592000)

    print("Database initialized successfully")
