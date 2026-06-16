from datetime import datetime, timezone

from bson import ObjectId

from app import mongo


def create_indexes():
    mongo.db.events.create_index("created_by")


def _oid(value):
    return value if isinstance(value, ObjectId) else ObjectId(value)


def parse_date(value):
    """Accept an ISO date ('2026-06-14') or datetime string; return a datetime or None."""
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        if "T" in text:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def fmt_date(value):
    if not value:
        return ""
    if isinstance(value, str):
        return value[:10]
    try:
        return value.date().isoformat()
    except AttributeError:
        return ""


def compute_status(start, end, now=None):
    """Derive the lifecycle status from the date window.

    No dates -> 'active' (an unscheduled event is treated as happening now, so a
    freshly-created demo event is immediately scannable). Redemption requires 'active'.
    """
    now = now or datetime.now(timezone.utc)
    today = now.date()
    start_d = start.date() if isinstance(start, datetime) else None
    end_d = end.date() if isinstance(end, datetime) else None
    if start_d and today < start_d:
        return "upcoming"
    if end_d and today > end_d:
        return "past"
    return "active"


def create_event(name, description, start_date, end_date, location, prize, created_by):
    result = mongo.db.events.insert_one(
        {
            "name": name,
            "description": description,
            "start_date": start_date,
            "end_date": end_date,
            "location": location,
            "prize": prize,
            "created_by": _oid(created_by),
            "created_at": datetime.now(timezone.utc),
        }
    )
    return str(result.inserted_id)


def find_by_id(event_id):
    try:
        return mongo.db.events.find_one({"_id": _oid(event_id)})
    except Exception:
        return None


def all_events():
    return list(mongo.db.events.find().sort("created_at", -1))


def event_summary(event, badges_total, badges_earned):
    """The shape every event-list/detail endpoint shares (matches the frontend contract)."""
    return {
        "id": str(event["_id"]),
        "name": event.get("name", ""),
        "description": event.get("description", ""),
        "date": fmt_date(event.get("start_date")),
        "endDate": fmt_date(event.get("end_date")),
        "location": event.get("location", ""),
        "prize": event.get("prize", ""),
        "status": compute_status(event.get("start_date"), event.get("end_date")),
        "badges_total": badges_total,
        "badges_earned": badges_earned,
        "completed": badges_total > 0 and badges_earned >= badges_total,
    }
