from datetime import datetime, timezone

from bson import ObjectId

from app import mongo


# A platform-wide announcement (forum-style). Authored only by a super_admin, but
# readable by every authenticated user on the home page. It may optionally point at
# any event (across all orgs) so the card can link to that event's join/detail path.
#
# Unread tracking is NOT stored here: each user's last-seen timestamp lives on their
# own user document (`announcements_seen_at`); "unread" is `created_at > seen_at`,
# computed per-request. That keeps the announcement a single shared document instead
# of fanning a read-receipt out to every user.


def create_indexes():
    mongo.db.announcements.create_index([("created_at", -1)])


def _oid(value):
    return value if isinstance(value, ObjectId) else ObjectId(value)


def create(title, body, author_id, event_id=None):
    now = datetime.now(timezone.utc)
    result = mongo.db.announcements.insert_one(
        {
            "title": title,
            "body": body,
            # Optional association with any event (any org). Stored as ObjectId for
            # join consistency with `events`; None when the announcement is general.
            "event_id": _oid(event_id) if event_id else None,
            "author_id": _oid(author_id),
            "created_at": now,
            "updated_at": now,
        }
    )
    return str(result.inserted_id)


def find_by_id(announcement_id):
    try:
        return mongo.db.announcements.find_one({"_id": _oid(announcement_id)})
    except Exception:
        return None


def update(announcement_id, fields):
    """Patch whitelisted fields (title/body/event_id). event_id is coerced to an
    ObjectId, or cleared when explicitly set to None/empty. Returns matched > 0."""
    allowed = {}
    if "title" in fields:
        allowed["title"] = fields["title"]
    if "body" in fields:
        allowed["body"] = fields["body"]
    if "event_id" in fields:
        ev = fields["event_id"]
        allowed["event_id"] = _oid(ev) if ev else None
    if not allowed:
        return False
    allowed["updated_at"] = datetime.now(timezone.utc)
    res = mongo.db.announcements.update_one({"_id": _oid(announcement_id)}, {"$set": allowed})
    return res.matched_count > 0


def delete(announcement_id):
    try:
        res = mongo.db.announcements.delete_one({"_id": _oid(announcement_id)})
        return res.deleted_count > 0
    except Exception:
        return False


def list_all(limit=50):
    """Newest first, bounded — never an unbounded scan."""
    return list(mongo.db.announcements.find().sort("created_at", -1).limit(limit))


def public(doc, event=None, seen_at=None):
    """Shape for the client. `event` (optional) attaches minimal event metadata for
    the home link; `seen_at` (optional datetime) marks the entry unread when the
    announcement is newer than the viewer's last-seen timestamp."""
    if not doc:
        return None
    created = doc.get("created_at")
    out = {
        "id": str(doc["_id"]),
        "title": doc.get("title", ""),
        "body": doc.get("body", ""),
        "event_id": str(doc["event_id"]) if doc.get("event_id") else None,
        "created_at": created.isoformat() if hasattr(created, "isoformat") else created,
        "unread": bool(created and (seen_at is None or created > seen_at)),
    }
    if event is not None:
        out["event"] = {"id": str(event["_id"]), "name": event.get("name", "")}
    elif out["event_id"]:
        # Associated event no longer resolvable (deleted) — keep the id, drop the link.
        out["event"] = None
    return out
