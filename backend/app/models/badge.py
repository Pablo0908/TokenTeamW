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


def count_for_event(event_id):
    return mongo.db.badges.count_documents({"event_id": _oid(event_id)})


def public_badge(badge, earned, redeemed_at=None):
    """Attendee-facing badge shape (never leaks token/qr internals)."""
    return {
        "id": str(badge["_id"]),
        "name": badge.get("name", ""),
        "description": badge.get("description", ""),
        "icon": badge.get("icon", "🏅"),
        "color": badge.get("color", "primary"),
        "earned": bool(earned),
        "date": fmt_date(redeemed_at) if redeemed_at else None,
    }
