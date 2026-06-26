"""GO-LIVE: designate the exact production super admins on the target DB.

Idempotent + reversible-in-effect. Dry-run by default; pass --apply to write.

End state guaranteed: ONLY the emails in PROD_SUPER_ADMINS hold platform_role
"super_admin"; every other account is demoted to a normal attendee-tier user.
This is the EXPLICIT designation the deploy plan requires (never the dev
auto-promotion, which is already removed).

Usage:
    python designate_prod_superadmins.py            # dry-run (shows the plan, writes nothing)
    python designate_prod_superadmins.py --apply     # perform the designation
"""
import sys

from app import create_app, mongo
from app.models import user as user_model

PROD_SUPER_ADMINS = ["santimenac23@gmail.com", "pablofori09@gmail.com"]

APPLY = "--apply" in sys.argv


def main():
    create_app()
    db = mongo.db
    print(f"=== TARGET DB: {db.name} ===   mode: {'APPLY (writing)' if APPLY else 'DRY-RUN (no writes)'}\n")

    allow = {e.strip().lower() for e in PROD_SUPER_ADMINS}

    current = list(db.users.find({"platform_role": "super_admin"}, {"email": 1}))
    print("current super admins:")
    for u in current:
        print("  -", u.get("email"))

    # Resolve the intended owners; refuse to invent accounts.
    intended = {}
    for email in allow:
        u = user_model.find_by_email(email)
        if not u:
            print(f"\n!! intended owner not found: {email} — they must register first. Aborting.")
            raise SystemExit(1)
        intended[email] = u["_id"]

    to_promote = [e for e in allow if not any(str(c["_id"]) == str(intended[e]) and c.get("email","").lower()==e for c in current)]
    to_demote = [u for u in current if (u.get("email") or "").lower() not in allow]

    print("\nplan:")
    print("  promote/confirm:", sorted(allow))
    print("  demote:", [u.get("email") for u in to_demote] or "(none)")

    if not APPLY:
        print("\nDRY-RUN — no changes written. Re-run with --apply to perform.")
        return

    for email, uid in intended.items():
        user_model.set_platform_role(uid, "super_admin")
    for u in to_demote:
        user_model.set_platform_role(u["_id"], None)

    after = sorted((u.get("email") or "") for u in db.users.find({"platform_role": "super_admin"}, {"email": 1}))
    print("\nafter — super admins:", after)
    ok = set(a.lower() for a in after) == allow
    print("RESULT:", "OK — exactly the intended owners hold super_admin" if ok else "FAIL — unexpected set")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
