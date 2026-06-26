"""Migration — retire the legacy global `users.role` ("admin"/"assistant").

The app no longer has a global admin tier: regular admin is org-scoped (a membership role)
and the only platform tier is `platform_role == "super_admin"`. The legacy `users.role`
string is now purely cosmetic and contradicts that model (a user could read as "admin" with
no panel and no powers). This forces every account to `role == "attendee"`.

`platform_role` is a SEPARATE field and is left untouched — super admins stay super admins.
Org admins keep their `memberships` rows and lose nothing.

Reversible: forward stashes the previous role in `_legacy_role` (only for non-attendee
users); rollback restores it. Idempotent, counted. Safe to run repeatedly.

Usage:
    python migrate_roles_cleanup.py            # retire global admin/assistant -> attendee
    python migrate_roles_cleanup.py --rollback # restore the previous role values
"""

import sys

from app import create_app, mongo


def _report():
    non_attendee = mongo.db.users.count_documents({"role": {"$ne": "attendee"}})
    supers = mongo.db.users.count_documents({"platform_role": "super_admin"})
    print(f"  users: role!='attendee'={non_attendee}, super_admin={supers}")
    return non_attendee, supers


def forward():
    print(f"\n=== roles cleanup (FORWARD) — DB='{mongo.db.name}' ===")
    _, supers_before = _report()
    # Stash the old role for reversibility, then flatten to attendee.
    stashed = mongo.db.users.update_many(
        {"role": {"$ne": "attendee"}, "_legacy_role": {"$exists": False}},
        [{"$set": {"_legacy_role": "$role"}}],
    )
    res = mongo.db.users.update_many(
        {"role": {"$ne": "attendee"}},
        {"$set": {"role": "attendee"}},
    )
    print(f"  stashed {stashed.modified_count} legacy role(s); flattened {res.modified_count} to attendee")
    non_attendee, supers_after = _report()
    assert non_attendee == 0, "every user must be role=attendee after cleanup"
    assert supers_after == supers_before, "super_admin count must be unchanged"
    print("=== FORWARD complete; global admin/assistant retired, super admins intact ===\n")


def rollback():
    print(f"\n=== roles cleanup (ROLLBACK) — DB='{mongo.db.name}' ===")
    _report()
    res = mongo.db.users.update_many(
        {"_legacy_role": {"$exists": True}},
        [{"$set": {"role": "$_legacy_role"}}, {"$unset": "_legacy_role"}],
    )
    print(f"  restored {res.modified_count} legacy role(s)")
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
