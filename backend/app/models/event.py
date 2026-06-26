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


def compute_status(start, end, now=None, started=False, paused=False, ended=False):
    """Derive the lifecycle status. Start/Stop is the MASTER SWITCH: an event is only
    scannable ('active') once it has been explicitly started. A freshly created event is
    'upcoming' (closed) until its creator presses Start, and Stop closes it again.

    Dates (`start`/`end`) are informational only — shown in the UI, they do NOT auto-open
    or auto-close scanning (kept in the signature for callers/back-compat).

    Precedence, highest first:
      - `ended`  -> 'past'     (terminal moderation: in past events, not scannable)
      - `paused` -> 'locked'   (temporary lock: earned badges visible, cannot scan)
      - `started`-> 'active'   (open for scanning)
      - otherwise -> 'upcoming' (created but not started → not scannable)
    """
    if ended:
        return "past"
    if paused:
        return "locked"
    if started:
        return "active"
    return "upcoming"


def status_of(event, now=None):
    """Status for an event document, applying its moderation overrides. The single
    source of truth used by the feed, the redeem gate and the summary payload."""
    return compute_status(
        event.get("start_date"), event.get("end_date"), now=now,
        started=event.get("started", False),
        paused=event.get("paused", False),
        ended=event.get("ended", False),
    )


VISIBILITIES = ("public", "unlisted", "scan-only")


def create_event(name, description, start_date, end_date, location, prize, created_by,
                  org_id=None, event_type="uncategorized", visibility="public",
                  platform_event=False):
    result = mongo.db.events.insert_one(
        {
            "name": name,
            "description": description,
            "start_date": start_date,
            "end_date": end_date,
            "location": location,
            "prize": prize,
            # Category/class for analytics (e.g. "favorite event type"). Existing
            # events are backfilled as "uncategorized".
            "event_type": event_type or "uncategorized",
            # Feed visibility (P7): "public" = listed in members'/participants' feeds;
            # "unlisted" = not listed except to org members, still reachable by link;
            # "scan-only" = never listed, reachable only via its QR. Governs the LIST,
            # not hard detail access. Existing events are backfilled as "public".
            "visibility": visibility if visibility in VISIBILITIES else "public",
            # Authoritative tenant pointer. Optional at the model layer so existing
            # callers don't break; the admin route resolves and passes it.
            "org_id": _oid(org_id) if org_id else None,
            # True = created from the platform (super-admin) panel. Such events are
            # platform-level and are excluded from org control panels/dashboards, which
            # show only events an org created for itself. False = an org's own event.
            "platform_event": bool(platform_event),
            # Manual activation override (see compute_status). False = status follows
            # the date window; True = forced active/scannable now.
            "started": False,
            # Moderation overrides: paused = temporary lock (status 'locked'), ended =
            # terminal (status 'past'). Both block redemption while set.
            "paused": False,
            "ended": False,
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


def delete_event(event_id):
    """Remove the event document itself. Cascading of its badges/redemptions/claims is the
    caller's responsibility (the delete route does the full cascade)."""
    try:
        return mongo.db.events.delete_one({"_id": _oid(event_id)}).deleted_count
    except Exception:
        return 0


def set_started(event_id, started: bool):
    """Flip the manual activation override. Returns matched count > 0."""
    return _set_flag(event_id, "started", started)


def set_paused(event_id, paused: bool):
    """Flip the temporary moderation lock ('locked'). Returns matched count > 0."""
    return _set_flag(event_id, "paused", paused)


def set_ended(event_id, ended: bool):
    """Flip the terminal moderation state ('past'). Returns matched count > 0."""
    return _set_flag(event_id, "ended", ended)


def _set_flag(event_id, field, value):
    try:
        res = mongo.db.events.update_one({"_id": _oid(event_id)}, {"$set": {field: bool(value)}})
        return res.matched_count > 0
    except Exception:
        return False


def all_events(org_id=None, exclude_platform=False):
    """All events, newest first. When org_id is given, scope to that tenant;
    omitted = current global behavior, unchanged. exclude_platform=True drops
    platform (super-admin-panel) events — used by org-scoped views, which must show
    only events the org created for itself."""
    query = {"org_id": _oid(org_id)} if org_id else {}
    if exclude_platform:
        query["platform_event"] = {"$ne": True}
    return list(mongo.db.events.find(query).sort("created_at", -1))


def feed_events_for_user(user_id):
    """The attendee events feed. Visibility governs listing:
      - "public"    -> listed to EVERYONE (global discovery — no org scoping)
      - "unlisted"  -> listed only to members of that event's org
      - "scan-only" -> never listed (reachable only via its QR)
    Newest first.
    """
    from app.models import membership as membership_model

    member_orgs = set(membership_model.orgs_for_user(user_id))
    out = []
    for ev in mongo.db.events.find({}).sort("created_at", -1):
        vis = ev.get("visibility", "public")
        org_str = str(ev["org_id"]) if ev.get("org_id") else None
        if vis == "public" or (vis == "unlisted" and org_str in member_orgs):
            out.append(ev)
    return out


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
        "status": status_of(event),
        "started": bool(event.get("started", False)),
        "paused": bool(event.get("paused", False)),
        "ended": bool(event.get("ended", False)),
        "badges_total": badges_total,
        "badges_earned": badges_earned,
        "completed": badges_total > 0 and badges_earned >= badges_total,
        "event_type": event.get("event_type", "uncategorized"),
        "visibility": event.get("visibility", "public"),
        "org_id": str(event["org_id"]) if event.get("org_id") else None,
    }
    if org is not None:
        summary["org"] = {
            "id": str(org["_id"]),
            "name": org.get("name", ""),
            "slug": org.get("slug", ""),
            "theme": org.get("theme") or {},
        }
    return summary
