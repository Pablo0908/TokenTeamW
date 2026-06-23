from datetime import datetime, timezone

from bson import ObjectId

from app import mongo


# A membership is (user × org × role). It is the org-scoped authority model that
# `users.role` (a single global string) cannot express: an "admin" of org #2 only.
# Platform-level authority (super_admin) lives on the user document, not here.
ROLES = ("owner", "admin", "staff")


def create_indexes():
    # The compound unique key is the per-user-per-org guard AND serves user_id-prefix
    # lookups ("which orgs is this user in"). A separate org_id index serves the
    # reverse ("who belongs to this org").
    mongo.db.memberships.create_index([("user_id", 1), ("org_id", 1)], unique=True)
    mongo.db.memberships.create_index("org_id")


def _oid(value):
    return value if isinstance(value, ObjectId) else ObjectId(value)


def add_membership(user_id, org_id, role):
    """Idempotent: upsert on (user_id, org_id). Re-running only updates the role."""
    now = datetime.now(timezone.utc)
    mongo.db.memberships.update_one(
        {"user_id": _oid(user_id), "org_id": _oid(org_id)},
        {
            "$set": {"role": role},
            "$setOnInsert": {
                "user_id": _oid(user_id),
                "org_id": _oid(org_id),
                "created_at": now,
            },
        },
        upsert=True,
    )


def find(user_id, org_id):
    try:
        return mongo.db.memberships.find_one({"user_id": _oid(user_id), "org_id": _oid(org_id)})
    except Exception:
        return None


def role_in_org(user_id, org_id):
    """The user's role string in this org, or None if not a member."""
    doc = find(user_id, org_id)
    return doc.get("role") if doc else None


def orgs_for_user(user_id):
    """List of org_id strings this user is a member of (any role)."""
    try:
        cursor = mongo.db.memberships.find({"user_id": _oid(user_id)}, {"org_id": 1})
    except Exception:
        return []
    return [str(doc["org_id"]) for doc in cursor]


def admin_orgs_for_user(user_id):
    """org_id strings where the user is an org owner or admin (admin-tier authority).
    Used to scope admin-only reads like the audit to the orgs they administer."""
    try:
        cursor = mongo.db.memberships.find(
            {"user_id": _oid(user_id), "role": {"$in": ["owner", "admin"]}}, {"org_id": 1}
        )
    except Exception:
        return []
    return [str(doc["org_id"]) for doc in cursor]
