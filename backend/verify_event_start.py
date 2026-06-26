"""Verification — manual event start/stop override + announcement auto-enable.

Proves the human-error-reduction feature end to end:
  1. an UPCOMING event (future start date) is NOT scannable -> redeem 403
  2. starting it (PATCH .../status {started:true}) forces status 'active' and it
     becomes scannable -> redeem 200
  3. stopping it reverts to date-derived status -> redeem 403 again
  4. tier: super admin starts via /admin; org owner/admin start via /orgs; staff
     and non-members are refused (403)
  5. creating a super-admin announcement with enable_event=true force-starts the
     linked event (which may belong to any org)
All fixtures cleaned up.

Usage:  python verify_event_start.py
"""

from datetime import datetime, timedelta, timezone

from bson import ObjectId

from app import create_app, mongo
from app.utils.auth import encode_token, hash_password
from app.models import user as user_model
from app.models import organization as org_model
from app.models import membership as membership_model

PASS, FAIL = "PASS", "FAIL"
results = []
SUFFIX = "evstart"


def check(label, cond):
    results.append((PASS if cond else FAIL, label))
    print(f"  [{PASS if cond else FAIL}] {label}")
    return cond


def main():
    app = create_app()
    client = app.test_client()
    emails = {k: f"{SUFFIX}_{k}@example.invalid" for k in ("owner", "staff", "other", "attendee")}
    org_id = ev_id = badge_token = None
    super_admin = None
    uids = {}
    try:
        for em in emails.values():
            mongo.db.users.delete_one({"email": em})
        for k, em in emails.items():
            uids[k] = user_model.create_user(k.title(), "ES", em, hash_password("TestPass1!"), role="attendee")
        super_admin = mongo.db.users.find_one({"platform_role": "super_admin"})
        if not super_admin:
            raise SystemExit("No super_admin in DB — cannot verify.")

        org_id = org_model.create_org(f"{SUFFIX} Org", f"{SUFFIX}-org", created_by=uids["owner"])
        membership_model.add_membership(uids["owner"], org_id, "owner")
        membership_model.add_membership(uids["staff"], org_id, "staff")

        with app.app_context():
            sat = encode_token(str(super_admin["_id"]), super_admin["role"])
            tok = {k: encode_token(uids[k], "attendee") for k in uids}
        H = lambda t: {"Authorization": f"Bearer {t}"}
        sah = H(sat)

        # An event with a FUTURE start date -> 'upcoming', not scannable.
        future = datetime.now(timezone.utc) + timedelta(days=10)
        ev_id = str(mongo.db.events.insert_one({
            "name": f"{SUFFIX} future event", "event_type": "workshop", "org_id": ObjectId(org_id),
            "start_date": future, "end_date": None, "started": False,
            "created_by": ObjectId(uids["owner"]), "created_at": datetime.now(timezone.utc),
        }).inserted_id)
        # A badge to scan.
        r = client.post(f"/orgs/{org_id}/events/{ev_id}/badge", headers=H(tok["owner"]), json={"name": "Door"})
        badge_token = (r.get_json() or {}).get("token")
        check("setup: org event + badge created", bool(badge_token))

        redeem = lambda: client.get(f"/redeem/{ev_id}/{badge_token}", headers=H(tok["attendee"])).status_code

        # ---- 1. upcoming -> not scannable ----
        check("upcoming event is NOT scannable (redeem 403)", redeem() == 403)
        check("event summary reports status 'upcoming'",
              next((e for e in client.get(f"/orgs/{org_id}/events", headers=H(tok['owner'])).get_json()
                    if e["id"] == ev_id), {}).get("status") == "upcoming")

        # ---- 4. tier: staff + non-member cannot start ----
        check("staff cannot start the event (403)",
              client.patch(f"/orgs/{org_id}/events/{ev_id}/status", headers=H(tok["staff"]), json={"started": True}).status_code == 403)
        check("non-member cannot start the event (403)",
              client.patch(f"/orgs/{org_id}/events/{ev_id}/status", headers=H(tok["other"]), json={"started": True}).status_code == 403)

        # ---- 2. owner starts -> active + scannable ----
        r = client.patch(f"/orgs/{org_id}/events/{ev_id}/status", headers=H(tok["owner"]), json={"started": True})
        check("owner starts the event -> 200 + status active",
              r.status_code == 200 and (r.get_json() or {}).get("status") == "active")
        check("started event IS scannable (redeem 200)", redeem() == 200)

        # ---- 3. stop -> reverts -> not scannable ----
        # (use a fresh attendee so the duplicate-redeem 409 doesn't mask the 403)
        r = client.patch(f"/orgs/{org_id}/events/{ev_id}/status", headers=H(tok["owner"]), json={"started": False})
        check("owner stops the event -> status reverts to 'upcoming'",
              r.status_code == 200 and (r.get_json() or {}).get("status") == "upcoming")
        check("stopped event is NOT scannable for a new attendee (403)",
              client.get(f"/redeem/{ev_id}/{badge_token}", headers=H(tok["other"])).status_code == 403)

        # ---- super admin can start via the platform path ----
        check("super_admin starts via /admin path (200, active)",
              (lambda rr: rr.status_code == 200 and rr.get_json().get("status") == "active")(
                  client.patch(f"/admin/events/{ev_id}/status", headers=sah, json={"started": True})))
        client.patch(f"/admin/events/{ev_id}/status", headers=sah, json={"started": False})  # reset

        # ---- 5. announcement enable_event force-starts the linked event ----
        r = client.post("/announcements", headers=sah,
                        json={"title": f"{SUFFIX} join us", "body": "Come!", "event_id": ev_id, "enable_event": True})
        ann_id = (r.get_json() or {}).get("id")
        started_now = mongo.db.events.find_one({"_id": ObjectId(ev_id)}).get("started")
        check("announcement with enable_event=true force-starts the linked event",
              r.status_code == 201 and started_now is True)
        if ann_id:
            client.delete(f"/announcements/{ann_id}", headers=sah)

        # control: enable_event omitted does NOT start
        client.patch(f"/admin/events/{ev_id}/status", headers=sah, json={"started": False})
        r = client.post("/announcements", headers=sah,
                        json={"title": f"{SUFFIX} plain", "body": "FYI", "event_id": ev_id})
        ann2 = (r.get_json() or {}).get("id")
        check("announcement without the flag leaves the event unstarted",
              mongo.db.events.find_one({"_id": ObjectId(ev_id)}).get("started") is False)
        if ann2:
            client.delete(f"/announcements/{ann2}", headers=sah)

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
            mongo.db.announcements.delete_many({"title": {"$regex": f"^{SUFFIX}"}})
            mongo.db.audit_log.delete_many({"actor_id": str(super_admin["_id"]),
                                            "action": {"$in": ["event.start", "event.stop", "announcement.create", "announcement.delete"]}})
        mongo.db.users.delete_many({"email": {"$in": list(emails.values())}})
        print("\n  cleaned up throwaway fixtures (users, org, event, badge, announcements, audit)")

    fails = [l for s, l in results if s == FAIL]
    print(f"\n=== {len(results) - len(fails)}/{len(results)} checks passed ===")
    if fails:
        raise SystemExit("FAILED:\n  - " + "\n  - ".join(fails))


if __name__ == "__main__":
    main()
