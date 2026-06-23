"""Phase 3 migration — backfill events.event_type (idempotent, reversible, counted).

Adds the event_type category to events that predate the field, as "uncategorized",
so the per-user "favorite event type" analytic is well-defined for every redemption.
Targets whatever DB the backend .env points at (a DEV database here). Additive.

Usage:
    python migrate_phase3_event_type.py            # backfill uncategorized
    python migrate_phase3_event_type.py --rollback # unset event_type

Safe to run repeatedly: only events missing the field are touched.
"""

import os
import sys

from app import create_app, mongo

FLASK_ENV = os.getenv("FLASK_ENV", "development")


def forward():
    db = mongo.db
    print(f"\n=== Phase 3 event_type backfill (FORWARD) — DB='{db.name}' FLASK_ENV='{FLASK_ENV}' ===")
    total = db.events.count_documents({})
    before = db.events.count_documents({"event_type": {"$exists": True}})
    r = db.events.update_many(
        {"$or": [{"event_type": {"$exists": False}}, {"event_type": None}, {"event_type": ""}]},
        {"$set": {"event_type": "uncategorized"}},
    )
    after = db.events.count_documents({"event_type": {"$exists": True}})
    print(f"  events total={total}; had event_type={before}; backfilled {r.modified_count}; now have field={after}")
    assert after == total, f"{total - after} event(s) still missing event_type"
    print("=== FORWARD complete ===\n")


def rollback():
    db = mongo.db
    print(f"\n=== Phase 3 event_type backfill (ROLLBACK) — DB='{db.name}' FLASK_ENV='{FLASK_ENV}' ===")
    r = db.events.update_many({}, {"$unset": {"event_type": ""}})
    print(f"  unset event_type on {r.modified_count}")
    print("=== ROLLBACK complete ===\n")


def run():
    create_app()
    if "--rollback" in sys.argv:
        rollback()
    else:
        forward()


if __name__ == "__main__":
    run()
