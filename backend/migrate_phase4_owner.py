"""Phase 4 migration — give organization #1 an owner (idempotent, reversible, counted).

P1 seeded org #1 ("lyfter") with `admin` memberships only, so owner-only actions
(change member roles, remove members, edit org, delete org) have no one to perform
them. This promotes org #1's `created_by` to `owner`. New orgs get an owner at
creation via the redeem flow, so this only fixes the migrated org #1.

Targets the DB the backend .env points at (a DEV database here). Additive.

Usage:
    python migrate_phase4_owner.py            # promote org #1 creator to owner
    python migrate_phase4_owner.py --rollback # demote that owner back to admin

Safe to run repeatedly.
"""

import os
import sys

from app import create_app, mongo
from app.models import organization as org_model
from app.models import membership as membership_model

FLASK_ENV = os.getenv("FLASK_ENV", "development")
ORG_SLUG = "lyfter"


def _report():
    org = org_model.find_by_slug(ORG_SLUG)
    if not org:
        return None
    owners = mongo.db.memberships.count_documents({"org_id": org["_id"], "role": "owner"})
    print(f"  org #1 ({org['_id']}) owners={owners}, created_by={org.get('created_by')}")
    return org


def forward():
    print(f"\n=== Phase 4 org #1 owner (FORWARD) — DB='{mongo.db.name}' FLASK_ENV='{FLASK_ENV}' ===")
    org = _report()
    if not org:
        print("  org #1 not found; nothing to do")
        return
    created_by = org.get("created_by")
    if not created_by:
        print("  org #1 has no created_by; cannot designate an owner — skipping")
        return
    membership_model.add_membership(created_by, org["_id"], "owner")  # upsert -> owner
    print(f"  promoted created_by {created_by} to owner")
    owners = mongo.db.memberships.count_documents({"org_id": org["_id"], "role": "owner"})
    assert owners >= 1, "org #1 still has no owner"
    _report()
    print("=== FORWARD complete; org #1 has an owner ===\n")


def rollback():
    print(f"\n=== Phase 4 org #1 owner (ROLLBACK) — DB='{mongo.db.name}' FLASK_ENV='{FLASK_ENV}' ===")
    org = org_model.find_by_slug(ORG_SLUG)
    if org and org.get("created_by"):
        membership_model.add_membership(org["created_by"], org["_id"], "admin")  # demote back
        print(f"  demoted {org['created_by']} back to admin")
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
