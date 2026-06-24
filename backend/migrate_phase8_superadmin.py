"""Phase 8 migration — DEV-ONLY promotion of legacy admins to super_admin.

The /admin/* routes are now locked to platform super_admin. On the dev database the
admin accounts are disposable test accounts, so (matching the Phase 1 dev rule) this
promotes any remaining `role=="admin"` user that isn't already super_admin to
`platform_role=="super_admin"`, so no one is locked out and the existing verify suite
keeps passing.

GUARDED: refuses to run when FLASK_ENV=production. In a real deployment the platform
owner must be named explicitly — never auto-promote. Reversible: forward tags the users
it promotes with `_p8_promoted` so rollback only undoes those.

Usage:
    python migrate_phase8_superadmin.py            # promote remaining admins (dev only)
    python migrate_phase8_superadmin.py --rollback # undo only the promotions this made

Safe to run repeatedly.
"""

import os
import sys

from app import create_app, mongo

FLASK_ENV = os.getenv("FLASK_ENV", "development")


def _report():
    admins = mongo.db.users.count_documents({"role": "admin"})
    supers = mongo.db.users.count_documents({"platform_role": "super_admin"})
    pending = mongo.db.users.count_documents({"role": "admin", "platform_role": {"$ne": "super_admin"}})
    print(f"  users: role=admin={admins}, super_admin={supers}, admins NOT super={pending}")
    return pending


def forward():
    print(f"\n=== Phase 8 super-admin (FORWARD) — DB='{mongo.db.name}' FLASK_ENV='{FLASK_ENV}' ===")
    if FLASK_ENV == "production":
        raise SystemExit("REFUSING: never auto-promote super admins in production. Name the owner explicitly.")
    _report()
    res = mongo.db.users.update_many(
        {"role": "admin", "platform_role": {"$ne": "super_admin"}},
        {"$set": {"platform_role": "super_admin", "_p8_promoted": True}},
    )
    print(f"  promoted {res.modified_count} legacy admin(s) to super_admin")
    pending = _report()
    assert pending == 0, "every legacy admin must be super_admin after promotion"
    print("=== FORWARD complete; no legacy admin is locked out of /admin/* ===\n")


def rollback():
    print(f"\n=== Phase 8 super-admin (ROLLBACK) — DB='{mongo.db.name}' FLASK_ENV='{FLASK_ENV}' ===")
    _report()
    res = mongo.db.users.update_many(
        {"_p8_promoted": True},
        {"$unset": {"platform_role": "", "_p8_promoted": ""}},
    )
    print(f"  reverted {res.modified_count} promotion(s)")
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
