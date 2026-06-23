import secrets

from flask import Blueprint, request, jsonify

from app.models import invite as invite_model
from app.models import organization as org_model
from app.models import membership as membership_model
from app.models import user as user_model
from app.models import event as event_model
from app.models import badge as badge_model
from app.models import redemption as redemption_model
from app.models import audit as audit_model
from app.utils.auth import jwt_required, super_admin_required, org_role_required
from app.utils.qr import generate_badge_token, build_redeem_url, generate_qr_data_url

# Org self-service: the in-app invite inbox, org-creation/join invites, org settings,
# member management, and the org-scoped management panel. The existing /admin/* routes
# remain the super-admin PLATFORM panel; everything here is org-scoped and authorized
# per membership via org_role_required (super_admin passes any check).
orgs_bp = Blueprint("orgs", __name__)


def _email_of(user_id):
    u = user_model.find_by_id(user_id)
    return u.get("email") if u else None


# ───────────────────────── invite inbox (any signed-in user) ─────────────────────────

@orgs_bp.route("/me/invites", methods=["GET"])
@jwt_required
def my_invites(current_user):
    email = _email_of(current_user["sub"])
    out = []
    for inv in invite_model.pending_for_email(email or ""):
        org = org_model.find_by_id(inv["org_id"]) if inv.get("org_id") else None
        out.append(invite_model.public(inv, org))
    return jsonify({"invites": out}), 200


@orgs_bp.route("/invites/accept", methods=["POST"])
@jwt_required
def accept_invite(current_user):
    token = (request.get_json(silent=True) or {}).get("token", "")
    uid = current_user["sub"]
    email = _email_of(uid)
    inv = invite_model.accept_atomic(token, email, uid)
    if not inv:
        return jsonify({"error": "This invite is invalid, expired, already used, or not for your account."}), 400

    if inv["type"] == "create_org":
        # Redeeming creates a NEW org and makes the redeemer its owner — nothing else.
        # No platform_role, no cross-org capability.
        org_id = org_model.create_org("My organization", f"org-{secrets.token_hex(5)}", created_by=uid)
        membership_model.add_membership(uid, org_id, "owner")
        audit_model.log(uid, "org.create", "My organization", org_id=org_id)
        org = org_model.find_by_id(org_id)
        return jsonify({"type": "create_org", "org": org_model.public_org(org)}), 200

    if inv["type"] == "org_join":
        role = inv.get("role") or "admin"
        membership_model.add_membership(uid, inv["org_id"], role)
        audit_model.log(uid, "org.member_join", role, org_id=inv["org_id"])
        org = org_model.find_by_id(inv["org_id"])
        return jsonify({"type": "org_join", "org": org_model.public_org(org), "role": role}), 200

    # "event" type is reserved for Phase 5 (announcements).
    return jsonify({"error": "Unsupported invite type."}), 400


# ───────────────────────── create-org invites (super-admin platform panel) ─────────────────────────

@orgs_bp.route("/admin/org-invites", methods=["POST"])
@super_admin_required
def create_org_invite(current_user):
    email = (request.get_json(silent=True) or {}).get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "An invitee email is required."}), 400
    inv = invite_model.create("create_org", email, invited_by=current_user["sub"])
    audit_model.log(current_user["sub"], "invite.create_org", email)
    return jsonify(invite_model.public(inv)), 201


@orgs_bp.route("/admin/org-invites", methods=["GET"])
@super_admin_required
def list_org_invites(current_user):
    return jsonify({"invites": [invite_model.public(i) for i in invite_model.list_by_type("create_org")]}), 200


@orgs_bp.route("/admin/org-invites/<invite_id>/revoke", methods=["POST"])
@super_admin_required
def revoke_org_invite(current_user, invite_id):
    inv = invite_model.find_by_id(invite_id)
    if not inv or inv.get("type") != "create_org":
        return jsonify({"error": "Invite not found."}), 404
    return (jsonify({"id": invite_id, "status": "revoked"}), 200) if invite_model.revoke(invite_id) \
        else (jsonify({"error": "Only a pending invite can be revoked."}), 400)


# ───────────────────────── org settings + members (org panel) ─────────────────────────

@orgs_bp.route("/orgs/<org_id>", methods=["GET"])
@org_role_required("owner", "admin", "staff")
def get_org(current_user, org_id):
    org = org_model.find_by_id(org_id)
    if not org:
        return jsonify({"error": "Organization not found."}), 404
    return jsonify({
        **org_model.public_org(org),
        "description": org.get("description", ""),
        "status": org.get("status", "active"),
    }), 200


@orgs_bp.route("/orgs/<org_id>", methods=["PATCH"])
@org_role_required("owner")
def update_org(current_user, org_id):
    body = request.get_json(silent=True) or {}
    fields = {}
    if "name" in body:
        fields["name"] = (body.get("name") or "").strip()
    if "description" in body:
        fields["description"] = (body.get("description") or "").strip()
    if not fields:
        return jsonify({"error": "Nothing to update."}), 400
    org_model.update_org(org_id, fields)
    audit_model.log(current_user["sub"], "org.update", ", ".join(fields), org_id=org_id)
    return jsonify({**org_model.public_org(org_model.find_by_id(org_id)),
                    "description": fields.get("description", "")}), 200


@orgs_bp.route("/orgs/<org_id>/members", methods=["GET"])
@org_role_required("owner", "admin")
def list_members(current_user, org_id):
    out = []
    for m in membership_model.members_of(org_id):
        u = user_model.find_by_id(m["user_id"])
        if u:
            out.append({
                "user_id": str(u["_id"]),
                "name": u.get("name", ""),
                "lastname": u.get("lastname", ""),
                "email": u.get("email", ""),
                "role": m.get("role"),
            })
    return jsonify({"members": out}), 200


@orgs_bp.route("/orgs/<org_id>/members/<user_id>", methods=["PATCH"])
@org_role_required("owner")
def change_member_role(current_user, org_id, user_id):
    role = (request.get_json(silent=True) or {}).get("role", "")
    if role not in ("admin", "staff"):
        return jsonify({"error": "Role must be 'admin' or 'staff'."}), 400
    if user_id == current_user["sub"]:
        return jsonify({"error": "You can't change your own role."}), 400
    if not membership_model.find(user_id, org_id):
        return jsonify({"error": "That user is not a member of this organization."}), 404
    membership_model.add_membership(user_id, org_id, role)  # upsert -> updates role
    audit_model.log(current_user["sub"], "org.member_role", f"{user_id} → {role}", org_id=org_id)
    return jsonify({"user_id": user_id, "role": role}), 200


@orgs_bp.route("/orgs/<org_id>/members/<user_id>", methods=["DELETE"])
@org_role_required("owner")
def remove_member(current_user, org_id, user_id):
    if user_id == current_user["sub"]:
        return jsonify({"error": "An owner can't remove themselves."}), 400
    if not membership_model.find(user_id, org_id):
        return jsonify({"error": "That user is not a member of this organization."}), 404
    membership_model.remove(user_id, org_id)
    audit_model.log(current_user["sub"], "org.member_remove", user_id, org_id=org_id)
    return jsonify({"user_id": user_id, "removed": True}), 200


# ───────────────────────── org_join invites (owner/admin) ─────────────────────────

@orgs_bp.route("/orgs/<org_id>/invites", methods=["POST"])
@org_role_required("owner", "admin")
def create_join_invite(current_user, org_id):
    email = (request.get_json(silent=True) or {}).get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "An invitee email is required."}), 400
    inv = invite_model.create("org_join", email, invited_by=current_user["sub"], org_id=org_id, role="admin")
    audit_model.log(current_user["sub"], "invite.org_join", email, org_id=org_id)
    return jsonify(invite_model.public(inv)), 201


@orgs_bp.route("/orgs/<org_id>/invites", methods=["GET"])
@org_role_required("owner", "admin")
def list_join_invites(current_user, org_id):
    return jsonify({"invites": [invite_model.public(i) for i in invite_model.list_for_org(org_id, "org_join")]}), 200


@orgs_bp.route("/orgs/<org_id>/invites/<invite_id>/revoke", methods=["POST"])
@org_role_required("owner", "admin")
def revoke_join_invite(current_user, org_id, invite_id):
    inv = invite_model.find_by_id(invite_id)
    if not inv or str(inv.get("org_id")) != str(org_id):
        return jsonify({"error": "Invite not found."}), 404
    return (jsonify({"id": invite_id, "status": "revoked"}), 200) if invite_model.revoke(invite_id) \
        else (jsonify({"error": "Only a pending invite can be revoked."}), 400)


# ───────────────────────── org-scoped management panel ─────────────────────────

@orgs_bp.route("/orgs/<org_id>/events", methods=["GET"])
@org_role_required("owner", "admin", "staff")
def org_events(current_user, org_id):
    out = []
    for ev in event_model.all_events(org_id=org_id):
        total = badge_model.count_for_event(ev["_id"])
        out.append(event_model.event_summary(ev, total, 0))
    return jsonify(out), 200


@orgs_bp.route("/orgs/<org_id>/event", methods=["POST"])
@org_role_required("owner", "admin")
def org_create_event(current_user, org_id):
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Event name is required."}), 400
    event_id = event_model.create_event(
        name=name,
        description=(body.get("description") or "").strip(),
        start_date=event_model.parse_date(body.get("date") or body.get("start_date")),
        end_date=event_model.parse_date(body.get("end_date")),
        location=(body.get("location") or "").strip(),
        prize=(body.get("prize") or "").strip(),
        created_by=current_user["sub"],
        org_id=org_id,
        event_type=(body.get("event_type") or "uncategorized").strip().lower(),
    )
    audit_model.log(current_user["sub"], "event.create", name, org_id=org_id, event_id=event_id)
    return jsonify({"id": event_id, "name": name}), 201


@orgs_bp.route("/orgs/<org_id>/events/<event_id>/badge", methods=["POST"])
@org_role_required("owner", "admin")
def org_create_badge(current_user, org_id, event_id):
    ev = event_model.find_by_id(event_id)
    if not ev or str(ev.get("org_id")) != str(org_id):
        return jsonify({"error": "Event not found"}), 404
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Badge name is required."}), 400
    token = generate_badge_token()
    qr_url = build_redeem_url(str(ev["_id"]), token)
    badge_id = badge_model.create_badge(
        event_id=ev["_id"], name=name, description=(body.get("description") or "").strip(),
        token=token, qr_image=generate_qr_data_url(qr_url),
        icon=(body.get("icon") or "🏅"), color=(body.get("color") or "primary"),
        image=(body.get("image") or "").strip(), org_id=ev.get("org_id"),
    )
    audit_model.log(current_user["sub"], "badge.create", f"{name} · {ev.get('name', '')}",
                    org_id=org_id, event_id=str(ev["_id"]))
    return jsonify({"id": badge_id, "name": name, "token": token, "qr_url": qr_url}), 201


@orgs_bp.route("/orgs/<org_id>/participants", methods=["GET"])
@org_role_required("owner", "admin", "staff")
def org_participants(current_user, org_id):
    counts = redemption_model.counts_by_user(org_id=org_id)
    out = []
    for uid, n in counts.items():
        u = user_model.find_by_id(uid)
        if u:
            out.append({"id": uid, "name": u.get("name", ""), "lastname": u.get("lastname", ""),
                        "email": u.get("email", ""), "badges_count": n})
    out.sort(key=lambda x: x["badges_count"], reverse=True)
    return jsonify({"participants": out}), 200


@orgs_bp.route("/orgs/<org_id>/audit", methods=["GET"])
@org_role_required("owner", "admin")
def org_audit(current_user, org_id):
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (TypeError, ValueError):
        page = 1
    entries, total = audit_model.query({"org_id": str(org_id)}, page, audit_model.PAGE_SIZE)
    return jsonify({"entries": entries, "page": page, "page_size": audit_model.PAGE_SIZE,
                    "total": total, "has_more": page * audit_model.PAGE_SIZE < total}), 200
