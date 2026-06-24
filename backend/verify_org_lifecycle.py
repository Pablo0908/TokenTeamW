"""Verification — org lifecycle (Phase C): suspend / reactivate (super-admin).

Proves:
  1. only a super_admin can list orgs / change org status (org owner -> 403)
  2. super_admin lists orgs (200) and sees the throwaway org
  3. an active org is scannable
  4. suspending the org -> 200; its scans are then refused (403) and event creation
     is blocked (403), WITHOUT touching member/attendee accounts
  5. reactivating -> 200; scanning works again
All fixtures cleaned up.

Usage:  python verify_org_lifecycle.py
"""

from bson import ObjectId

from app import create_app, mongo
from app.utils.auth import encode_token, hash_password
from app.models import user as user_model
from app.models import organization as org_model
from app.models import membership as membership_model

PASS, FAIL = "PASS", "FAIL"
results = []
SUFFIX = "lifecycle"


def check(label, cond):
    results.append((PASS if cond else FAIL, label))
    print(f"  [{PASS if cond else FAIL}] {label}")
    return cond


def main():
    app = create_app()
    client = app.test_client()
    emails = {k: f"{SUFFIX}_{k}@example.invalid" for k in ("owner", "attendee")}
    org_id = ev_id = None
    super_admin = None
    uids = {}
    try:
        for em in emails.values():
            mongo.db.users.delete_one({"email": em})
        for k, em in emails.items():
            uids[k] = user_model.create_user(k.title(), "LC", em, hash_password("TestPass1!"), role="attendee")
        super_admin = mongo.db.users.find_one({"platform_role": "super_admin"})
        if not super_admin:
            raise SystemExit("No super_admin in DB — cannot verify.")

        org_id = org_model.create_org(f"{SUFFIX} Org", f"{SUFFIX}-org", created_by=uids["owner"])
        membership_model.add_membership(uids["owner"], org_id, "owner")

        with app.app_context():
            sat = encode_token(str(super_admin["_id"]), super_admin["role"])
            tok = {k: encode_token(uids[k], "attendee") for k in uids}
        H = lambda t: {"Authorization": f"Bearer {t}"}

        # event + two badges (one to scan before suspend, one after)
        ev_id = (client.post(f"/orgs/{org_id}/event", headers=H(tok["owner"]),
                             json={"name": f"{SUFFIX} ev"}).get_json() or {}).get("id")
        b1 = (client.post(f"/orgs/{org_id}/events/{ev_id}/badge", headers=H(tok["owner"]),
                          json={"name": "B1"}).get_json() or {}).get("token")
        b2 = (client.post(f"/orgs/{org_id}/events/{ev_id}/badge", headers=H(tok["owner"]),
                          json={"name": "B2"}).get_json() or {}).get("token")
        # Events start closed — open it so an active org's scans succeed.
        client.patch(f"/orgs/{org_id}/events/{ev_id}/status", headers=H(tok["owner"]), json={"started": True})

        # ---- 1. only super_admin governs orgs ----
        check("org owner cannot list /admin/orgs (403)",
              client.get("/admin/orgs", headers=H(tok["owner"])).status_code == 403)
        check("org owner cannot change org status (403)",
              client.patch(f"/admin/orgs/{org_id}/status", headers=H(tok["owner"]),
                           json={"status": "suspended"}).status_code == 403)

        # ---- 2. super_admin lists orgs ----
        r = client.get("/admin/orgs", headers=H(sat))
        body = r.get_json() or {}
        check("super_admin lists orgs (200) and sees the throwaway org",
              r.status_code == 200 and any(o["id"] == org_id for o in body.get("orgs", [])))

        # ---- 3. active org is scannable ----
        check("active org: scan succeeds (200)",
              client.get(f"/redeem/{ev_id}/{b1}", headers=H(tok["attendee"])).status_code == 200)

        # ---- 4. suspend freezes scans + event creation ----
        r = client.patch(f"/admin/orgs/{org_id}/status", headers=H(sat), json={"status": "suspended"})
        check("super_admin suspends the org (200, suspended)",
              r.status_code == 200 and (r.get_json() or {}).get("status") == "suspended")
        check("suspended org: scan refused (403)",
              client.get(f"/redeem/{ev_id}/{b2}", headers=H(tok["attendee"])).status_code == 403)
        check("suspended org: event creation blocked (403)",
              client.post(f"/orgs/{org_id}/event", headers=H(tok["owner"]),
                          json={"name": "blocked"}).status_code == 403)
        owner_doc = user_model.find_by_id(uids["owner"])
        attendee_doc = user_model.find_by_id(uids["attendee"])
        check("suspend did NOT disable member/attendee accounts",
              not owner_doc.get("disabled", False) and not attendee_doc.get("disabled", False))

        # ---- 5. reactivate restores scanning ----
        r = client.patch(f"/admin/orgs/{org_id}/status", headers=H(sat), json={"status": "active"})
        check("super_admin reactivates the org (200, active)",
              r.status_code == 200 and (r.get_json() or {}).get("status") == "active")
        check("reactivated org: scan succeeds again (200)",
              client.get(f"/redeem/{ev_id}/{b2}", headers=H(tok["attendee"])).status_code == 200)

    finally:
        if ev_id:
            mongo.db.badges.delete_many({"event_id": ObjectId(ev_id)})
            mongo.db.redemptions.delete_many({"event_id": ObjectId(ev_id)})
            mongo.db.events.delete_one({"_id": ObjectId(ev_id)})
        if org_id:
            mongo.db.audit_log.delete_many({"org_id": org_id})
            mongo.db.memberships.delete_many({"org_id": ObjectId(org_id)})
            mongo.db.organizations.delete_one({"_id": ObjectId(org_id)})
        if uids:
            mongo.db.audit_log.delete_many({"actor_id": {"$in": list(uids.values())}})
        if super_admin:
            mongo.db.audit_log.delete_many({"actor_id": str(super_admin["_id"]),
                                            "action": {"$in": ["org.suspend", "org.reactivate"]}})
        mongo.db.users.delete_many({"email": {"$in": list(emails.values())}})
        print("\n  cleaned up throwaway fixtures (users, org, membership, event, badges, audit)")

    fails = [l for s, l in results if s == FAIL]
    print(f"\n=== {len(results) - len(fails)}/{len(results)} checks passed ===")
    if fails:
        raise SystemExit("FAILED:\n  - " + "\n  - ".join(fails))


if __name__ == "__main__":
    main()
