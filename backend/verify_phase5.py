"""Phase 5 verification — announcements (super-admin-only, platform-wide).

Drives the real HTTP surface with locally-minted JWTs and throwaway fixtures, proving:
  1. only a super_admin can create/edit/delete announcements (org admin + attendee
     get 403 on writes)
  2. every authenticated user can READ announcements (200)
  3. an announcement may link any event; the read payload carries that event's
     metadata for the home link
  4. unread tracking: a fresh user sees the announcement as unread; after POST
     /announcements/seen it reads as read (unread_count -> 0)
  5. writes are recorded in the audit_log with the announcement.* actions
  6. app still works (feed)
All fixtures cleaned up.

Usage:  python verify_phase5.py
"""

from bson import ObjectId

from app import create_app, mongo
from app.utils.auth import encode_token, hash_password
from app.models import user as user_model

PASS, FAIL = "PASS", "FAIL"
results = []
SUFFIX = "p5verify"


def check(label, cond):
    results.append((PASS if cond else FAIL, label))
    print(f"  [{PASS if cond else FAIL}] {label}")
    return cond


def main():
    app = create_app()
    client = app.test_client()
    emails = {k: f"{SUFFIX}_{k}@example.invalid" for k in ("admin", "attendee")}
    ann_id = ev_id = None
    super_admin = None
    uids = {}
    try:
        for em in emails.values():
            mongo.db.users.delete_one({"email": em})
        for k, em in emails.items():
            uids[k] = user_model.create_user(k.title(), "P5", em, hash_password("TestPass1!"), role="attendee")
        super_admin = mongo.db.users.find_one({"platform_role": "super_admin"})
        if not super_admin:
            raise SystemExit("No super_admin in DB — cannot verify Phase 5.")

        # A throwaway event to link the announcement to.
        ev_id = mongo.db.events.insert_one(
            {"name": f"{SUFFIX} linked event", "event_type": "workshop", "org_id": None,
             "created_by": ObjectId(uids["admin"])}
        ).inserted_id
        ev_id = str(ev_id)

        with app.app_context():
            sat = encode_token(str(super_admin["_id"]), super_admin["role"])
            tok = {k: encode_token(uids[k], "attendee") for k in uids}
        H = lambda t: {"Authorization": f"Bearer {t}"}
        sah = H(sat)

        # ---- 1. write gate: non-super-admin forbidden ----
        check("attendee cannot create an announcement (403)",
              client.post("/announcements", headers=H(tok["attendee"]), json={"title": "x", "body": "y"}).status_code == 403)
        check("org admin (no platform_role) cannot create an announcement (403)",
              client.post("/announcements", headers=H(tok["admin"]), json={"title": "x", "body": "y"}).status_code == 403)

        # ---- 3. super_admin creates one linked to the event ----
        r = client.post("/announcements", headers=sah,
                        json={"title": f"{SUFFIX} hello", "body": "Come to the event!", "event_id": ev_id})
        ann_id = (r.get_json() or {}).get("id")
        check("super_admin creates announcement (201)", r.status_code == 201 and ann_id)
        check("created payload links the event with its name",
              (r.get_json() or {}).get("event", {}).get("id") == ev_id
              and (r.get_json() or {}).get("event", {}).get("name") == f"{SUFFIX} linked event")

        # validation
        check("empty title rejected (400)",
              client.post("/announcements", headers=sah, json={"title": "", "body": "z"}).status_code == 400)
        check("bad event_id rejected (400)",
              client.post("/announcements", headers=sah, json={"title": "t", "body": "b", "event_id": str(ObjectId())}).status_code == 400)

        # ---- 2 + 4. all users read; unread then seen ----
        r = client.get("/announcements", headers=H(tok["attendee"]))
        body = r.get_json() or {}
        mine = next((a for a in body.get("announcements", []) if a["id"] == ann_id), None)
        check("attendee can read announcements (200)", r.status_code == 200)
        check("fresh user sees announcement as unread + unread_count >= 1",
              mine is not None and mine["unread"] is True and body.get("unread_count", 0) >= 1)
        check("mark seen succeeds (200)",
              client.post("/announcements/seen", headers=H(tok["attendee"])).status_code == 200)
        body2 = client.get("/announcements", headers=H(tok["attendee"])).get_json() or {}
        mine2 = next((a for a in body2.get("announcements", []) if a["id"] == ann_id), None)
        check("after seen: announcement reads as read + unread_count 0",
              mine2 is not None and mine2["unread"] is False and body2.get("unread_count", 0) == 0)

        # ---- edit / delete gating ----
        check("attendee cannot edit (403)",
              client.patch(f"/announcements/{ann_id}", headers=H(tok["attendee"]), json={"title": "nope"}).status_code == 403)
        check("super_admin edits announcement (200)",
              client.patch(f"/announcements/{ann_id}", headers=sah, json={"title": f"{SUFFIX} edited"}).status_code == 200)
        check("attendee cannot delete (403)",
              client.delete(f"/announcements/{ann_id}", headers=H(tok["attendee"])).status_code == 403)

        # ---- 5. audit recorded ----
        check("create + update audited (announcement.* entries present)",
              mongo.db.audit_log.count_documents(
                  {"actor_id": str(super_admin["_id"]), "action": {"$regex": "^announcement\\."}}) >= 2)

        # ---- 6. app still works ----
        check("GET /events/ still works (200)", client.get("/events/", headers=H(tok["attendee"])).status_code == 200)

        # cleanup of the announcement via the API (also exercises delete success path)
        check("super_admin deletes announcement (200)",
              client.delete(f"/announcements/{ann_id}", headers=sah).status_code == 200)
        ann_id = None  # deleted

    finally:
        if ann_id:
            mongo.db.announcements.delete_one({"_id": ObjectId(ann_id)})
        if ev_id:
            mongo.db.events.delete_one({"_id": ObjectId(ev_id)})
        if super_admin:
            mongo.db.audit_log.delete_many(
                {"actor_id": str(super_admin["_id"]), "action": {"$regex": "^announcement\\."}})
        mongo.db.users.delete_many({"email": {"$in": list(emails.values())}})
        print("\n  cleaned up throwaway fixtures (users, event, announcement, audit)")

    fails = [l for s, l in results if s == FAIL]
    print(f"\n=== {len(results) - len(fails)}/{len(results)} checks passed ===")
    if fails:
        raise SystemExit("FAILED:\n  - " + "\n  - ".join(fails))


if __name__ == "__main__":
    main()
