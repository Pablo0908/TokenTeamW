"""Phase 7 migration — backfill event `visibility` (idempotent, reversible, counted).

P7 adds a `visibility` field to events ("public" | "unlisted" | "scan-only"). Existing
events predate the field; this sets them all to "public" so current discovery behavior
is preserved for them. New events get a visibility at creation.

Targets the DB the backend .env points at (a DEV database here). Additive.

Usage:
    python migrate_phase7_visibility.py            # backfill missing visibility -> "public"
    python migrate_phase7_visibility.py --rollback # remove the visibility field

Safe to run repeatedly.
"""

import os
import sys

from app import create_app, mongo

FLASK_ENV = os.getenv("FLASK_ENV", "development")


def _report():
    total = mongo.db.events.count_documents({})
    missing = mongo.db.events.count_documents({"visibility": {"$exists": False}})
    public = mongo.db.events.count_documents({"visibility": "public"})
    print(f"  events: total={total}, missing visibility={missing}, public={public}")
    return total, missing


def forward():
    print(f"\n=== Phase 7 visibility (FORWARD) — DB='{mongo.db.name}' FLASK_ENV='{FLASK_ENV}' ===")
    total_before, missing_before = _report()
    res = mongo.db.events.update_many({"visibility": {"$exists": False}}, {"$set": {"visibility": "public"}})
    print(f"  backfilled visibility='public' on {res.modified_count} event(s)")
    total_after, missing_after = _report()
    assert total_after == total_before, "event count must not change"
    assert missing_after == 0, "every event must have a visibility after backfill"
    print("=== FORWARD complete; no events left without visibility ===\n")


def rollback():
    print(f"\n=== Phase 7 visibility (ROLLBACK) — DB='{mongo.db.name}' FLASK_ENV='{FLASK_ENV}' ===")
    _report()
    res = mongo.db.events.update_many({"visibility": {"$exists": True}}, {"$unset": {"visibility": ""}})
    print(f"  removed visibility from {res.modified_count} event(s)")
    _report()
    print("=== ROLLBACK complete ===\n")


def run():
    create_app()
    if "--rollback" in sys.argv:
        rollback()
    else:
        forward()


if __name__ == "__main__":
    run()
