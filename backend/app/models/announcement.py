from datetime import datetime, timezone

from bson import ObjectId

from app import mongo


def _oid(value):
    return value if isinstance(value, ObjectId) else ObjectId(value)


def create_indexes():
    mongo.db.announcements.create_index("created_at")


def create(title, body, event_id, created_by):
    result = mongo.db.announcements.insert_one({
        "title": title,
        "body": body,
        "event_id": _oid(event_id) if event_id else None,
        "created_by": _oid(created_by),
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
    })
    return str(result.inserted_id)


def all_announcements():
    return list(mongo.db.announcements.find().sort("created_at", -1))


def find_by_id(ann_id):
    try:
        return mongo.db.announcements.find_one({"_id": _oid(ann_id)})
    except Exception:
        return None


def update(ann_id, title, body, event_id):
    mongo.db.announcements.update_one(
        {"_id": _oid(ann_id)},
        {"$set": {
            "title": title,
            "body": body,
            "event_id": _oid(event_id) if event_id else None,
            "updated_at": datetime.now(timezone.utc),
        }},
    )


def delete(ann_id):
    mongo.db.announcements.delete_one({"_id": _oid(ann_id)})
