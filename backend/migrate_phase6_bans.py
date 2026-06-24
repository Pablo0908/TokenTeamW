"""Phase 6 migration — create the `bans` collection + indexes (idempotent, reversible).

Per-(user, org) bans bar an attendee from one org's events without touching the
platform account. This migration only provisions the collection/indexes — there is no
historical data to backfill (bans accrue from now on). create_app() already calls
ban.create_indexes() at startup; this script makes the provisioning explicit and
counted, and gives a clean rollback.

Targets the DB the backend .env points at (a DEV database here). Additive.

Usage:
    python migrate_phase6_bans.py            # create collection + indexes
    python migrate_phase6_bans.py --rollback # drop the bans collection

Safe to run repeatedly.
"""

import os
import sys

from app import create_app, mongo
from app.models import ban as ban_model

FLASK_ENV = os.getenv("FLASK_ENV", "development")


def _report():
    count = mongo.db.bans.count_documents({})
    idx = list(mongo.db.bans.index_information().keys())
    print(f"  bans: docs={count}, indexes={idx}")
    return count


def forward():
    print(f"\n=== Phase 6 bans (FORWARD) — DB='{mongo.db.name}' FLASK_ENV='{FLASK_ENV}' ===")
    before = _report()
    ban_model.create_indexes()  # idempotent
    print("  ensured bans indexes (unique user_id+org_id, org_id, created_at)")
    after = _report()
    assert after == before, "ban docs must be unchanged by index provisioning"
    assert "user_id_1_org_id_1" in mongo.db.bans.index_information(), "unique compound index missing"
    print("=== FORWARD complete; bans collection ready ===\n")


def rollback():
    print(f"\n=== Phase 6 bans (ROLLBACK) — DB='{mongo.db.name}' FLASK_ENV='{FLASK_ENV}' ===")
    before = _report()
    mongo.db.bans.drop()
    print(f"  dropped bans collection ({before} docs removed)")
    print("=== ROLLBACK complete ===\n")


def run():
    create_app()
    if "--rollback" in sys.argv:
        rollback()
    else:
        forward()


if __name__ == "__main__":
    run()
