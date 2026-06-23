from datetime import datetime, timezone

from app import mongo


def create_indexes():
    mongo.db.audit_log.create_index([("ts", -1)])
    mongo.db.audit_log.create_index([("actor_id", 1)])
    mongo.db.audit_log.create_index("org_id")
    mongo.db.audit_log.create_index("event_id")
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


def recent(limit=150):
    cursor = mongo.db.audit_log.find({}, {"_id": 0}).sort("ts", -1).limit(limit)
    return [{**doc, "ts": doc["ts"].isoformat()} for doc in cursor]


def recent_for_orgs(org_ids, limit=150):
    """Audit entries for the given orgs (org_id is stored as a string), newest first.
    Used to scope an org admin to their own org(s)."""
    cursor = (
        mongo.db.audit_log.find({"org_id": {"$in": list(org_ids)}}, {"_id": 0})
        .sort("ts", -1)
        .limit(limit)
    )
    return [{**doc, "ts": doc["ts"].isoformat()} for doc in cursor]
