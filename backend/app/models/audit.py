from datetime import datetime, timezone

from app import mongo

PAGE_SIZE = 50  # server-side audit page size


def create_indexes():
    mongo.db.audit_log.create_index([("ts", -1)])
    mongo.db.audit_log.create_index([("actor_id", 1)])
    mongo.db.audit_log.create_index("org_id")
    mongo.db.audit_log.create_index("event_id")
    mongo.db.audit_log.create_index("actor_email")  # search-by-user filter path
    # Serves the tier-scoped read: filter org_id ∈ orgs, sorted ts desc.
    mongo.db.audit_log.create_index([("org_id", 1), ("ts", -1)])


def log(actor_id, action, detail="", org_id=None, event_id=None, actor_role=None, actor_email=None):
    """Append an audit entry.

    org_id/event_id are the tenant/event dimensions; passed where the action concerns
    an org/event, left None for platform-level actions (e.g. account management).
    actor_role/actor_email denormalize the actor's identity so the audit is a
    self-contained analytics surface; when the caller doesn't supply them they're
    resolved once from the user document. All ids stored as strings to match the
    existing actor_id convention."""
    if actor_role is None or actor_email is None:
        from app.models import user as user_model  # lazy: avoid model import cycle
        actor = user_model.find_by_id(actor_id)
        if actor:
            actor_role = actor_role if actor_role is not None else actor.get("role")
            actor_email = actor_email if actor_email is not None else actor.get("email")
    mongo.db.audit_log.insert_one(
        {
            "actor_id": str(actor_id),
            "actor_role": actor_role,
            "actor_email": actor_email,
            "action": action,
            "detail": detail,
            "org_id": str(org_id) if org_id else None,
            "event_id": str(event_id) if event_id else None,
            "ts": datetime.now(timezone.utc),
        }
    )


def query(filter=None, page=1, page_size=PAGE_SIZE):
    """Paginated, ts-desc audit read. `filter` is a fully-built Mongo query (the route
    composes the tier scope and any search clause). Returns (entries, total)."""
    filter = filter or {}
    total = mongo.db.audit_log.count_documents(filter)
    skip = max(0, (page - 1) * page_size)
    cursor = (
        mongo.db.audit_log.find(filter, {"_id": 0})
        .sort("ts", -1)
        .skip(skip)
        .limit(page_size)
    )
    entries = [{**doc, "ts": doc["ts"].isoformat()} for doc in cursor]
    return entries, total


def activity_buckets(actor_id, period, scope_filter=None):
    """Per-period counts of one actor's interaction entries, oldest→newest.
    `period` is 'day' | 'week' | 'month'; `scope_filter` narrows by tenant (org admin)."""
    unit = {"day": "day", "week": "week", "month": "month"}.get(period, "day")
    match = {"actor_id": str(actor_id)}
    if scope_filter:
        match.update(scope_filter)
    pipeline = [
        {"$match": match},
        {"$group": {"_id": {"$dateTrunc": {"date": "$ts", "unit": unit}}, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    out = []
    for doc in mongo.db.audit_log.aggregate(pipeline):
        bucket = doc["_id"]
        out.append({"bucket": bucket.isoformat() if bucket else None, "count": doc["count"]})
    return out


def login_count(actor_id):
    """Total successful logins for a user (platform-level metric)."""
    return mongo.db.audit_log.count_documents({"actor_id": str(actor_id), "action": "auth.login"})
