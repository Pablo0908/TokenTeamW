from datetime import datetime, timezone

from bson import ObjectId

from app import mongo


def create_indexes():
    mongo.db.redemptions.create_index([("user_id", 1), ("event_id", 1)])
    # The compound unique index is the race-safe duplicate guard (enforced by the DB, not app logic).
    mongo.db.redemptions.create_index([("badge_id", 1), ("user_id", 1)], unique=True)
    mongo.db.redemptions.create_index("org_id")


def _oid(value):
    return value if isinstance(value, ObjectId) else ObjectId(value)


def redeem(badge_id, event_id, user_id, org_id=None):
    """Insert a redemption. Raises pymongo.errors.DuplicateKeyError on a repeat scan.

    org_id is denormalized from the event (the scan path already has the event in
    hand) so redemption analytics can scope by tenant without a join."""
    now = datetime.now(timezone.utc)
    mongo.db.redemptions.insert_one(
        {
            "badge_id": _oid(badge_id),
            "event_id": _oid(event_id),
            "user_id": _oid(user_id),
            "org_id": _oid(org_id) if org_id else None,
            "redeemed_at": now,
        }
    )
    return now


def count_for_event(user_id, event_id):
    return mongo.db.redemptions.count_documents({"user_id": _oid(user_id), "event_id": _oid(event_id)})


def count_for_badge(badge_id):
    return mongo.db.redemptions.count_documents({"badge_id": _oid(badge_id)})


def count_for_user(user_id, org_id=None):
    query = {"user_id": _oid(user_id)}
    if org_id:
        query["org_id"] = _oid(org_id)
    return mongo.db.redemptions.count_documents(query)


def redeemed_badge_map(user_id, event_id):
    """Return {badge_id_str: redeemed_at} for this user's redemptions in an event."""
    cursor = mongo.db.redemptions.find({"user_id": _oid(user_id), "event_id": _oid(event_id)})
    return {str(doc["badge_id"]): doc.get("redeemed_at") for doc in cursor}


def counts_by_user(org_id=None):
    """Return {user_id_str: total_badges_redeemed}. Across all events by default;
    scoped to one tenant when org_id is given (one aggregation either way)."""
    pipeline = []
    if org_id:
        pipeline.append({"$match": {"org_id": _oid(org_id)}})
    pipeline.append({"$group": {"_id": "$user_id", "count": {"$sum": 1}}})
    return {str(doc["_id"]): doc["count"] for doc in mongo.db.redemptions.aggregate(pipeline)}


def counts_by_badge(event_id):
    """Return {badge_id_str: redemption_count} for one event (one aggregation) — used to
    compute each badge's rarity without a query per badge."""
    pipeline = [
        {"$match": {"event_id": _oid(event_id)}},
        {"$group": {"_id": "$badge_id", "count": {"$sum": 1}}},
    ]
    return {str(doc["_id"]): doc["count"] for doc in mongo.db.redemptions.aggregate(pipeline)}


def delete_by_user(user_id):
    """Remove all redemptions belonging to a deleted user (cascade)."""
    mongo.db.redemptions.delete_many({"user_id": _oid(user_id)})
