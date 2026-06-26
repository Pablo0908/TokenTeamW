"""Verification — permanent per-event delete (ended-only, owner/admin, cascade).

Proves:
  1. a NOT-ended event cannot be deleted (409) — deletion requires a past/ended event
  2. org staff cannot delete (403); a non-member cannot delete (403)
  3. an org owner can delete an ended event -> 200, and its badges, redemptions (scanned
     badges) and prize claims are all cascaded away with the event
  4. an org admin can delete an ended event (403/200 tier: owner+admin allowed)
  5. a super admin can delete ANY event (incl. an org event) via /admin/events/<id>
  6. every delete is audited (event.delete)
All fixtures cleaned up.

Usage:  python verify_event_delete.py
"""

from bson import ObjectId

from app import create_app, mongo
from app.utils.auth import encode_token, hash_password
from app.utils.qr import generate_badge_token
from app.models import user as user_model
from app.models import organization as org_model
from app.models import membership as membership_model
from app.models import event as event_model
from app.models import badge as badge_model
from app.models import redemption as redemption_model
from app.models import prize_claim as claim_model

PASS, FAIL = "PASS", "FAIL"
results = []
SUFFIX = "delverify"


def check(label, cond):
    results.append((PASS if cond else FAIL, label))
    print(f"  [{PASS if cond else FAIL}] {label}")
    return cond


def main():
    app = create_app()
    client = app.test_client()
    emails = {k: f"{SUFFIX}_{k}@example.invalid" for k in ("owner", "admin", "staff", "outsider", "scanner")}
    org_id = None
    uids = {}
    super_admin = None
    created_events = []

    def make_event(name, *, ended, with_data=False):
        eid = event_model.create_event(name, "", None, None, "", "Prize", uids["owner"], org_id=org_id)
        created_events.append(eid)
        if with_data:
            tok = generate_badge_token()
            bid = badge_model.create_badge(eid, "b", "", tok, "", org_id=org_id)
            redemption_model.redeem(bid, eid, uids["scanner"], org_id=org_id)
            claim_model.award(uids["scanner"], eid, org_id, awarded_by=uids["owner"])
        if ended:
            event_model.set_ended(eid, True)
        return eid

    try:
        for em in emails.values():
            mongo.db.users.delete_one({"email": em})
        for o in mongo.db.organizations.find({"slug": f"{SUFFIX}-org"}):
            for e in mongo.db.events.find({"org_id": o["_id"]}, {"_id": 1}):
                for coll in ("badges", "redemptions", "prize_claims"):
                    mongo.db[coll].delete_many({"event_id": e["_id"]})
                mongo.db.events.delete_one({"_id": e["_id"]})
            mongo.db.memberships.delete_many({"org_id": o["_id"]})
            mongo.db.organizations.delete_one({"_id": o["_id"]})

        for k, em in emails.items():
            uids[k] = user_model.create_user(k.title(), "DV", em, hash_password("TestPass1!"), role="attendee")
        super_admin = mongo.db.users.find_one({"platform_role": "super_admin"})
        if not super_admin:
            raise SystemExit("No super_admin in DB — cannot verify.")

        org_id = org_model.create_org(f"{SUFFIX} Org", f"{SUFFIX}-org", created_by=uids["owner"])
        membership_model.add_membership(uids["owner"], org_id, "owner")
        membership_model.add_membership(uids["admin"], org_id, "admin")
        membership_model.add_membership(uids["staff"], org_id, "staff")

        with app.app_context():
            tok = {k: encode_token(uids[k], "attendee", 0) for k in uids}
            sat = encode_token(str(super_admin["_id"]), super_admin.get("role", "attendee"), super_admin.get("token_version", 0))
        H = lambda t: {"Authorization": f"Bearer {t}"}
        D = lambda url, t: client.delete(url, headers=H(t))

        ev_a = make_event("DV A", ended=True, with_data=True)   # owner deletes; cascade check
        ev_b = make_event("DV B", ended=True)                   # admin deletes
        ev_c = make_event("DV C", ended=True, with_data=True)   # super_admin deletes via /admin
        ev_d = make_event("DV D", ended=False)                  # cannot delete (not ended)
        org_url = lambda eid: f"/orgs/{org_id}/events/{eid}"

        # ---- 1. not-ended -> 409 ----
        check("owner cannot delete a NOT-ended event (409)", D(org_url(ev_d), tok["owner"]).status_code == 409)

        # ---- 2. staff / non-member refused on an ended event ----
        check("org staff cannot delete (403)", D(org_url(ev_a), tok["staff"]).status_code == 403)
        check("non-member cannot delete (403)", D(org_url(ev_a), tok["outsider"]).status_code == 403)

        # confirm the failed attempts left everything intact
        check("ev A still present + data intact after refused attempts",
              event_model.find_by_id(ev_a) is not None
              and badge_model.count_for_event(ev_a) == 1
              and mongo.db.redemptions.count_documents({"event_id": ObjectId(ev_a)}) == 1
              and mongo.db.prize_claims.count_documents({"event_id": ObjectId(ev_a)}) == 1)

        # ---- 3. owner deletes ended event + cascade ----
        r = D(org_url(ev_a), tok["owner"])
        check("owner deletes ended event (200)", r.status_code == 200)
        check("event + badges + redemptions + prize claims all cascaded away",
              event_model.find_by_id(ev_a) is None
              and badge_model.count_for_event(ev_a) == 0
              and mongo.db.redemptions.count_documents({"event_id": ObjectId(ev_a)}) == 0
              and mongo.db.prize_claims.count_documents({"event_id": ObjectId(ev_a)}) == 0)

        # ---- 4. org admin can delete ----
        check("org admin can delete an ended event (200)", D(org_url(ev_b), tok["admin"]).status_code == 200)

        # ---- 5. super admin deletes ANY event via /admin/events/<id> ----
        r = D(f"/admin/events/{ev_c}", sat)
        check("super admin deletes any (org) event via /admin (200)", r.status_code == 200)
        check("super-admin delete also cascaded the org event's data",
              event_model.find_by_id(ev_c) is None and badge_model.count_for_event(ev_c) == 0)
        check("super admin gets 409 on a not-ended event too",
              D(f"/admin/events/{ev_d}", sat).status_code == 409)

        # ---- 6. audit ----
        deletes = mongo.db.audit_log.count_documents({"action": "event.delete", "event_id": {"$in": [ev_a, ev_b, ev_c]}})
        check("event.delete audited for each deletion", deletes >= 3)

    finally:
        for eid in created_events:
            for coll in ("badges", "redemptions", "prize_claims"):
                mongo.db[coll].delete_many({"event_id": ObjectId(eid)})
            mongo.db.events.delete_one({"_id": ObjectId(eid)})
        if org_id:
            mongo.db.audit_log.delete_many({"org_id": org_id})
            mongo.db.memberships.delete_many({"org_id": ObjectId(org_id)})
            mongo.db.organizations.delete_one({"_id": ObjectId(org_id)})
        if uids:
            mongo.db.audit_log.delete_many({"actor_id": {"$in": list(uids.values())}})
        mongo.db.users.delete_many({"email": {"$in": list(emails.values())}})
        print("\n  cleaned up throwaway fixtures (users, org, memberships, events, badges, redemptions, prize_claims, audit)")

    fails = [l for s, l in results if s == FAIL]
    print(f"\n=== {len(results) - len(fails)}/{len(results)} checks passed ===")
    if fails:
        raise SystemExit("FAILED:\n  - " + "\n  - ".join(fails))


if __name__ == "__main__":
    main()
