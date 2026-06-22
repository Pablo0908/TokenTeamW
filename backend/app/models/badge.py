from datetime import datetime, timezone

from bson import ObjectId

from app import mongo
from app.models.event import fmt_date


def create_indexes():
    mongo.db.badges.create_index("event_id")
    mongo.db.badges.create_index("token", unique=True)


def _oid(value):
    return value if isinstance(value, ObjectId) else ObjectId(value)


def create_badge(event_id, name, description, token, qr_image, icon="🏅", color="primary", image=""):
    result = mongo.db.badges.insert_one(
        {
            "event_id": _oid(event_id),
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


def find_by_event(event_id):
    return list(mongo.db.badges.find({"event_id": _oid(event_id)}).sort("created_at", 1))


def find_by_token(event_id, token):
    return mongo.db.badges.find_one({"event_id": _oid(event_id), "token": token})


def find_by_id(badge_id):
    try:
        return mongo.db.badges.find_one({"_id": _oid(badge_id)})
    except Exception:
        return None


def count_for_event(event_id):
    return mongo.db.badges.count_documents({"event_id": _oid(event_id)})


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
