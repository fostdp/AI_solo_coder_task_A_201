from pymongo import MongoClient, ASCENDING, DESCENDING
from config import settings

client = MongoClient(settings.MONGODB_URL)
db = client[settings.DATABASE_NAME]

def init_db():
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

def get_db():
    return db
