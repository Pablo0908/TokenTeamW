"""Verification — per-(user, org) bans (Phase 6 / Phase D).

Proves an org can bar an attendee from ITS events only, enforced in the scan path,
without ever touching the platform account:
  1. staff and non-members cannot ban (403); owner/admin can
  2. a banned attendee can no longer scan in that org (403)
  3. the same attendee can STILL scan in a different org (ban is org-scoped)
  4. the ban never disables the account (user.disabled stays false)
  5. the people list flags the banned attendee
  6. unbanning restores scanning
  7. super_admin can ban (passes org_role_required)
All fixtures cleaned up.

Usage:  python verify_phase6.py
"""

from bson import ObjectId

from app import create_app, mongo
from app.utils.auth import encode_token, hash_password
from app.models import user as user_model
from app.models import organization as org_model
from app.models import membership as membership_model

PASS, FAIL = "PASS", "FAIL"
results = []
SUFFIX = "banverify"


def check(label, cond):
    results.append((PASS if cond else FAIL, label))
    print(f"  [{PASS if cond else FAIL}] {label}")
    return cond


def main():
    app = create_app()
    client = app.test_client()
    emails = {k: f"{SUFFIX}_{k}@example.invalid" for k in ("owner", "admin", "staff", "attendee", "otherowner")}
    org_a = org_b = ev_a = ev_b = None
    super_admin = None
    uids = {}
    try:
        for em in emails.values():
            mongo.db.users.delete_one({"email": em})
        for k, em in emails.items():
            uids[k] = user_model.create_user(k.title(), "BN", em, hash_password("TestPass1!"), role="attendee")
        super_admin = mongo.db.users.find_one({"platform_role": "super_admin"})
        if not super_admin:
            raise SystemExit("No super_admin in DB — cannot verify.")

        org_a = org_model.create_org(f"{SUFFIX} A", f"{SUFFIX}-a", created_by=uids["owner"])
        membership_model.add_membership(uids["owner"], org_a, "owner")
        membership_model.add_membership(uids["admin"], org_a, "admin")
        membership_model.add_membership(uids["staff"], org_a, "staff")
        org_b = org_model.create_org(f"{SUFFIX} B", f"{SUFFIX}-b", created_by=uids["otherowner"])
        membership_model.add_membership(uids["otherowner"], org_b, "owner")

        with app.app_context():
            sat = encode_token(str(super_admin["_id"]), super_admin["role"])
            tok = {k: encode_token(uids[k], "attendee") for k in uids}
        H = lambda t: {"Authorization": f"Bearer {t}"}

        def make_badge(org, ev, name):
            return (client.post(f"/orgs/{org}/events/{ev}/badge", headers=H(tok["owner" if org == org_a else "otherowner"]),
                                json={"name": name}).get_json() or {}).get("token")

        ev_a = (client.post(f"/orgs/{org_a}/event", headers=H(tok["owner"]), json={"name": "A ev"}).get_json() or {}).get("id")
        ev_b = (client.post(f"/orgs/{org_b}/event", headers=H(tok["otherowner"]), json={"name": "B ev"}).get_json() or {}).get("id")
        # Events start closed — open both so scans succeed.
        client.patch(f"/orgs/{org_a}/events/{ev_a}/status", headers=H(tok["owner"]), json={"started": True})
        client.patch(f"/orgs/{org_b}/events/{ev_b}/status", headers=H(tok["otherowner"]), json={"started": True})
        a1, a2, a3 = (make_badge(org_a, ev_a, f"A{i}") for i in (1, 2, 3))
        b1, b2 = (make_badge(org_b, ev_b, f"B{i}") for i in (1, 2))

        att = H(tok["attendee"])
        check("setup: attendee scans in org A (200) and org B (200) before any ban",
              client.get(f"/redeem/{ev_a}/{a1}", headers=att).status_code == 200
              and client.get(f"/redeem/{ev_b}/{b1}", headers=att).status_code == 200)

        # ---- 1. who may ban ----
        check("staff cannot ban (403)",
              client.post(f"/orgs/{org_a}/participants/{uids['attendee']}/ban", headers=H(tok["staff"])).status_code == 403)
        check("non-member cannot ban (403)",
              client.post(f"/orgs/{org_a}/participants/{uids['attendee']}/ban", headers=H(tok["otherowner"])).status_code == 403)
        check("admin bans the attendee (200)",
              client.post(f"/orgs/{org_a}/participants/{uids['attendee']}/ban", headers=H(tok["admin"]),
                          json={"reason": "spam"}).status_code == 200)

        # ---- 2 + 3. enforcement is org-scoped ----
        check("banned attendee cannot scan in org A (403)",
              client.get(f"/redeem/{ev_a}/{a2}", headers=att).status_code == 403)
        check("banned attendee CAN still scan in org B (200, org-scoped)",
              client.get(f"/redeem/{ev_b}/{b2}", headers=att).status_code == 200)

        # ---- 4. account untouched ----
        adoc = user_model.find_by_id(uids["attendee"])
        check("ban did NOT disable the platform account", not adoc.get("disabled", False))

        # ---- 5. people list flags the ban ----
        plist = (client.get(f"/orgs/{org_a}/participants", headers=H(tok["owner"])).get_json() or {}).get("participants", [])
        row = next((p for p in plist if p["id"] == uids["attendee"]), None)
        check("people list flags the banned attendee", bool(row) and row.get("banned") is True)

        # ---- 6. unban restores scanning ----
        check("owner unbans the attendee (200)",
              client.delete(f"/orgs/{org_a}/participants/{uids['attendee']}/ban", headers=H(tok["owner"])).status_code == 200)
        check("unbanned attendee can scan in org A again (200)",
              client.get(f"/redeem/{ev_a}/{a3}", headers=att).status_code == 200)

        # ---- 7. super_admin can ban ----
        check("super_admin can ban (passes org_role_required) (200)",
              client.post(f"/orgs/{org_a}/participants/{uids['attendee']}/ban", headers=H(sat)).status_code == 200)

    finally:
        for e in (ev_a, ev_b):
            if e:
                mongo.db.badges.delete_many({"event_id": ObjectId(e)})
                mongo.db.redemptions.delete_many({"event_id": ObjectId(e)})
                mongo.db.events.delete_one({"_id": ObjectId(e)})
        for o in (org_a, org_b):
            if o:
                mongo.db.bans.delete_many({"org_id": ObjectId(o)})
                mongo.db.audit_log.delete_many({"org_id": o})
                mongo.db.memberships.delete_many({"org_id": ObjectId(o)})
                mongo.db.organizations.delete_one({"_id": ObjectId(o)})
        if uids:
            mongo.db.audit_log.delete_many({"actor_id": {"$in": list(uids.values())}})
        if super_admin:
            mongo.db.audit_log.delete_many({"actor_id": str(super_admin["_id"]), "action": "attendee.ban"})
        mongo.db.users.delete_many({"email": {"$in": list(emails.values())}})
        print("\n  cleaned up throwaway fixtures (users, orgs, memberships, events, badges, bans, audit)")

    fails = [l for s, l in results if s == FAIL]
    print(f"\n=== {len(results) - len(fails)}/{len(results)} checks passed ===")
    if fails:
        raise SystemExit("FAILED:\n  - " + "\n  - ".join(fails))


if __name__ == "__main__":
    main()
