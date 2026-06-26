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


def redeemed_map_by_events(user_id, event_ids=None):
    """Batch form of redeemed_badge_map: {event_id_str: {badge_id_str: redeemed_at}} for this
    user in ONE query. event_ids=None returns the user's redemptions across ALL events; a list
    scopes to those events. Avoids a query-per-event when scanning the whole catalog."""
    query = {"user_id": _oid(user_id)}
    if event_ids is not None:
        query["event_id"] = {"$in": [_oid(e) for e in event_ids]}
    out = {}
    for doc in mongo.db.redemptions.find(query):
        out.setdefault(str(doc["event_id"]), {})[str(doc["badge_id"])] = doc.get("redeemed_at")
    return out


def favorite_event_type(user_id, org_ids=None):
    """The event_type this user has redeemed most (mode over their redemptions joined
    to events). `org_ids` (strings) scopes to a tenant set for an org admin; None = all.
    Returns {event_type, count, tie} or None when the user has no redemptions."""
    match = {"user_id": _oid(user_id)}
    if org_ids is not None:
        match["org_id"] = {"$in": [_oid(o) for o in org_ids]}
    pipeline = [
        {"$match": match},
        {"$lookup": {"from": "events", "localField": "event_id", "foreignField": "_id", "as": "ev"}},
        {"$unwind": "$ev"},
        {"$group": {"_id": "$ev.event_type", "count": {"$sum": 1}}},
        # Highest count first; name as a stable tiebreak so the result is deterministic.
        {"$sort": {"count": -1, "_id": 1}},
    ]
    results = list(mongo.db.redemptions.aggregate(pipeline))
    if not results:
        return None
    top = results[0]
    tie = len(results) > 1 and results[1]["count"] == top["count"]
    return {"event_type": top["_id"] or "uncategorized", "count": top["count"], "tie": tie}


def counts_by_user(org_id=None):
    """Return {user_id_str: total_badges_redeemed}. Across all events by default;
    scoped to one tenant when org_id is given (one aggregation either way)."""
    pipeline = []
    if org_id:
        pipeline.append({"$match": {"org_id": _oid(org_id)}})
    pipeline.append({"$group": {"_id": "$user_id", "count": {"$sum": 1}}})
    return {str(doc["_id"]): doc["count"] for doc in mongo.db.redemptions.aggregate(pipeline)}


def org_ids_for_user(user_id):
    """Set of org_id strings where the user has at least one redemption — the orgs they've
    'interacted with'. Drives the org-scoped feed (P7). Skips legacy null-org redemptions."""
    ids = mongo.db.redemptions.distinct("org_id", {"user_id": _oid(user_id)})
    return {str(o) for o in ids if o}


def org_overview(org_id):
    """Headline counts for an org dashboard: total scans (redemptions) and the number
    of distinct attendees who scanned at least once. Two cheap counts, no join."""
    oid = _oid(org_id)
    total = mongo.db.redemptions.count_documents({"org_id": oid})
    unique = len(mongo.db.redemptions.distinct("user_id", {"org_id": oid}))
    return {"total_scans": total, "unique_participants": unique}


def scans_over_time(org_id, period):
    """Per-period scan counts for one org, oldest→newest — same {bucket, count} shape
    as audit.activity_buckets so the frontend ActivityChart renders it unchanged.
    `period` is 'day' | 'week' | 'month'."""
    unit = {"day": "day", "week": "week", "month": "month"}.get(period, "day")
    pipeline = [
        {"$match": {"org_id": _oid(org_id)}},
        {"$group": {"_id": {"$dateTrunc": {"date": "$redeemed_at", "unit": unit}}, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    out = []
    for doc in mongo.db.redemptions.aggregate(pipeline):
        bucket = doc["_id"]
        out.append({"bucket": bucket.isoformat() if bucket else None, "count": doc["count"]})
    return out


def top_events(org_id, limit=5):
    """The org's most-scanned events: [{id, name, scans}], busiest first."""
    pipeline = [
        {"$match": {"org_id": _oid(org_id)}},
        {"$group": {"_id": "$event_id", "scans": {"$sum": 1}}},
        {"$sort": {"scans": -1}},
        {"$limit": limit},
        {"$lookup": {"from": "events", "localField": "_id", "foreignField": "_id", "as": "ev"}},
        {"$unwind": "$ev"},
    ]
    return [{"id": str(d["_id"]), "name": d["ev"].get("name", ""), "scans": d["scans"]}
            for d in mongo.db.redemptions.aggregate(pipeline)]


def counts_by_badge(event_id):
    """Return {badge_id_str: redemption_count} for one event (one aggregation) — used to
    compute each badge's rarity without a query per badge."""
    pipeline = [
        {"$match": {"event_id": _oid(event_id)}},
        {"$group": {"_id": "$badge_id", "count": {"$sum": 1}}},
    ]
    return {str(doc["_id"]): doc["count"] for doc in mongo.db.redemptions.aggregate(pipeline)}


def counts_by_badge_for_events(event_ids):
    """Batch form of counts_by_badge: {badge_id_str: redemption_count} across many events in
    ONE aggregation. badge_ids are globally unique, so a single flat map serves all events."""
    oids = [_oid(e) for e in event_ids]
    if not oids:
        return {}
    pipeline = [
        {"$match": {"event_id": {"$in": oids}}},
        {"$group": {"_id": "$badge_id", "count": {"$sum": 1}}},
    ]
    return {str(doc["_id"]): doc["count"] for doc in mongo.db.redemptions.aggregate(pipeline)}


def delete_by_user(user_id):
    """Remove all redemptions belonging to a deleted user (cascade)."""
    mongo.db.redemptions.delete_many({"user_id": _oid(user_id)})


def delete_by_event(event_id):
    """Remove all redemptions (scanned badges) for an event (cascade on event delete)."""
    return mongo.db.redemptions.delete_many({"event_id": _oid(event_id)}).deleted_count
