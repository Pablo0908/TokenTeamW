"""Phase 2 verification — tiered audit access + interaction capture.

Drives the real HTTP surface with locally-minted JWTs (no OTP/email path) and proves:
  1. app still works: attendee feed + a scan -> badge -> completion flow
  2. a scan writes a badge.redeem audit entry carrying org_id/event_id/actor identity
  3. a login writes an auth.login audit entry
  4. tier-scoped read: a super_admin sees cross-org entries; an org-admin who is NOT
     a super_admin sees ONLY their org's entries; staff and a plain attendee are 403

All fixtures (orgs, users, memberships, event/badge/redemptions, audit rows) are
created throwaway and cleaned up at the end.

Usage:  python verify_phase2.py
"""

from bson import ObjectId

from app import create_app, mongo
from app.utils.auth import encode_token, hash_password
from app.models import user as user_model
from app.models import organization as org_model
from app.models import membership as membership_model
from app.models import audit as audit_model

PASS, FAIL = "PASS", "FAIL"
results = []
SUFFIX = "p2verify"  # marks throwaway docs for cleanup


def check(label, cond):
    results.append((PASS if cond else FAIL, label))
    print(f"  [{PASS if cond else FAIL}] {label}")
    return cond


def main():
    app = create_app()
    client = app.test_client()
    created_event_id = None
    emails = {
        "attendee": f"{SUFFIX}_attendee@example.invalid",
        "orgb_admin": f"{SUFFIX}_orgb_admin@example.invalid",
        "orgb_staff": f"{SUFFIX}_orgb_staff@example.invalid",
    }
    org_b_id = None
    try:
        # ---- fixtures ----
        for em in emails.values():
            mongo.db.users.delete_one({"email": em})
        mongo.db.organizations.delete_many({"slug": f"{SUFFIX}-org-b"})

        att_id = user_model.create_user("Ver", "Attendee", emails["attendee"], hash_password("TestPass1!"), role="attendee")
        attendee = user_model.find_by_id(att_id)
        super_admin = mongo.db.users.find_one({"platform_role": "super_admin"})
        assert super_admin, "need a super_admin in the DB"

        org_b_id = ObjectId(org_model.create_org("Verify Org B", f"{SUFFIX}-org-b", description=""))
        orgb_admin_id = user_model.create_user("OrgB", "Admin", emails["orgb_admin"], hash_password("TestPass1!"), role="attendee")
        orgb_staff_id = user_model.create_user("OrgB", "Staff", emails["orgb_staff"], hash_password("TestPass1!"), role="attendee")
        membership_model.add_membership(orgb_admin_id, org_b_id, "admin")
        membership_model.add_membership(orgb_staff_id, org_b_id, "staff")
        # An audit entry that belongs to org B only.
        audit_model.log(orgb_admin_id, "test.verify_orgb", "org B marker", org_id=org_b_id)

        with app.app_context():
            attendee_tok = encode_token(att_id, "attendee")
            superadmin_tok = encode_token(str(super_admin["_id"]), super_admin["role"])
            orgb_admin_tok = encode_token(orgb_admin_id, "attendee")
            orgb_staff_tok = encode_token(orgb_staff_id, "attendee")
        ah = {"Authorization": f"Bearer {attendee_tok}"}
        sah = {"Authorization": f"Bearer {superadmin_tok}"}
        bah = {"Authorization": f"Bearer {orgb_admin_tok}"}
        bsh = {"Authorization": f"Bearer {orgb_staff_tok}"}

        # ---- 1. app still works: feed + scan -> completion ----
        r = client.get("/events/", headers=ah)
        check("GET /events/ -> 200 (feed works)", r.status_code == 200 and isinstance(r.get_json(), list))

        r = client.post("/admin/event", headers=sah, json={"name": "P2 Verify Event", "prize": "P2 Prize"})
        created_event_id = r.get_json().get("id")
        check("admin create event -> 201", r.status_code == 201 and created_event_id)
        r = client.post(f"/admin/events/{created_event_id}/badge", headers=sah, json={"name": "P2 Badge"})
        token = r.get_json().get("token")
        check("admin create badge -> 201", r.status_code == 201 and token)

        r = client.get(f"/redeem/{created_event_id}/{token}", headers=ah)
        redeem = r.get_json()
        check("scan -> 200, completed, prize", r.status_code == 200 and redeem.get("event_completed") and redeem.get("prize") == "P2 Prize")

        # ---- 2. the scan wrote a dimensioned audit entry ----
        ev_org = mongo.db.events.find_one({"_id": ObjectId(created_event_id)}).get("org_id")
        scan_entry = mongo.db.audit_log.find_one({"action": "badge.redeem", "event_id": created_event_id})
        check("scan logged badge.redeem with org_id + event_id",
              bool(scan_entry) and scan_entry.get("org_id") == str(ev_org) and scan_entry.get("event_id") == created_event_id)
        check("scan entry carries actor identity (attendee)",
              bool(scan_entry) and scan_entry.get("actor_email") == emails["attendee"] and scan_entry.get("actor_role") == "attendee")

        # ---- 3. a login writes auth.login ----
        r = client.post("/auth/login", json={"email": emails["attendee"], "password": "TestPass1!"})
        check("login -> 200 (password-only, no 2FA)", r.status_code == 200 and bool(r.get_json().get("token")))
        login_entry = mongo.db.audit_log.find_one({"action": "auth.login", "actor_id": att_id})
        check("login logged auth.login with actor identity",
              bool(login_entry) and login_entry.get("actor_email") == emails["attendee"])

        # ---- 4. tier-scoped read ----
        r = client.get("/admin/audit", headers=sah)
        sa_entries = r.get_json().get("entries", [])
        sa_orgs = {e.get("org_id") for e in sa_entries}
        check("super_admin: /admin/audit 200 and sees MULTIPLE orgs",
              r.status_code == 200 and str(org_b_id) in sa_orgs and any(o not in (None, str(org_b_id)) for o in sa_orgs))

        r = client.get("/admin/audit", headers=bah)
        b_entries = r.get_json().get("entries", [])
        check("org-admin (not super): 200 and sees ONLY its org",
              r.status_code == 200 and len(b_entries) > 0 and all(e.get("org_id") == str(org_b_id) for e in b_entries))

        r = client.get("/admin/audit", headers=bsh)
        check("org STAFF: /admin/audit -> 403 (audit is admin-tier)", r.status_code == 403)
        r = client.get("/admin/audit", headers=ah)
        check("plain attendee: /admin/audit -> 403", r.status_code == 403)

    finally:
        if created_event_id:
            oid = ObjectId(created_event_id)
            mongo.db.redemptions.delete_many({"event_id": oid})
            mongo.db.badges.delete_many({"event_id": oid})
            mongo.db.events.delete_one({"_id": oid})
            mongo.db.audit_log.delete_many({"event_id": created_event_id})
        ids = [str(i) for i in [
            *[u["_id"] for u in mongo.db.users.find({"email": {"$in": list(emails.values())}}, {"_id": 1})]
        ]]
        mongo.db.audit_log.delete_many({"actor_id": {"$in": ids}})
        if org_b_id is not None:
            mongo.db.audit_log.delete_many({"org_id": str(org_b_id)})
            mongo.db.memberships.delete_many({"org_id": org_b_id})
            mongo.db.organizations.delete_one({"_id": org_b_id})
        mongo.db.users.delete_many({"email": {"$in": list(emails.values())}})
        print("\n  cleaned up throwaway fixtures (users, org B, memberships, event, audit rows)")

    fails = [l for s, l in results if s == FAIL]
    print(f"\n=== {len(results) - len(fails)}/{len(results)} checks passed ===")
    if fails:
        raise SystemExit("FAILED:\n  - " + "\n  - ".join(fails))


if __name__ == "__main__":
    main()
