from datetime import datetime, timezone

from bson import ObjectId

from app import mongo


# A ban is (user × org): an attendee barred from scanning at an org's events. It is
# strictly org-scoped — it NEVER touches the platform-level account (that's
# user.disabled, super-admin only). Mirrors the membership model's shape/guards.


def create_indexes():
    # Compound unique key = the per-user-per-org guard AND the membership-style
    # is-this-user-banned-here lookup. A separate org_id index serves the reverse
    # ("who is banned in this org"); created_at supports housekeeping.
    mongo.db.bans.create_index([("user_id", 1), ("org_id", 1)], unique=True)
    mongo.db.bans.create_index("org_id")
    mongo.db.bans.create_index("created_at")


def _oid(value):
    return value if isinstance(value, ObjectId) else ObjectId(value)


def add_ban(user_id, org_id, banned_by, reason=""):
    """Idempotent: upsert on (user_id, org_id). Re-running refreshes reason/actor only."""
    now = datetime.now(timezone.utc)
    mongo.db.bans.update_one(
        {"user_id": _oid(user_id), "org_id": _oid(org_id)},
        {
            "$set": {"reason": reason or "", "banned_by": _oid(banned_by) if banned_by else None},
            "$setOnInsert": {
                "user_id": _oid(user_id),
                "org_id": _oid(org_id),
                "created_at": now,
            },
        },
        upsert=True,
    )


def remove_ban(user_id, org_id):
    mongo.db.bans.delete_one({"user_id": _oid(user_id), "org_id": _oid(org_id)})


def is_banned(user_id, org_id):
    """True when this user is banned in this org. A missing org_id (legacy/global
    resource) can't carry a ban, so callers guard the scan path uniformly."""
    if not org_id:
        return False
    try:
        return mongo.db.bans.find_one({"user_id": _oid(user_id), "org_id": _oid(org_id)}) is not None
    except Exception:
        return False


def banned_user_ids(org_id):
    """Set of user_id strings banned in this org (one query — annotates the people list)."""
    try:
        cursor = mongo.db.bans.find({"org_id": _oid(org_id)}, {"user_id": 1})
    except Exception:
        return set()
    return {str(doc["user_id"]) for doc in cursor}


def delete_by_user(user_id):
    """Remove all of a deleted user's bans (cascade, mirrors redemption.delete_by_user)."""
    mongo.db.bans.delete_many({"user_id": _oid(user_id)})
