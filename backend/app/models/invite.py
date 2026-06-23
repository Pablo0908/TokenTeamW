import secrets
from datetime import datetime, timedelta, timezone

from bson import ObjectId

from app import mongo

# One unified, in-app invite system. `type` discriminates the three kinds so they
# share a single accept inbox (GET /me/invites):
#   - "create_org": super_admin -> recipient may create a NEW org (becomes its owner)
#   - "org_join":   super_admin or an org owner/admin -> recipient joins that org
#   - "event":      RESERVED for Phase 5 (announcements) — recipient gets the event
TYPES = ("create_org", "org_join", "event")
DEFAULT_TTL_DAYS = 14


def create_indexes():
    mongo.db.invites.create_index("token", unique=True)
    mongo.db.invites.create_index([("email", 1), ("status", 1)])
    mongo.db.invites.create_index("org_id")


def _oid(value):
    return value if isinstance(value, ObjectId) else ObjectId(value)


def _now():
    return datetime.now(timezone.utc)


def create(invite_type, email, invited_by, org_id=None, role=None, event_id=None, ttl_days=DEFAULT_TTL_DAYS):
    doc = {
        "type": invite_type,
        "email": (email or "").strip().lower(),
        "role": role,
        "org_id": _oid(org_id) if org_id else None,
        "event_id": _oid(event_id) if event_id else None,
        "token": secrets.token_urlsafe(24),
        "invited_by": _oid(invited_by) if invited_by else None,
        "status": "pending",
        "expires_at": _now() + timedelta(days=ttl_days),
        "created_at": _now(),
        "accepted_by": None,
        "accepted_at": None,
    }
    doc["_id"] = mongo.db.invites.insert_one(doc).inserted_id
    return doc


def public(inv, org=None):
    """Inbox/list shape (never leaks the raw token except where the caller owns it)."""
    return {
        "id": str(inv["_id"]),
        "type": inv["type"],
        "email": inv.get("email"),
        "role": inv.get("role"),
        "org_id": str(inv["org_id"]) if inv.get("org_id") else None,
        "org_name": (org or {}).get("name") if org else None,
        "status": inv.get("status"),
        "token": inv.get("token"),
        "expires_at": inv["expires_at"].isoformat() if inv.get("expires_at") else None,
        "created_at": inv["created_at"].isoformat() if inv.get("created_at") else None,
    }


def pending_for_email(email):
    return list(mongo.db.invites.find({
        "email": (email or "").strip().lower(),
        "status": "pending",
        "expires_at": {"$gt": _now()},
    }).sort("created_at", -1))


def list_for_org(org_id, invite_type=None):
    query = {"org_id": _oid(org_id)}
    if invite_type:
        query["type"] = invite_type
    return list(mongo.db.invites.find(query).sort("created_at", -1))


def list_by_type(invite_type):
    return list(mongo.db.invites.find({"type": invite_type}).sort("created_at", -1))


def find_by_id(invite_id):
    try:
        return mongo.db.invites.find_one({"_id": _oid(invite_id)})
    except Exception:
        return None


def revoke(invite_id):
    """Revoke a still-pending invite (idempotent-ish; only flips pending->revoked)."""
    res = mongo.db.invites.update_one(
        {"_id": _oid(invite_id), "status": "pending"}, {"$set": {"status": "revoked"}}
    )
    return res.modified_count > 0


def accept_atomic(token, accepting_email, accepting_user_id):
    """Race-safe single-use accept: only a pending, unexpired invite addressed to the
    accepting account's email flips to accepted. Returns the (pre-update) invite doc on
    success, or None if it was already used / expired / not for this email."""
    return mongo.db.invites.find_one_and_update(
        {
            "token": token,
            "status": "pending",
            "email": (accepting_email or "").strip().lower(),
            "expires_at": {"$gt": _now()},
        },
        {"$set": {"status": "accepted", "accepted_by": _oid(accepting_user_id), "accepted_at": _now()}},
    )
