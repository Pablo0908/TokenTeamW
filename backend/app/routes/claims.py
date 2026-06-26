from flask import Blueprint, request, jsonify
from pymongo.errors import DuplicateKeyError

from app.models import event as event_model
from app.models import badge as badge_model
from app.models import redemption as redemption_model
from app.models import membership as membership_model
from app.models import user as user_model
from app.models import audit as audit_model
from app.models import prize_claim as claim_model
from app.utils.auth import jwt_required
from app.utils.qr import sign_claim_token, verify_claim_token, generate_qr_data_url, CLAIM_TTL_SECONDS

# Prize-claim verification (staff-scanned, server-authoritative). This is a claim-STATE
# layer on top of existing completion — it does NOT touch the `prize` string or build a
# rewards subsystem. The attendee's claim QR is an assertion only; ALL authority is the
# server-side atomic flip in claim_model.award().
claims_bp = Blueprint("claims", __name__)


def _display_name(user_doc):
    if not user_doc:
        return None
    full = " ".join(p for p in (user_doc.get("name"), user_doc.get("lastname")) if p).strip()
    return full or user_doc.get("email")


def _has_completed(user_id, event):
    """Re-derive completion from server truth — the same check the redeem path uses
    (badges minted vs this user's redemptions). Never trusts the client."""
    total = badge_model.count_for_event(event["_id"])
    earned = redemption_model.count_for_event(user_id, event["_id"])
    return total > 0 and earned >= total


@claims_bp.route("/events/<event_id>/claim/qr", methods=["GET"])
@jwt_required
def claim_qr(current_user, event_id):
    """Attendee-facing, READ-ONLY. Returns the signed claim QR for an event the caller has
    completed. Changes no state. If the prize was already claimed, returns that instead of
    a QR so the screen shows the handover record, not a forgeable code."""
    uid = current_user["sub"]
    ev = event_model.find_by_id(event_id)
    if not ev:
        return jsonify({"error": "Event not found"}), 404

    # Claiming is gated on COMPLETION only — not on event status. A prize for a now-past
    # event must still be claimable (handover happens after the event, in the real world).
    if not _has_completed(uid, ev):
        return jsonify({"error": "Complete the event to claim your prize."}), 403

    existing = claim_model.find(uid, ev["_id"])
    if existing:
        awarder = _display_name(user_model.find_by_id(existing.get("awarded_by")))
        return jsonify({"claimed": True, "claim": claim_model.public_claim(existing, awarder)}), 200

    token = sign_claim_token(uid, str(ev["_id"]))
    return jsonify({
        "claimed": False,
        "token": token,
        "qr": generate_qr_data_url(token),
        "ttl": CLAIM_TTL_SECONDS,
        "prize": ev.get("prize", ""),
    }), 200


def _deny(actor_id, reason, *, org_id=None, event_id=None, target=None, event_name=None, http=200, claim=None):
    """Record a denied claim attempt in the audit (actor, target, event, org, reason) and
    return the denial. Every denial is logged for human review — we never auto-block."""
    detail = " · ".join(p for p in (target, event_name, f"denied: {reason}") if p)
    audit_model.log(actor_id, "prize.claim.deny", detail, org_id=org_id, event_id=event_id)
    body = {"result": "denied", "reason": reason}
    if claim is not None:
        body["claim"] = claim
    return jsonify(body), http


@claims_bp.route("/claims/verify", methods=["POST"])
@jwt_required
def verify(current_user):
    """Staff-facing, MUTATING — the inverse of /redeem. Scans the attendee's claim QR and,
    in ONE atomic operation, re-verifies completion, confirms the claim is still unclaimed,
    and flips it to claimed (stamping awarded_by/awarded_at). The server flip IS the award."""
    actor = user_model.find_by_id(current_user["sub"])
    actor_id = current_user["sub"]
    body = request.get_json(silent=True) or {}
    token = (body.get("token") or "").strip()
    claimant_name = (body.get("claimant_name") or "").strip() or None

    # 1. Signature + TTL. A bad/expired/tampered token never reveals anything.
    data = verify_claim_token(token)
    if not data:
        return _deny(actor_id, "invalid_token")

    target_uid, ev_id = data["u"], data["e"]
    ev = event_model.find_by_id(ev_id)
    if not ev:
        return _deny(actor_id, "not_found", event_id=ev_id)
    org_id = str(ev["org_id"]) if ev.get("org_id") else None
    ev_name = ev.get("name", "")
    target_user = user_model.find_by_id(target_uid)
    target_name = _display_name(target_user)

    # 2. Authorize. Org is resolved from the SIGNED TOKEN's event (not the URL), so we
    # enforce the same rule as org_role_required("owner","admin","staff") inline:
    # super_admin may verify any event; otherwise the actor must hold a role in the
    # event's org. Staff/admins can therefore verify ONLY their own org's events.
    authorized = user_model.is_super_admin(actor) or (
        org_id and membership_model.role_in_org(actor_id, org_id) in ("owner", "admin", "staff")
    )
    if not authorized:
        return _deny(actor_id, "out_of_scope", org_id=org_id, event_id=ev_id,
                     target=target_name, event_name=ev_name, http=403)

    # 3. Completion is re-checked server-side on every scan (the QR's claim is not trusted).
    if not target_user or not _has_completed(target_uid, ev):
        return _deny(actor_id, "not_completed", org_id=org_id, event_id=ev_id,
                     target=target_name, event_name=ev_name)

    # 4. Atomic flip. The unique (user, event) index makes this race-safe: concurrent scans
    # → exactly one award; the loser raises DuplicateKeyError and is denied as already-claimed.
    try:
        claim = claim_model.award(target_uid, ev_id, org_id, awarded_by=actor_id, claimant_name=claimant_name)
    except DuplicateKeyError:
        existing = claim_model.find(target_uid, ev_id)
        awarder = _display_name(user_model.find_by_id(existing.get("awarded_by"))) if existing else None
        return _deny(actor_id, "already_claimed", org_id=org_id, event_id=ev_id,
                     target=target_name, event_name=ev_name, http=409,
                     claim=claim_model.public_claim(existing, awarder))

    audit_model.log(actor_id, "prize.claim.award", " · ".join(p for p in (target_name, ev_name) if p),
                    org_id=org_id, event_id=ev_id)
    return jsonify({
        "result": "awarded",
        "claim": claim_model.public_claim(claim, _display_name(actor)),
        "attendee": target_name,
        "event": ev_name,
        "prize": ev.get("prize", ""),
    }), 200
