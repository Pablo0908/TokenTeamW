"""Verification — event moderation: pause/lock (temporary) + end (terminal).

Proves the moderation lifecycle and its permission matrix:
  1. pause -> status 'locked', NOT scannable; attendee still sees the event + its
     badges; unpause restores 'active' and scannability
  2. end -> status 'past' (event.ended flag), NOT scannable; reopen restores it
  3. permission matrix:
       pause/unpause: owner, admin, super  (staff + non-member 403)
       end/reopen:    owner, super ONLY    (admin 403; staff + non-member 403)
  4. super admin can pause/end via the platform /admin path
All fixtures cleaned up.

Usage:  python verify_event_moderation.py
"""

from bson import ObjectId

from app import create_app, mongo
from app.utils.auth import encode_token, hash_password
from app.models import user as user_model
from app.models import organization as org_model
from app.models import membership as membership_model

PASS, FAIL = "PASS", "FAIL"
results = []
SUFFIX = "evmod"


def check(label, cond):
    results.append((PASS if cond else FAIL, label))
    print(f"  [{PASS if cond else FAIL}] {label}")
    return cond


def main():
    app = create_app()
    client = app.test_client()
    emails = {k: f"{SUFFIX}_{k}@example.invalid" for k in ("owner", "admin", "staff", "other", "att")}
    org_id = ev_id = token = None
    super_admin = None
    uids = {}
    try:
        for em in emails.values():
            mongo.db.users.delete_one({"email": em})
        for k, em in emails.items():
            uids[k] = user_model.create_user(k.title(), "EM", em, hash_password("TestPass1!"), role="attendee")
        super_admin = mongo.db.users.find_one({"platform_role": "super_admin"})
        if not super_admin:
            raise SystemExit("No super_admin in DB — cannot verify.")

        org_id = org_model.create_org(f"{SUFFIX} Org", f"{SUFFIX}-org", created_by=uids["owner"])
        membership_model.add_membership(uids["owner"], org_id, "owner")
        membership_model.add_membership(uids["admin"], org_id, "admin")
        membership_model.add_membership(uids["staff"], org_id, "staff")

        with app.app_context():
            sat = encode_token(str(super_admin["_id"]), super_admin["role"])
            tok = {k: encode_token(uids[k], "attendee") for k in uids}
        H = lambda t: {"Authorization": f"Bearer {t}"}
        sah = H(sat)

        # active org event (no dates -> active) + a badge
        ev_id = (client.post(f"/orgs/{org_id}/event", headers=H(tok["owner"]),
                             json={"name": f"{SUFFIX} ev"}).get_json() or {}).get("id")
        token = (client.post(f"/orgs/{org_id}/events/{ev_id}/badge", headers=H(tok["owner"]),
                             json={"name": "Door"}).get_json() or {}).get("token")
        # Events start closed (Start/Stop master switch) — start it so it's 'active'.
        client.patch(f"/orgs/{org_id}/events/{ev_id}/status", headers=H(tok["owner"]), json={"started": True})
        pause = f"/orgs/{org_id}/events/{ev_id}/pause"
        end = f"/orgs/{org_id}/events/{ev_id}/end"
        status_of = lambda: next((e for e in client.get(f"/orgs/{org_id}/events", headers=H(tok['owner'])).get_json()
                                  if e["id"] == ev_id), {})
        check("setup: active org event + badge", bool(token) and status_of().get("status") == "active")

        # ---- 3a. pause permission: staff + non-member refused ----
        check("staff cannot pause (403)", client.patch(pause, headers=H(tok["staff"]), json={"paused": True}).status_code == 403)
        check("non-member cannot pause (403)", client.patch(pause, headers=H(tok["other"]), json={"paused": True}).status_code == 403)

        # ---- 1. admin pauses -> locked, not scannable, still visible ----
        r = client.patch(pause, headers=H(tok["admin"]), json={"paused": True})
        check("admin pauses -> 200 + status 'locked'", r.status_code == 200 and r.get_json().get("status") == "locked")
        check("locked event is NOT scannable (403)",
              client.get(f"/redeem/{ev_id}/{token}", headers=H(tok["att"])).status_code == 403)
        det = client.get(f"/events/{ev_id}", headers=H(tok["att"])).get_json() or {}
        check("attendee still sees the locked event + its badges",
              det.get("status") == "locked" and isinstance(det.get("badges"), list) and len(det["badges"]) == 1)

        # unpause -> active + scannable
        r = client.patch(pause, headers=H(tok["owner"]), json={"paused": False})
        check("owner unpauses -> status 'active'", r.get_json().get("status") == "active")
        check("unlocked event is scannable again (200)",
              client.get(f"/redeem/{ev_id}/{token}", headers=H(tok["att"])).status_code == 200)

        # ---- 3b. end permission: admin/staff/non-member refused; owner allowed ----
        check("admin CANNOT end the event (403)", client.patch(end, headers=H(tok["admin"]), json={"ended": True}).status_code == 403)
        check("staff cannot end (403)", client.patch(end, headers=H(tok["staff"]), json={"ended": True}).status_code == 403)
        check("non-member cannot end (403)", client.patch(end, headers=H(tok["other"]), json={"ended": True}).status_code == 403)

        # ---- 2. owner ends -> past, ended flag, not scannable ----
        r = client.patch(end, headers=H(tok["owner"]), json={"ended": True})
        check("owner ends -> 200 + status 'past'", r.status_code == 200 and r.get_json().get("status") == "past")
        s = status_of()
        check("ended event reports status 'past' + ended flag", s.get("status") == "past" and s.get("ended") is True)
        check("ended event is NOT scannable (403)",
              client.get(f"/redeem/{ev_id}/{token}", headers=H(tok["other"])).status_code == 403)

        # reopen (owner)
        r = client.patch(end, headers=H(tok["owner"]), json={"ended": False})
        check("owner reopens -> status back to 'active'", r.get_json().get("status") == "active")

        # ---- 4. super admin via platform path ----
        check("super_admin pauses via /admin (200, locked)",
              (lambda rr: rr.status_code == 200 and rr.get_json().get("status") == "locked")(
                  client.patch(f"/admin/events/{ev_id}/pause", headers=sah, json={"paused": True})))
        check("super_admin ends via /admin (200, past)",
              (lambda rr: rr.status_code == 200 and rr.get_json().get("status") == "past")(
                  client.patch(f"/admin/events/{ev_id}/end", headers=sah, json={"ended": True})))

    finally:
        if ev_id:
            mongo.db.redemptions.delete_many({"event_id": ObjectId(ev_id)})
            mongo.db.badges.delete_many({"event_id": ObjectId(ev_id)})
            mongo.db.events.delete_one({"_id": ObjectId(ev_id)})
        if org_id:
            mongo.db.audit_log.delete_many({"org_id": org_id})
            mongo.db.memberships.delete_many({"org_id": ObjectId(org_id)})
            mongo.db.organizations.delete_one({"_id": ObjectId(org_id)})
        if uids:
            mongo.db.audit_log.delete_many({"actor_id": {"$in": list(uids.values())}})
        if super_admin:
            mongo.db.audit_log.delete_many({"actor_id": str(super_admin["_id"]),
                                            "action": {"$regex": "^event\\."}})
        mongo.db.users.delete_many({"email": {"$in": list(emails.values())}})
        print("\n  cleaned up throwaway fixtures (users, org, event, badge, audit)")

    fails = [l for s, l in results if s == FAIL]
    print(f"\n=== {len(results) - len(fails)}/{len(results)} checks passed ===")
    if fails:
        raise SystemExit("FAILED:\n  - " + "\n  - ".join(fails))


if __name__ == "__main__":
    main()
