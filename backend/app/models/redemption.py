from datetime import datetime, timezone

from bson import ObjectId

from app import mongo


def create_indexes():
    mongo.db.redemptions.create_index([("user_id", 1), ("event_id", 1)])
    # The compound unique index is the race-safe duplicate guard (enforced by the DB, not app logic).
    mongo.db.redemptions.create_index([("badge_id", 1), ("user_id", 1)], unique=True)


def _oid(value):
    return value if isinstance(value, ObjectId) else ObjectId(value)


def redeem(badge_id, event_id, user_id):
    """Insert a redemption. Raises pymongo.errors.DuplicateKeyError on a repeat scan."""
    now = datetime.now(timezone.utc)
    mongo.db.redemptions.insert_one(
        {
            "badge_id": _oid(badge_id),
            "event_id": _oid(event_id),
            "user_id": _oid(user_id),
            "redeemed_at": now,
        }
    )
    return now


def count_for_event(user_id, event_id):
    return mongo.db.redemptions.count_documents({"user_id": _oid(user_id), "event_id": _oid(event_id)})


def count_for_badge(badge_id):
    return mongo.db.redemptions.count_documents({"badge_id": _oid(badge_id)})


def count_for_user(user_id):
    return mongo.db.redemptions.count_documents({"user_id": _oid(user_id)})


def redeemed_badge_map(user_id, event_id):
    """Return {badge_id_str: redeemed_at} for this user's redemptions in an event."""
    cursor = mongo.db.redemptions.find({"user_id": _oid(user_id), "event_id": _oid(event_id)})
    return {str(doc["badge_id"]): doc.get("redeemed_at") for doc in cursor}


def counts_by_user():
    """Return {user_id_str: total_badges_redeemed} across all events (one aggregation)."""
    pipeline = [{"$group": {"_id": "$user_id", "count": {"$sum": 1}}}]
    return {str(doc["_id"]): doc["count"] for doc in mongo.db.redemptions.aggregate(pipeline)}
