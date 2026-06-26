"""Phase 1 tenancy migration — idempotent, reversible, count-verified.

Makes the existing single-brand data tenant-ready WITHOUT changing end-user behavior:
  - create organization #1 for the existing brand (slug "lyfter"),
  - backfill org_id onto events (authoritative) and, denormalized FROM THE PARENT
    EVENT, onto badges and redemptions,
  - backfill org_id (and event_id shape) onto historical audit_log entries,
  - add platform_role: None to users for shape consistency,
  - backfill org #1 memberships from the legacy global role.

NOTE: the old "auto-promote admins to super_admin" step was REMOVED — it was a security
risk. Platform owners are named explicitly and granted in-app via
PATCH /admin/users/<id>/super-admin by an existing super admin. This migration never
elevates anyone.

Targets whatever DB the backend .env points at (a DEV database operation).

Usage:
    python migrate_phase1_tenancy.py             # forward migration
    python migrate_phase1_tenancy.py --rollback  # undo (unset fields, drop org #1 + its memberships)

Safe to run repeatedly: every step only touches documents not already migrated.
"""

import os
import sys

from bson import ObjectId

from app import create_app, mongo
from app.models import organization as org_model
from app.models import membership as membership_model

ORG_SLUG = "lyfter"
ORG_NAME = "Lyfter"

FLASK_ENV = os.getenv("FLASK_ENV", "development")
IS_PRODUCTION = FLASK_ENV == "production"


# ─────────────────────────────────────────────────────────────────────────────
def _counts(label):
    db = mongo.db
    print(
        f"  [{label}] orgs={db.organizations.count_documents({})} "
        f"memberships={db.memberships.count_documents({})} "
        f"users={db.users.count_documents({})} "
        f"events={db.events.count_documents({})} "
        f"badges={db.badges.count_documents({})} "
        f"redemptions={db.redemptions.count_documents({})} "
        f"audit={db.audit_log.count_documents({})}"
    )


def _ensure_org_one():
    """Find-or-create organization #1. Idempotent via the unique slug."""
    existing = org_model.find_by_slug(ORG_SLUG)
    if existing:
        print(f"  org #1 already exists: {ORG_SLUG} ({existing['_id']})")
        return existing["_id"]
    first_admin = mongo.db.users.find_one({"role": "admin"}, sort=[("created_at", 1)])
    created_by = str(first_admin["_id"]) if first_admin else None
    org_id = org_model.create_org(ORG_NAME, ORG_SLUG, created_by=created_by, description="")
    print(f"  created org #1: {ORG_SLUG} ({org_id}) created_by={created_by}")
    return ObjectId(org_id)


def forward():
    print(f"\n=== Phase 1 migration (FORWARD) — DB='{mongo.db.name}' FLASK_ENV='{FLASK_ENV}' ===")
    _counts("before")

    # 1) Organization #1
    org_oid = _ensure_org_one()

    # 1b) description shape — backfill orgs created before the field existed.
    r = mongo.db.organizations.update_many(
        {"description": {"$exists": False}}, {"$set": {"description": ""}}
    )
    print(f"  organizations: set description shape on {r.modified_count}")

    # 2) events.org_id — every existing event belongs to the single existing brand.
    r = mongo.db.events.update_many(
        {"$or": [{"org_id": {"$exists": False}}, {"org_id": None}]},
        {"$set": {"org_id": org_oid}},
    )
    print(f"  events: set org_id on {r.modified_count} (matched {r.matched_count})")

    # 3) badges.org_id — DENORMALIZED FROM THE PARENT EVENT (correct even if many orgs).
    badges_set = 0
    for ev in mongo.db.events.find({}, {"org_id": 1}):
        res = mongo.db.badges.update_many(
            {"event_id": ev["_id"], "$or": [{"org_id": {"$exists": False}}, {"org_id": None}]},
            {"$set": {"org_id": ev["org_id"]}},
        )
        badges_set += res.modified_count
    print(f"  badges: set org_id from parent event on {badges_set}")

    # 4) redemptions.org_id — denormalized from the parent event.
    redemptions_set = 0
    for ev in mongo.db.events.find({}, {"org_id": 1}):
        res = mongo.db.redemptions.update_many(
            {"event_id": ev["_id"], "$or": [{"org_id": {"$exists": False}}, {"org_id": None}]},
            {"$set": {"org_id": ev["org_id"]}},
        )
        redemptions_set += res.modified_count
    print(f"  redemptions: set org_id from parent event on {redemptions_set}")

    # 5) audit_log — all historical entries belong to org #1 (single tenant until now).
    #    event_id is left null: it is not reliably derivable from the free-text detail.
    #    Stored as strings to match the existing actor_id / new log() convention.
    r = mongo.db.audit_log.update_many(
        {"$or": [{"org_id": {"$exists": False}}, {"org_id": None}]},
        {"$set": {"org_id": str(org_oid)}},
    )
    r2 = mongo.db.audit_log.update_many(
        {"event_id": {"$exists": False}}, {"$set": {"event_id": None}}
    )
    print(f"  audit_log: set org_id on {r.modified_count}, event_id shape on {r2.modified_count}")

    # 6) users.platform_role shape (does NOT promote anyone).
    r = mongo.db.users.update_many(
        {"platform_role": {"$exists": False}}, {"$set": {"platform_role": None}}
    )
    print(f"  users: set platform_role:None on {r.modified_count}")

    # 7) Super-admin promotion is intentionally NOT performed here. Auto-promoting admins
    #    to super_admin was a security risk and has been removed. Platform owners are named
    #    explicitly and granted in-app (PATCH /admin/users/<id>/super-admin) by an existing
    #    super admin. This migration never elevates anyone.

    # 8) Memberships from the legacy global role.
    admins = list(mongo.db.users.find({"role": "admin"}, {"_id": 1}))
    assistants = list(mongo.db.users.find({"role": "assistant"}, {"_id": 1}))
    for u in admins:
        membership_model.add_membership(u["_id"], org_oid, "admin")
    for u in assistants:
        membership_model.add_membership(u["_id"], org_oid, "staff")
    print(f"  memberships: ensured org #1 admin x{len(admins)}, staff x{len(assistants)}")

    # 8b) Drop memberships whose user no longer exists. The app's delete_user does
    #     not yet cascade memberships, so account deletions during normal use can
    #     leave orphans; clean them so "nothing orphaned" holds (idempotent).
    user_ids = {u["_id"] for u in mongo.db.users.find({}, {"_id": 1})}
    orphan_ids = [m["_id"] for m in mongo.db.memberships.find({}, {"user_id": 1})
                  if m["user_id"] not in user_ids]
    if orphan_ids:
        mongo.db.memberships.delete_many({"_id": {"$in": orphan_ids}})
    print(f"  memberships: removed {len(orphan_ids)} orphaned (deleted user)")

    _counts("after")
    _assert_integrity(org_oid)
    print("=== FORWARD complete; integrity assertions passed ===\n")


def _assert_integrity(org_oid):
    db = mongo.db
    no_org = {"$or": [{"org_id": {"$exists": False}}, {"org_id": None}]}
    e = db.events.count_documents(no_org)
    b = db.badges.count_documents(no_org)
    rd = db.redemptions.count_documents(no_org)
    assert e == 0, f"{e} event(s) still missing org_id"
    assert b == 0, f"{b} badge(s) still missing org_id"
    assert rd == 0, f"{rd} redemption(s) still missing org_id"

    # Denormalized org_id must equal the parent event's org_id (no drift).
    mismatches = 0
    event_org = {ev["_id"]: ev.get("org_id") for ev in db.events.find({}, {"org_id": 1})}
    for coll in ("badges", "redemptions"):
        for doc in db[coll].find({}, {"event_id": 1, "org_id": 1}):
            if event_org.get(doc.get("event_id")) != doc.get("org_id"):
                mismatches += 1
    assert mismatches == 0, f"{mismatches} badge/redemption org_id != parent event org_id"

    # Coverage: every current admin/assistant must hold its org #1 membership. (We
    # check coverage, not an exact count, so role changes made via the live app
    # don't make a re-run spuriously fail.)
    missing = 0
    for u in db.users.find({"role": "admin"}, {"_id": 1}):
        if not db.memberships.count_documents({"user_id": u["_id"], "org_id": org_oid, "role": "admin"}):
            missing += 1
    for u in db.users.find({"role": "assistant"}, {"_id": 1}):
        if not db.memberships.count_documents({"user_id": u["_id"], "org_id": org_oid, "role": "staff"}):
            missing += 1
    assert missing == 0, f"{missing} admin/assistant user(s) missing their org #1 membership"

    # No orphaned memberships (user deleted) remain.
    user_ids = {u["_id"] for u in db.users.find({}, {"_id": 1})}
    orphans = sum(1 for m in db.memberships.find({}, {"user_id": 1}) if m["user_id"] not in user_ids)
    assert orphans == 0, f"{orphans} orphaned membership(s) remain"

    mem = db.memberships.count_documents({"org_id": org_oid})
    print(f"  integrity: events/badges/redemptions carry org_id; denormalization consistent; "
          f"all admins/assistants covered; 0 orphans; memberships={mem}")


def rollback():
    print(f"\n=== Phase 1 migration (ROLLBACK) — DB='{mongo.db.name}' FLASK_ENV='{FLASK_ENV}' ===")
    _counts("before")

    org = org_model.find_by_slug(ORG_SLUG)
    org_oid = org["_id"] if org else None

    for coll, fields in (
        ("events", {"org_id": ""}),
        ("badges", {"org_id": ""}),
        ("redemptions", {"org_id": ""}),
        ("audit_log", {"org_id": "", "event_id": ""}),
        ("users", {"platform_role": ""}),
    ):
        r = mongo.db[coll].update_many({}, {"$unset": fields})
        print(f"  {coll}: unset {list(fields)} on {r.modified_count}")

    if org_oid is not None:
        dm = mongo.db.memberships.delete_many({"org_id": org_oid})
        print(f"  memberships: deleted {dm.deleted_count} for org #1")
        mongo.db.organizations.delete_one({"_id": org_oid})
        print(f"  organizations: deleted org #1 ({org_oid})")
    else:
        print("  org #1 not found; nothing to delete")

    _counts("after")
    print("=== ROLLBACK complete ===\n")


def run():
    create_app()  # connects to Atlas / DB, fails fast if unreachable, ensures indexes
    if "--rollback" in sys.argv:
        rollback()
    else:
        forward()


if __name__ == "__main__":
    run()
