from datetime import datetime, timezone

from bson import ObjectId

from app import mongo
from app.models.event import fmt_date


# A prize_claim records that a COMPLETED user has physically received their prize — the
# real-world handover, which event completion alone does not capture. It is flipped exactly
# once, by authorized staff scanning the user in person (the inverse of a badge redemption:
# there an attendee scans a badge; here staff scan the attendee).
#
# Design: "unclaimed" is the ABSENCE of a row. Generating the claim QR must change no state,
# so we never persist an unclaimed row; the award is an INSERT guarded by the
# (user_id, event_id) unique index — the same race-safe mechanism as redemption.redeem().
# Two staff scanning the same user at once → exactly one insert wins, the other raises
# DuplicateKeyError. The stored row carries status:"claimed" for clarity/extensibility.
def create_indexes():
    # The compound unique index is the race guard — the DB, not app logic, enforces
    # one claim per (user, event). This is what makes the check-and-flip atomic.
    mongo.db.prize_claims.create_index([("user_id", 1), ("event_id", 1)], unique=True)
    mongo.db.prize_claims.create_index("org_id")
    mongo.db.prize_claims.create_index("event_id")


def _oid(value):
    return value if isinstance(value, ObjectId) else ObjectId(value)


def award(user_id, event_id, org_id, awarded_by, claimant_name=None):
    """Atomically record the award. Raises pymongo.errors.DuplicateKeyError if this
    (user, event) was already claimed — that raise IS the double-claim guard. Returns
    the inserted claim document. The server flip here is the award; the QR has no say."""
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": _oid(user_id),
        "event_id": _oid(event_id),
        "org_id": _oid(org_id) if org_id else None,
        "status": "claimed",
        "awarded_by": _oid(awarded_by),
        "awarded_at": now,
        "claimant_name": (claimant_name or "").strip() or None,
    }
    mongo.db.prize_claims.insert_one(doc)
    return doc


def find(user_id, event_id):
    """The existing claim for (user, event), or None (None == still unclaimed)."""
    try:
        return mongo.db.prize_claims.find_one({"user_id": _oid(user_id), "event_id": _oid(event_id)})
    except Exception:
        return None


def public_claim(doc, awarded_by_name=None):
    """Serialize a claim for the API (ids->str, ts->iso). `awarded_by_name` is the
    resolved staff display name (the model doesn't reach into users itself)."""
    if not doc:
        return None
    awarded_at = doc.get("awarded_at")
    return {
        "status": doc.get("status", "claimed"),
        "awarded_by": str(doc["awarded_by"]) if doc.get("awarded_by") else None,
        "awarded_by_name": awarded_by_name,
        "awarded_at": awarded_at.isoformat() if awarded_at else None,
        "awarded_on": fmt_date(awarded_at) if awarded_at else None,
        "claimant_name": doc.get("claimant_name"),
    }


def delete_by_user(user_id):
    """Remove all claims belonging to a deleted user (cascade parity with redemptions)."""
    mongo.db.prize_claims.delete_many({"user_id": _oid(user_id)})
