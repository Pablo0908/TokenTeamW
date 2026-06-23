"""Phase 2 audit migration — idempotent, reversible, count-verified.

Backfills the denormalized actor identity (actor_role, actor_email) onto historical
audit_log entries by resolving each entry's actor_id. Entries whose actor no longer
exists get explicit nulls so the field shape is consistent. org_id was already
backfilled in Phase 1; event_id is intentionally left as-is (not reliably derivable
from the historical free-text detail), and login/signup history cannot be
reconstructed — those accrue only from now on.

Targets whatever DB the backend .env points at (a DEV database here). Additive and
non-destructive.

Usage:
    python migrate_phase2_audit.py            # backfill actor_role/actor_email
    python migrate_phase2_audit.py --rollback # unset actor_role/actor_email

Safe to run repeatedly: only entries missing the fields are touched.
"""

import os
import sys

from app import create_app, mongo
from app.models import user as user_model

FLASK_ENV = os.getenv("FLASK_ENV", "development")


def forward():
    db = mongo.db
    print(f"\n=== Phase 2 audit backfill (FORWARD) — DB='{db.name}' FLASK_ENV='{FLASK_ENV}' ===")
    total = db.audit_log.count_documents({})
    before = db.audit_log.count_documents({"actor_email": {"$exists": True}})
    print(f"  [before] audit total={total}, with actor_email field={before}")

    need = list(
        db.audit_log.find(
            {"$or": [{"actor_email": {"$exists": False}}, {"actor_role": {"$exists": False}}]},
            {"actor_id": 1},
        )
    )
    cache = {}
    updated = unresolved = 0
    for doc in need:
        aid = doc.get("actor_id")
        if aid not in cache:
            cache[aid] = user_model.find_by_id(aid)
        u = cache[aid]
        if u:
            db.audit_log.update_one(
                {"_id": doc["_id"]},
                {"$set": {"actor_role": u.get("role"), "actor_email": u.get("email")}},
            )
            updated += 1
        else:
            # Actor deleted: set explicit nulls so the field exists (and won't re-match).
            db.audit_log.update_one(
                {"_id": doc["_id"]}, {"$set": {"actor_role": None, "actor_email": None}}
            )
            unresolved += 1

    after = db.audit_log.count_documents({"actor_email": {"$exists": True}})
    print(f"  backfilled identity on {updated}; {unresolved} unresolved (actor deleted)")
    print(f"  [after] with actor_email field={after}/{total}")
    assert after == total, f"{total - after} entry(ies) still missing the actor_email field"
    print("=== FORWARD complete; every entry now carries the identity fields ===\n")


def rollback():
    db = mongo.db
    print(f"\n=== Phase 2 audit backfill (ROLLBACK) — DB='{db.name}' FLASK_ENV='{FLASK_ENV}' ===")
    before = db.audit_log.count_documents({"actor_email": {"$exists": True}})
    r = db.audit_log.update_many({}, {"$unset": {"actor_role": "", "actor_email": ""}})
    print(f"  unset actor_role/actor_email on {r.modified_count} (had field on {before})")
    print("=== ROLLBACK complete ===\n")


def run():
    create_app()
    if "--rollback" in sys.argv:
        rollback()
    else:
        forward()


if __name__ == "__main__":
    run()
