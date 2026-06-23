import re
from datetime import datetime, timezone

from bson import ObjectId

from app import mongo


def create_indexes():
    mongo.db.events.create_index("created_by")
    mongo.db.events.create_index("org_id")


def _oid(value):
    return value if isinstance(value, ObjectId) else ObjectId(value)


def search_ids(q):
    """Event ids (as strings) whose name matches `q` (case-insensitive). Used to
    resolve an audit search term to events."""
    rx = {"$regex": re.escape(q), "$options": "i"}
    return [str(doc["_id"]) for doc in mongo.db.events.find({"name": rx}, {"_id": 1})]


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


def create_event(name, description, start_date, end_date, location, prize, created_by, org_id=None):
    result = mongo.db.events.insert_one(
        {
            "name": name,
            "description": description,
            "start_date": start_date,
            "end_date": end_date,
            "location": location,
            "prize": prize,
            # Authoritative tenant pointer. Optional at the model layer so existing
            # callers don't break; the admin route resolves and passes it.
            "org_id": _oid(org_id) if org_id else None,
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


def all_events(org_id=None):
    """All events, newest first. When org_id is given, scope to that tenant;
    omitted = current global behavior, unchanged."""
    query = {"org_id": _oid(org_id)} if org_id else {}
    return list(mongo.db.events.find(query).sort("created_at", -1))


def event_summary(event, badges_total, badges_earned, org=None):
    """The shape every event-list/detail endpoint shares (matches the frontend contract).

    `org_id` and (when the org document is passed) minimal `org` metadata are added
    additively — existing clients ignore unknown fields, so behavior is unchanged.
    """
    summary = {
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
        "org_id": str(event["org_id"]) if event.get("org_id") else None,
    }
    if org is not None:
        summary["org"] = {
            "id": str(org["_id"]),
            "name": org.get("name", ""),
            "slug": org.get("slug", ""),
        }
    return summary
