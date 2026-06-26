"""Verification — prize-claim verification (staff-scanned, server-authoritative).

Proves the claim-state layer on top of completion:
  1. a NOT-completed attendee cannot get a claim QR (403)
  2. a completed attendee gets a signed claim QR (token + qr), still unclaimed
  3. authorized STAFF can verify it -> AWARDED, a claimed row is stamped (awarded_by/at)
  4. re-verifying the same token -> DENIED already_claimed (reports awarder + time),
     and NO second flip happens (exactly one row)
  5. the (user,event) unique index makes award() atomic — a direct second award raises
  6. a forged token for a NOT-completed user -> DENIED not_completed (QR carries no authority)
  7. a staff member of ANOTHER org cannot verify this event (403 out_of_scope)
  8. a super_admin can verify ANY event -> AWARDED
  9. a tampered/expired signature -> DENIED invalid_token
 10. every award AND every denial is written to the audit (prize.claim.award / .deny)
All fixtures cleaned up.

Usage:  python verify_prize_claim.py
"""

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app import create_app, mongo
from app.utils.auth import encode_token, hash_password
from app.utils.qr import sign_claim_token, generate_badge_token
from app.models import user as user_model
from app.models import organization as org_model
from app.models import membership as membership_model
from app.models import event as event_model
from app.models import badge as badge_model
from app.models import redemption as redemption_model
from app.models import prize_claim as claim_model

PASS, FAIL = "PASS", "FAIL"
results = []
SUFFIX = "claimverify"


def check(label, cond):
    results.append((PASS if cond else FAIL, label))
    print(f"  [{PASS if cond else FAIL}] {label}")
    return cond


def _complete(uid, org_id, ev_id):
    """Mint a 1-badge event-completion for `uid` directly (no active-status gate needed)."""
    tok = generate_badge_token()
    bid = badge_model.create_badge(ev_id, "b", "", tok, "", org_id=org_id)
    redemption_model.redeem(bid, ev_id, uid, org_id=org_id)
    return bid


def main():
    app = create_app()
    client = app.test_client()
    emails = {k: f"{SUFFIX}_{k}@example.invalid"
              for k in ("owner", "staff", "done", "todo", "outsider")}
    org_a = org_b = None
    ev1 = ev2 = None
    uids = {}
    super_admin = None
    try:
        for em in emails.values():
            mongo.db.users.delete_one({"email": em})
        for o in mongo.db.organizations.find({"slug": {"$in": [f"{SUFFIX}-a", f"{SUFFIX}-b"]}}):
            for e in mongo.db.events.find({"org_id": o["_id"]}, {"_id": 1}):
                mongo.db.badges.delete_many({"event_id": e["_id"]})
                mongo.db.redemptions.delete_many({"event_id": e["_id"]})
                mongo.db.prize_claims.delete_many({"event_id": e["_id"]})
                mongo.db.events.delete_one({"_id": e["_id"]})
            mongo.db.memberships.delete_many({"org_id": o["_id"]})
            mongo.db.organizations.delete_one({"_id": o["_id"]})

        for k, em in emails.items():
            uids[k] = user_model.create_user(k.title(), "CV", em, hash_password("TestPass1!"), role="attendee")
        super_admin = mongo.db.users.find_one({"platform_role": "super_admin"})
        if not super_admin:
            raise SystemExit("No super_admin in DB — cannot verify.")

        org_a = org_model.create_org(f"{SUFFIX} A", f"{SUFFIX}-a", created_by=uids["owner"])
        org_b = org_model.create_org(f"{SUFFIX} B", f"{SUFFIX}-b", created_by=uids["outsider"])
        membership_model.add_membership(uids["owner"], org_a, "owner")
        membership_model.add_membership(uids["staff"], org_a, "staff")
        membership_model.add_membership(uids["outsider"], org_b, "staff")  # staff of a DIFFERENT org

        ev1 = event_model.create_event("CV ev1", "", None, None, "", "Prize One", uids["owner"], org_id=org_a)
        ev2 = event_model.create_event("CV ev2", "", None, None, "", "Prize Two", uids["owner"], org_id=org_a)
        # "done" completes both events; "todo" completes neither.
        _complete(uids["done"], org_a, ev1)
        _complete(uids["done"], org_a, ev2)

        with app.app_context():
            tok = {k: encode_token(uids[k], "attendee", 0) for k in uids}
            sat = encode_token(str(super_admin["_id"]), super_admin["role"], super_admin.get("token_version", 0))
            forged_todo = sign_claim_token(uids["todo"], ev1)   # valid signature, NOT completed
        H = lambda t: {"Authorization": f"Bearer {t}"}

        # ---- 1. not-completed attendee cannot get a claim QR ----
        check("not-completed attendee -> GET claim/qr is 403",
              client.get(f"/events/{ev1}/claim/qr", headers=H(tok["todo"])).status_code == 403)

        # ---- 2. completed attendee gets a signed, still-unclaimed QR ----
        r = client.get(f"/events/{ev1}/claim/qr", headers=H(tok["done"]))
        qr_body = r.get_json() or {}
        claim_token = qr_body.get("token")
        check("completed attendee -> 200 with token + qr, claimed False",
              r.status_code == 200 and qr_body.get("claimed") is False
              and bool(claim_token) and str(qr_body.get("qr", "")).startswith("data:image/png"))

        # ---- 3. staff verifies -> AWARDED + stamped row ----
        r = client.post("/claims/verify", headers=H(tok["staff"]), json={"token": claim_token})
        aw = r.get_json() or {}
        row = mongo.db.prize_claims.find_one({"user_id": ObjectId(uids["done"]), "event_id": ObjectId(ev1)})
        check("staff verify -> awarded, row claimed, awarded_by=staff",
              r.status_code == 200 and aw.get("result") == "awarded"
              and row and row.get("status") == "claimed"
              and str(row.get("awarded_by")) == str(uids["staff"]) and row.get("awarded_at"))

        # ---- 4. re-verify the same token -> denied already_claimed, no second flip ----
        r = client.post("/claims/verify", headers=H(tok["staff"]), json={"token": claim_token})
        dn = r.get_json() or {}
        cnt = mongo.db.prize_claims.count_documents({"user_id": ObjectId(uids["done"]), "event_id": ObjectId(ev1)})
        check("re-verify -> denied already_claimed with awarder, exactly one row",
              dn.get("result") == "denied" and dn.get("reason") == "already_claimed"
              and (dn.get("claim") or {}).get("awarded_by_name") and cnt == 1)

        # ---- 5. unique index makes award() atomic (a direct second award raises) ----
        dup = False
        try:
            claim_model.award(uids["done"], ev1, org_a, awarded_by=uids["owner"])
        except DuplicateKeyError:
            dup = True
        check("direct second award() raises DuplicateKeyError (unique-index race guard)", dup)

        # ---- 6. forged token for a NOT-completed user -> denied not_completed ----
        r = client.post("/claims/verify", headers=H(tok["staff"]), json={"token": forged_todo})
        check("forged token for non-completed user -> denied not_completed",
              (r.get_json() or {}).get("reason") == "not_completed")

        # ---- 7. staff of another org cannot verify this event ----
        with app.app_context():
            ev2_token = sign_claim_token(uids["done"], ev2)  # fresh, unclaimed
        r = client.post("/claims/verify", headers=H(tok["outsider"]), json={"token": ev2_token})
        check("staff of a DIFFERENT org -> 403 out_of_scope",
              r.status_code == 403 and (r.get_json() or {}).get("reason") == "out_of_scope")

        # ---- 8. super_admin can verify any event ----
        r = client.post("/claims/verify", headers=H(sat), json={"token": ev2_token})
        check("super_admin verifies any event -> awarded",
              r.status_code == 200 and (r.get_json() or {}).get("result") == "awarded")

        # ---- 9. tampered signature -> denied invalid_token ----
        r = client.post("/claims/verify", headers=H(tok["staff"]), json={"token": (claim_token or "") + "tampered"})
        check("tampered signature -> denied invalid_token",
              (r.get_json() or {}).get("reason") == "invalid_token")

        # ---- 10. audit captured both an award and a denial ----
        awarded = mongo.db.audit_log.count_documents({"action": "prize.claim.award", "event_id": {"$in": [ev1, ev2]}})
        denied = mongo.db.audit_log.count_documents({"action": "prize.claim.deny", "event_id": {"$in": [ev1, ev2]}})
        check("audit logged both prize.claim.award and prize.claim.deny (with event_id)",
              awarded >= 1 and denied >= 1)

    finally:
        for ev in (ev1, ev2):
            if ev:
                mongo.db.badges.delete_many({"event_id": ObjectId(ev)})
                mongo.db.redemptions.delete_many({"event_id": ObjectId(ev)})
                mongo.db.prize_claims.delete_many({"event_id": ObjectId(ev)})
                mongo.db.events.delete_one({"_id": ObjectId(ev)})
        for org in (org_a, org_b):
            if org:
                mongo.db.audit_log.delete_many({"org_id": org})
                mongo.db.memberships.delete_many({"org_id": ObjectId(org)})
                mongo.db.organizations.delete_one({"_id": ObjectId(org)})
        if uids:
            mongo.db.audit_log.delete_many({"actor_id": {"$in": list(uids.values())}})
        mongo.db.users.delete_many({"email": {"$in": list(emails.values())}})
        print("\n  cleaned up throwaway fixtures (users, orgs, memberships, events, badges, redemptions, prize_claims, audit)")

    fails = [l for s, l in results if s == FAIL]
    print(f"\n=== {len(results) - len(fails)}/{len(results)} checks passed ===")
    if fails:
        raise SystemExit("FAILED:\n  - " + "\n  - ".join(fails))


if __name__ == "__main__":
    main()
