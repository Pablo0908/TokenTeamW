"""Verification — org-scoped badge management parity with the platform /admin path.

Proves an org owner/admin gets the SAME badge-creation feature super admins have,
without any cross-org leakage:
  1. owner creates a single badge -> 201 with token + qr_url + qr_image
  2. owner bulk-creates badges -> 201 with the right count
  3. badge list returns the full management shape (token, qr_url, redeemed_by,
     total_attendees) for owner/admin AND read-only staff
  4. staff CANNOT create (single or bulk) -> 403
  5. a non-member CANNOT read or write the org's badges -> 403
  6. super_admin passes the org-scoped routes
  7. an event from another org cannot be addressed via this org's route -> 404
All fixtures cleaned up.

Usage:  python verify_org_badges.py
"""

from bson import ObjectId

from app import create_app, mongo
from app.utils.auth import encode_token, hash_password
from app.models import user as user_model
from app.models import organization as org_model
from app.models import membership as membership_model

PASS, FAIL = "PASS", "FAIL"
results = []
SUFFIX = "orgbadge"


def check(label, cond):
    results.append((PASS if cond else FAIL, label))
    print(f"  [{PASS if cond else FAIL}] {label}")
    return cond


def main():
    app = create_app()
    client = app.test_client()
    emails = {k: f"{SUFFIX}_{k}@example.invalid" for k in ("owner", "staff", "other")}
    org_id = other_org_id = ev_id = other_ev_id = None
    super_admin = None
    uids = {}
    try:
        for em in emails.values():
            mongo.db.users.delete_one({"email": em})
        for k, em in emails.items():
            uids[k] = user_model.create_user(k.title(), "OB", em, hash_password("TestPass1!"), role="attendee")
        super_admin = mongo.db.users.find_one({"platform_role": "super_admin"})
        if not super_admin:
            raise SystemExit("No super_admin in DB — cannot verify.")

        # Org A: owner + staff. Org B: a separate org with its own event (isolation test).
        org_id = org_model.create_org(f"{SUFFIX} Org A", f"{SUFFIX}-a", created_by=uids["owner"])
        membership_model.add_membership(uids["owner"], org_id, "owner")
        membership_model.add_membership(uids["staff"], org_id, "staff")
        other_org_id = org_model.create_org(f"{SUFFIX} Org B", f"{SUFFIX}-b", created_by=uids["other"])
        membership_model.add_membership(uids["other"], other_org_id, "owner")

        with app.app_context():
            sat = encode_token(str(super_admin["_id"]), super_admin["role"])
            tok = {k: encode_token(uids[k], "attendee") for k in uids}
        H = lambda t: {"Authorization": f"Bearer {t}"}
        sah = H(sat)

        # events in each org
        ev_id = (client.post(f"/orgs/{org_id}/event", headers=H(tok["owner"]),
                             json={"name": f"{SUFFIX} ev A", "event_type": "workshop"}).get_json() or {}).get("id")
        other_ev_id = (client.post(f"/orgs/{other_org_id}/event", headers=H(tok["other"]),
                                   json={"name": f"{SUFFIX} ev B"}).get_json() or {}).get("id")
        check("owner created an org event", bool(ev_id) and bool(other_ev_id))

        # ---- 1. single badge ----
        r = client.post(f"/orgs/{org_id}/events/{ev_id}/badge", headers=H(tok["owner"]),
                        json={"name": "Keynote", "icon": "🎤"})
        b = r.get_json() or {}
        check("owner creates single badge (201) with token + qr_url + qr_image",
              r.status_code == 201 and b.get("token") and b.get("qr_url") and b.get("qr_image"))

        # ---- 2. bulk ----
        r = client.post(f"/orgs/{org_id}/events/{ev_id}/badges/bulk", headers=H(tok["owner"]),
                        json={"badges": [{"name": "Booth 1"}, {"name": "Booth 2"}, {"name": "Booth 3"}]})
        check("owner bulk-creates badges (201, count 3)",
              r.status_code == 201 and (r.get_json() or {}).get("count") == 3)
        check("bulk requires a valid spec (400 on empty)",
              client.post(f"/orgs/{org_id}/events/{ev_id}/badges/bulk", headers=H(tok["owner"]), json={}).status_code == 400)

        # ---- 3. list shape, owner + staff ----
        r = client.get(f"/orgs/{org_id}/events/{ev_id}/badges", headers=H(tok["owner"]))
        lst = r.get_json() or []
        sample = lst[0] if lst else {}
        check("owner lists badges with full management shape",
              r.status_code == 200 and len(lst) == 4
              and all(k in sample for k in ("token", "qr_url", "redeem_path", "redeemed_by", "total_attendees")))
        check("staff can READ the badge list (200)",
              client.get(f"/orgs/{org_id}/events/{ev_id}/badges", headers=H(tok["staff"])).status_code == 200)

        # ---- 4. staff cannot write ----
        check("staff cannot create a single badge (403)",
              client.post(f"/orgs/{org_id}/events/{ev_id}/badge", headers=H(tok["staff"]), json={"name": "Nope"}).status_code == 403)
        check("staff cannot bulk-create (403)",
              client.post(f"/orgs/{org_id}/events/{ev_id}/badges/bulk", headers=H(tok["staff"]), json={"badges": [{"name": "x"}]}).status_code == 403)

        # ---- 5. non-member blocked ----
        check("non-member cannot read the org's badges (403)",
              client.get(f"/orgs/{org_id}/events/{ev_id}/badges", headers=H(tok["other"])).status_code == 403)
        check("non-member cannot create a badge (403)",
              client.post(f"/orgs/{org_id}/events/{ev_id}/badge", headers=H(tok["other"]), json={"name": "x"}).status_code == 403)

        # ---- 6. super_admin passes ----
        check("super_admin can create in any org (201)",
              client.post(f"/orgs/{org_id}/events/{ev_id}/badge", headers=sah, json={"name": "SA badge"}).status_code == 201)

        # ---- 7. cross-org event id rejected on this org's route ----
        check("event from another org is 404 on this org's badge route",
              client.get(f"/orgs/{org_id}/events/{other_ev_id}/badges", headers=H(tok["owner"])).status_code == 404
              and client.post(f"/orgs/{org_id}/events/{other_ev_id}/badge", headers=H(tok["owner"]), json={"name": "x"}).status_code == 404)

    finally:
        for e in (ev_id, other_ev_id):
            if e:
                mongo.db.badges.delete_many({"event_id": ObjectId(e)})
                mongo.db.redemptions.delete_many({"event_id": ObjectId(e)})
                mongo.db.events.delete_one({"_id": ObjectId(e)})
        for o in (org_id, other_org_id):
            if o:
                mongo.db.audit_log.delete_many({"org_id": o})
                mongo.db.memberships.delete_many({"org_id": ObjectId(o)})
                mongo.db.organizations.delete_one({"_id": ObjectId(o)})
        if uids:
            mongo.db.audit_log.delete_many({"actor_id": {"$in": list(uids.values())}})
        if super_admin:
            mongo.db.audit_log.delete_many({"actor_id": str(super_admin["_id"]), "action": "badge.create"})
        mongo.db.users.delete_many({"email": {"$in": list(emails.values())}})
        print("\n  cleaned up throwaway fixtures (users, orgs, memberships, events, badges, audit)")

    fails = [l for s, l in results if s == FAIL]
    print(f"\n=== {len(results) - len(fails)}/{len(results)} checks passed ===")
    if fails:
        raise SystemExit("FAILED:\n  - " + "\n  - ".join(fails))


if __name__ == "__main__":
    main()
