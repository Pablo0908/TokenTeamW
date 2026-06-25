"""Phase 1 verification — proves the app still works after the tenancy migration.

Exercises the real HTTP surface via Flask's test client with locally-minted JWTs
(so it never touches the OTP/email 2FA path), then cleans up everything it creates:
  1. attendee feed (GET /events/) + event detail — render unchanged, now carry org_id
  2. a full scan -> badge -> completion flow on a throwaway event (asserts org_id on
     the new event/badge/redemption, and that completion + prize still work)
  3. admin surface unchanged (GET /admin/users, GET /admin/audit return 200)
  4. org_role_required: super_admin passes, a non-member attendee is refused

Usage:  python verify_phase1.py
"""

from app import create_app, mongo
from app.utils.auth import encode_token, org_role_required
from flask import jsonify

PASS, FAIL = "PASS", "FAIL"
results = []


def check(label, cond):
    results.append((PASS if cond else FAIL, label))
    print(f"  [{PASS if cond else FAIL}] {label}")
    return cond


def main():
    app = create_app()

    # A temporary org-scoped route so we can prove org_role_required end-to-end.
    @app.route("/__verify_org/<event_id>", endpoint="__verify_org")
    @org_role_required("owner", "admin", "staff")
    def _verify_org(current_user, event_id):
        return jsonify({"ok": True}), 200

    client = app.test_client()

    # Self-contained fixtures: create a throwaway attendee (cleaned up below) instead
    # of depending on the DB already having one. An admin must exist (org #1 admin).
    from app.models import user as user_model
    from app.utils.auth import hash_password
    ATT_EMAIL = "verify_phase1_attendee@example.invalid"
    mongo.db.users.delete_one({"email": ATT_EMAIL})
    att_id = user_model.create_user("Verify", "Attendee", ATT_EMAIL, hash_password("TestPass1!"), role="attendee")
    attendee = user_model.find_by_id(att_id)
    # The /admin/* surface is platform super_admin only (no global admin tier anymore).
    admin = mongo.db.users.find_one({"platform_role": "super_admin"})
    assert attendee and admin, "need at least one super_admin in the DB"

    with app.app_context():
        attendee_tok = encode_token(str(attendee["_id"]), attendee["role"])
        admin_tok = encode_token(str(admin["_id"]), admin["role"])
    ah = {"Authorization": f"Bearer {attendee_tok}"}
    adh = {"Authorization": f"Bearer {admin_tok}"}

    created_event_id = None
    try:
        # 1) Attendee feed + detail
        r = client.get("/events/", headers=ah)
        feed = r.get_json()
        check("GET /events/ -> 200", r.status_code == 200)
        check("feed is a list", isinstance(feed, list))
        check("every feed event exposes org_id (additive)",
              all("org_id" in e for e in feed) if feed else True)
        if feed:
            r = client.get(f"/events/{feed[0]['id']}", headers=ah)
            det = r.get_json()
            check("GET /events/<id> -> 200", r.status_code == 200)
            check("event detail exposes org_id + badges", "org_id" in det and "badges" in det)

        # 2) scan -> badge -> completion (throwaway, single badge so it completes)
        r = client.post("/admin/event", headers=adh,
                        json={"name": "P1 Verify Event", "prize": "Verify Prize"})
        created_event_id = r.get_json().get("id")
        check("admin create event -> 201", r.status_code == 201 and created_event_id)

        ev_doc = mongo.db.events.find_one({"_id": __import__("bson").ObjectId(created_event_id)})
        check("new event has org_id set by the create route", bool(ev_doc and ev_doc.get("org_id")))

        r = client.post(f"/admin/events/{created_event_id}/badge", headers=adh,
                        json={"name": "Verify Badge"})
        badge_payload = r.get_json()
        token = badge_payload.get("token")
        check("admin create badge -> 201", r.status_code == 201 and token)

        badge_doc = mongo.db.badges.find_one({"token": token})
        check("new badge inherited event's org_id",
              bool(badge_doc) and badge_doc.get("org_id") == (ev_doc.get("org_id") if ev_doc else 1))

        # Events start closed (Start/Stop is the master switch) — open it before scanning.
        client.patch(f"/admin/events/{created_event_id}/status", headers=adh, json={"started": True})
        r = client.get(f"/redeem/{created_event_id}/{token}", headers=ah)
        redeem = r.get_json()
        check("scan /redeem -> 200", r.status_code == 200)
        check("badge earned + event completed (1/1)",
              redeem.get("event_completed") is True and redeem.get("badges_earned") == 1)
        check("prize returned on completion", redeem.get("prize") == "Verify Prize")

        red_doc = mongo.db.redemptions.find_one(
            {"user_id": attendee["_id"], "event_id": __import__("bson").ObjectId(created_event_id)})
        check("redemption stored with org_id from event",
              bool(red_doc) and red_doc.get("org_id") == (ev_doc.get("org_id") if ev_doc else 2))

        # 3) admin surface unchanged
        r = client.get("/admin/users", headers=adh)
        users_body = r.get_json()
        check("GET /admin/users -> 200 with users[]", r.status_code == 200 and "users" in users_body)
        check("user rows keep their original shape",
              all({"id", "email", "super_admin", "badges_count"} <= set(u) for u in users_body["users"]))
        r = client.get("/admin/audit", headers=adh)
        check("GET /admin/audit -> 200 with entries[]",
              r.status_code == 200 and "entries" in r.get_json())

        # 4) org_role_required: super_admin passes; non-member attendee refused
        r = client.get(f"/__verify_org/{created_event_id}", headers=adh)
        check("org_role_required: super_admin admin passes (200)", r.status_code == 200)
        r = client.get(f"/__verify_org/{created_event_id}", headers=ah)
        check("org_role_required: non-member attendee refused (403)", r.status_code == 403)

    finally:
        # Clean up everything the throwaway flow created.
        if created_event_id:
            oid = __import__("bson").ObjectId(created_event_id)
            mongo.db.redemptions.delete_many({"event_id": oid})
            mongo.db.badges.delete_many({"event_id": oid})
            mongo.db.events.delete_one({"_id": oid})
            print(f"\n  cleaned up throwaway event {created_event_id} (+ its badge/redemptions)")
        mongo.db.users.delete_one({"email": ATT_EMAIL})
        print("  cleaned up throwaway attendee")

    fails = [l for s, l in results if s == FAIL]
    print(f"\n=== {len(results) - len(fails)}/{len(results)} checks passed ===")
    if fails:
        raise SystemExit("FAILED:\n  - " + "\n  - ".join(fails))


if __name__ == "__main__":
    main()
