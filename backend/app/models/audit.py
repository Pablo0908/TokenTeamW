from datetime import datetime, timezone

from app import mongo


def create_indexes():
    mongo.db.audit_log.create_index([("ts", -1)])
    mongo.db.audit_log.create_index([("actor_id", 1)])


def log(actor_id, action, detail=""):
    mongo.db.audit_log.insert_one(
        {
            "actor_id": str(actor_id),
            "action": action,
            "detail": detail,
            "ts": datetime.now(timezone.utc),
        }
    )


def recent(limit=150):
    cursor = mongo.db.audit_log.find({}, {"_id": 0}).sort("ts", -1).limit(limit)
    return [
        {**doc, "ts": doc["ts"].isoformat()} for doc in cursor
    ]
