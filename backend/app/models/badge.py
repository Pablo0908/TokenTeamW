from datetime import datetime, timezone

from bson import ObjectId

from app import mongo
from app.models.event import fmt_date


def create_indexes():
    mongo.db.badges.create_index("event_id")
    mongo.db.badges.create_index("token", unique=True)
    mongo.db.badges.create_index("org_id")


def _oid(value):
    return value if isinstance(value, ObjectId) else ObjectId(value)


def create_badge(event_id, name, description, token, qr_image, icon="🏅", color="primary", image="", org_id=None):
    result = mongo.db.badges.insert_one(
        {
            "event_id": _oid(event_id),
            # Denormalized from the parent event so badge queries can scope by tenant
            # without a join. Always set from the event's org_id at the call site.
            "org_id": _oid(org_id) if org_id else None,
            "name": name,
            "description": description,
            "icon": icon,
            "color": color,
            "image": image,
            "token": token,
            "qr_image": qr_image,
            "created_at": datetime.now(timezone.utc),
        }
    )
    return str(result.inserted_id)


def find_by_event(event_id, org_id=None):
    """Badges for an event. An optional org_id adds a defense-in-depth tenant guard
    (the event_id already implies the tenant); omitted = unchanged behavior."""
    query = {"event_id": _oid(event_id)}
    if org_id:
        query["org_id"] = _oid(org_id)
    return list(mongo.db.badges.find(query).sort("created_at", 1))


def find_by_token(event_id, token):
    return mongo.db.badges.find_one({"event_id": _oid(event_id), "token": token})


def find_by_id(badge_id):
    try:
        return mongo.db.badges.find_one({"_id": _oid(badge_id)})
    except Exception:
        return None


def count_for_event(event_id):
    return mongo.db.badges.count_documents({"event_id": _oid(event_id)})


def count_for_org(org_id):
    """Total badges minted across an org's events (uses the denormalized org_id)."""
    return mongo.db.badges.count_documents({"org_id": _oid(org_id)})


def compute_rarity(redeemed_by, total_attendees):
    """Tier a badge by how few attendees have collected it. Returns None when there's not
    enough signal yet (no attendees, or nobody has earned it) so the UI shows no tier."""
    if not total_attendees or not redeemed_by or redeemed_by <= 0:
        return None
    rate = redeemed_by / total_attendees
    if rate <= 0.05:
        return "legendary"
    if rate <= 0.15:
        return "epic"
    if rate <= 0.40:
        return "rare"
    return "common"


def public_badge(badge, earned, redeemed_at=None, redeemed_by=None, total_attendees=None):
    """Attendee-facing badge shape (never leaks token/qr internals). When `redeemed_by`
    is supplied, also exposes the collected count and a rarity tier."""
    out = {
        "id": str(badge["_id"]),
        "name": badge.get("name", ""),
        "description": badge.get("description", ""),
        "icon": badge.get("icon", "🏅"),
        "color": badge.get("color", "primary"),
        "image": badge.get("image", ""),
        "earned": bool(earned),
        "date": fmt_date(redeemed_at) if redeemed_at else None,
    }
    if redeemed_by is not None:
        out["redeemed_by"] = redeemed_by
        rarity = compute_rarity(redeemed_by, total_attendees)
        if rarity:
            out["rarity"] = rarity
    return out
