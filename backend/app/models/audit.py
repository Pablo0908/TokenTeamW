from datetime import datetime, timezone

from app import mongo


def create_indexes():
    mongo.db.audit_log.create_index([("ts", -1)])
    mongo.db.audit_log.create_index([("actor_id", 1)])
    mongo.db.audit_log.create_index("org_id")
    mongo.db.audit_log.create_index("event_id")


def log(actor_id, action, detail="", org_id=None, event_id=None):
    """Append an audit entry. org_id/event_id are the tenant/event dimensions added
    in the multi-tenant pivot — passed where the action concerns an org/event, left
    None for platform-level actions (e.g. account management). Stored as strings to
    match the existing actor_id convention."""
    mongo.db.audit_log.insert_one(
        {
            "actor_id": str(actor_id),
            "action": action,
            "detail": detail,
            "org_id": str(org_id) if org_id else None,
            "event_id": str(event_id) if event_id else None,
            "ts": datetime.now(timezone.utc),
        }
    )


def recent(limit=150):
    cursor = mongo.db.audit_log.find({}, {"_id": 0}).sort("ts", -1).limit(limit)
    return [
        {**doc, "ts": doc["ts"].isoformat()} for doc in cursor
    ]
