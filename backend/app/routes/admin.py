import re

from flask import Blueprint, request, jsonify

from app.models import event as event_model
from app.models import badge as badge_model
from app.models import redemption as redemption_model
from app.models import user as user_model
from app.models import audit as audit_model
from app.models import organization as org_model
from app.models import membership as membership_model
from app.models import ban as ban_model
from app.utils.auth import jwt_required, super_admin_required
from app.utils.qr import generate_badge_token, build_redeem_url, generate_qr_data_url

# The PLATFORM panel — super-admin only. Global event/badge creation, badge stats, org
# lifecycle, and user management across all tenants. Org-tier members operate through the
# org-scoped /orgs/* routes instead. The two read endpoints that tier internally (audit,
# per-user analytics) stay on jwt_required so org admins keep their own-org view.
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _resolve_org_for_creator(user_id):
    """Pick the org a newly created event belongs to. Today every staffer belongs to
    exactly one org, so this resolves from their membership; the bootstrap (earliest)
    org is a deterministic fallback for a membership-less super_admin. Explicit org
    selection on create arrives with org self-service (P4) — no brand is hardcoded."""
    orgs = membership_model.orgs_for_user(user_id)
    return orgs[0] if orgs else org_model.bootstrap_org_id()


@admin_bp.route("/event", methods=["POST"])
@super_admin_required
def create_event(current_user):
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Event name is required."}), 400

    org_id = _resolve_org_for_creator(current_user["sub"])
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
        visibility=(body.get("visibility") or "public").strip().lower(),
    )
    audit_model.log(current_user["sub"], "event.create", name, org_id=org_id, event_id=event_id)
    return jsonify({"id": event_id, "name": name}), 201


@admin_bp.route("/events/<event_id>/badge", methods=["POST"])
@super_admin_required
def create_badge(current_user, event_id):
    ev = event_model.find_by_id(event_id)
    if not ev:
        return jsonify({"error": "Event not found"}), 404

    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Badge name is required."}), 400

    # Server generates the token + QR image; the client only sends name/description/icon/color.
    token = generate_badge_token()
    qr_url = build_redeem_url(str(ev["_id"]), token)
    qr_image = generate_qr_data_url(qr_url)
    badge_id = badge_model.create_badge(
        event_id=ev["_id"],
        name=name,
        description=(body.get("description") or "").strip(),
        token=token,
        qr_image=qr_image,
        icon=(body.get("icon") or "🏅"),
        color=(body.get("color") or "primary"),
        image=(body.get("image") or "").strip(),
        org_id=ev.get("org_id"),
    )
    audit_model.log(
        current_user["sub"], "badge.create", f"{name} · {ev.get('name', '')}",
        org_id=ev.get("org_id"), event_id=str(ev["_id"]),
    )
    return jsonify(
        {
            "id": badge_id,
            "name": name,
            "token": token,
            "qr_url": qr_url,
            "redeem_path": f"/redeem/{str(ev['_id'])}/{token}",
            "qr_image": qr_image,
        }
    ), 201


@admin_bp.route("/events/<event_id>/badges/bulk", methods=["POST"])
@super_admin_required
def create_badges_bulk(current_user, event_id):
    """Create many badges in one call. Accepts either an explicit list:
        {"badges": [{"name", "description?", "icon?", "color?"}, ...]}
    or a template + count (names become "<name_prefix> 1..N"):
        {"count": N, "name_prefix": "Booth", "icon?": "🏅", "color?": "primary"}
    Returns the created badges (qr generated client-side from qr_url for the print sheet)."""
    ev = event_model.find_by_id(event_id)
    if not ev:
        return jsonify({"error": "Event not found"}), 404

    body = request.get_json(silent=True) or {}
    specs = body.get("badges")

    if not isinstance(specs, list):
        count = body.get("count")
        prefix = (body.get("name_prefix") or body.get("name") or "").strip()
        shared = {"icon": body.get("icon", "🏅"), "color": body.get("color", "primary")}
        if isinstance(count, int) and count > 0 and prefix:
            specs = [{"name": f"{prefix} {i}", **shared} for i in range(1, count + 1)]
        else:
            return jsonify({"error": "Provide a 'badges' list, or a 'count' plus a 'name_prefix'."}), 400

    cleaned = []
    for s in specs:
        if not isinstance(s, dict):
            continue
        name = (s.get("name") or "").strip()
        if name:
            cleaned.append({**s, "name": name})

    if not cleaned:
        return jsonify({"error": "No valid badge names were provided."}), 400
    if len(cleaned) > 100:
        return jsonify({"error": "You can create at most 100 badges at once."}), 400

    created = []
    for s in cleaned:
        token = generate_badge_token()
        qr_url = build_redeem_url(str(ev["_id"]), token)
        qr_image = generate_qr_data_url(qr_url)
        badge_id = badge_model.create_badge(
            event_id=ev["_id"],
            name=s["name"],
            description=(s.get("description") or "").strip(),
            token=token,
            qr_image=qr_image,
            icon=(s.get("icon") or "🏅"),
            color=(s.get("color") or "primary"),
            image=(s.get("image") or "").strip(),
            org_id=ev.get("org_id"),
        )
        created.append(
            {
                "id": badge_id,
                "name": s["name"],
                "token": token,
                "qr_url": qr_url,
                "redeem_path": f"/redeem/{str(ev['_id'])}/{token}",
            }
        )
    audit_model.log(
        current_user["sub"], "badge.bulk_create", f"{len(created)} badges · {ev.get('name', '')}",
        org_id=ev.get("org_id"), event_id=str(ev["_id"]),
    )
    return jsonify({"created": created, "count": len(created)}), 201


@admin_bp.route("/events/<event_id>/status", methods=["PATCH"])
@super_admin_required
def set_event_status(current_user, event_id):
    """Start/stop an event: a manual activation override that forces the event active
    (scannable now) or reverts it to its date-derived status. Reduces human error
    around date windows."""
    ev = event_model.find_by_id(event_id)
    if not ev:
        return jsonify({"error": "Event not found"}), 404
    started = bool((request.get_json(silent=True) or {}).get("started", True))
    event_model.set_started(event_id, started)
    audit_model.log(
        current_user["sub"], "event.start" if started else "event.stop",
        ev.get("name", ""), org_id=ev.get("org_id"), event_id=str(ev["_id"]),
    )
    ev["started"] = started
    return jsonify({"id": event_id, "started": started, "status": event_model.status_of(ev)}), 200


@admin_bp.route("/events/<event_id>/pause", methods=["PATCH"])
@super_admin_required
def pause_event(current_user, event_id):
    """Temporary moderation lock: attendees keep seeing earned badges but cannot scan.
    Reversible (paused=false unlocks)."""
    ev = event_model.find_by_id(event_id)
    if not ev:
        return jsonify({"error": "Event not found"}), 404
    paused = bool((request.get_json(silent=True) or {}).get("paused", True))
    event_model.set_paused(event_id, paused)
    audit_model.log(current_user["sub"], "event.pause" if paused else "event.unpause",
                    ev.get("name", ""), org_id=ev.get("org_id"), event_id=str(ev["_id"]))
    ev["paused"] = paused
    return jsonify({"id": event_id, "paused": paused, "status": event_model.status_of(ev)}), 200


@admin_bp.route("/events/<event_id>/end", methods=["PATCH"])
@super_admin_required
def end_event(current_user, event_id):
    """Terminal moderation: moves the event to past events and blocks scanning.
    Reversible by a super admin (ended=false reopens)."""
    ev = event_model.find_by_id(event_id)
    if not ev:
        return jsonify({"error": "Event not found"}), 404
    ended = bool((request.get_json(silent=True) or {}).get("ended", True))
    event_model.set_ended(event_id, ended)
    audit_model.log(current_user["sub"], "event.end" if ended else "event.reopen",
                    ev.get("name", ""), org_id=ev.get("org_id"), event_id=str(ev["_id"]))
    ev["ended"] = ended
    return jsonify({"id": event_id, "ended": ended, "status": event_model.status_of(ev)}), 200


@admin_bp.route("/events/<event_id>/badges", methods=["GET"])
@super_admin_required
def list_badges(current_user, event_id):
    ev = event_model.find_by_id(event_id)
    if not ev:
        return jsonify({"error": "Event not found"}), 404

    total_attendees = user_model.count_attendees()
    out = []
    for b in badge_model.find_by_event(ev["_id"]):
        token = b.get("token", "")
        # No qr_image in this list response (keeps the payload light per the mobile rule);
        # the QR is regenerated client-side from qr_url, and is also stored on each badge doc.
        out.append(
            {
                "id": str(b["_id"]),
                "name": b.get("name", ""),
                "description": b.get("description", ""),
                "icon": b.get("icon", "🏅"),
                "color": b.get("color", "primary"),
                "image": b.get("image", ""),
                "token": token,
                "qr_url": build_redeem_url(str(ev["_id"]), token),
                "redeem_path": f"/redeem/{str(ev['_id'])}/{token}",
                "redeemed_by": redemption_model.count_for_badge(b["_id"]),
                "total_attendees": total_attendees,
            }
        )
    return jsonify(out), 200


# --- Organization lifecycle (super-admin platform governance) ---

@admin_bp.route("/orgs", methods=["GET"])
@super_admin_required
def list_orgs(current_user):
    """Platform-wide org directory for the super-admin panel: status, owner, and cheap
    member/event counts."""
    out = []
    for o in org_model.all_orgs():
        oid = str(o["_id"])
        members = membership_model.members_of(oid)
        owner = next((m for m in members if m.get("role") == "owner"), None)
        owner_email = ""
        if owner:
            ou = user_model.find_by_id(owner["user_id"])
            owner_email = ou.get("email", "") if ou else ""
        out.append({
            "id": oid,
            "name": o.get("name", ""),
            "slug": o.get("slug", ""),
            "status": o.get("status", "active"),
            "owner_email": owner_email,
            "members_count": len(members),
            "events_count": len(event_model.all_events(org_id=oid)),
            "created_at": event_model.fmt_date(o.get("created_at")),
        })
    return jsonify({"orgs": out}), 200


@admin_bp.route("/orgs/<org_id>/status", methods=["PATCH"])
@super_admin_required
def set_org_status(current_user, org_id):
    """Suspend or reactivate an org (platform governance). Suspending freezes the org's
    scans and event creation; it never touches member accounts (attendees stay
    platform-level)."""
    org = org_model.find_by_id(org_id)
    if not org:
        return jsonify({"error": "Organization not found."}), 404
    status = (request.get_json(silent=True) or {}).get("status", "")
    if status not in ("active", "suspended"):
        return jsonify({"error": "Status must be 'active' or 'suspended'."}), 400
    org_model.update_org(org_id, {"status": status})
    audit_model.log(current_user["sub"], "org.suspend" if status == "suspended" else "org.reactivate",
                    org.get("name", ""), org_id=org_id)
    return jsonify({"id": org_id, "status": status}), 200


# --- User management (super-admin only): track badge counts, promote/demote ---

@admin_bp.route("/users", methods=["GET"])
@super_admin_required
def list_users(current_user):
    counts = redemption_model.counts_by_user()
    out = []
    for u in user_model.all_users():
        uid = str(u["_id"])
        out.append(
            {
                "id": uid,
                "name": u.get("name", ""),
                "lastname": u.get("lastname", ""),
                "email": u.get("email", ""),
                "role": u.get("role", "attendee"),
                "disabled": bool(u.get("disabled", False)),
                "badges_count": counts.get(uid, 0),
                "created_at": event_model.fmt_date(u.get("created_at")),
            }
        )
    return jsonify({"users": out}), 200


@admin_bp.route("/users/<user_id>/badges", methods=["GET"])
@super_admin_required
def user_badges(current_user, user_id):
    user = user_model.find_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Same per-event grouping as /me/badges, but for the user the admin is inspecting.
    events = []
    for ev in event_model.all_events():
        badges = badge_model.find_by_event(ev["_id"])
        redeemed = redemption_model.redeemed_badge_map(user_id, ev["_id"])
        total = len(badges)
        earned = sum(1 for b in badges if str(b["_id"]) in redeemed)
        events.append(
            {
                "event_id": str(ev["_id"]),
                "event": ev.get("name", ""),
                "date": event_model.fmt_date(ev.get("start_date")),
                "status": event_model.status_of(ev),
                "prize": ev.get("prize", ""),
                "badges_total": total,
                "badges_earned": earned,
                "completed": total > 0 and earned >= total,
                "badges": [
                    badge_model.public_badge(b, str(b["_id"]) in redeemed, redeemed.get(str(b["_id"])))
                    for b in badges
                ],
            }
        )

    return jsonify(
        {
            "user": {
                "id": str(user["_id"]),
                "name": user.get("name", ""),
                "lastname": user.get("lastname", ""),
                "email": user.get("email", ""),
                "role": user.get("role", "attendee"),
                "badges_count": redemption_model.count_for_user(user_id),
            },
            "events": events,
        }
    ), 200


@admin_bp.route("/users/<user_id>/analytics", methods=["GET"])
@jwt_required
def user_analytics(current_user, user_id):
    # Admin-tier analytics surface, under the same tier rules as the audit: a
    # super_admin sees the user's full activity; an org owner/admin sees only the
    # portion within their org(s); staff/attendees are refused.
    actor = user_model.find_by_id(current_user["sub"])
    is_super = user_model.is_super_admin(actor)
    org_ids = None
    if not is_super:
        org_ids = membership_model.admin_orgs_for_user(current_user["sub"])
        if not org_ids:
            return jsonify({"error": "Admin access required."}), 403

    if not user_model.find_by_id(user_id):
        return jsonify({"error": "User not found"}), 404

    period = request.args.get("period", "day")
    if period not in ("day", "week", "month"):
        period = "day"

    # Audit org_id is stored as a string; redemptions store an ObjectId — each helper
    # handles its own collection's type.
    audit_scope = None if is_super else {"org_id": {"$in": org_ids}}
    payload = {
        "user_id": user_id,
        "period": period,
        "activity": audit_model.activity_buckets(user_id, period, audit_scope),
        "favorite_event_type": redemption_model.favorite_event_type(user_id, org_ids),
    }
    # login_count is a platform-level metric — surfaced to super_admin only, since an
    # org admin must not gain cross-org visibility into a user.
    if is_super:
        payload["login_count"] = audit_model.login_count(user_id)
    return jsonify(payload), 200


@admin_bp.route("/users/<user_id>/role", methods=["PATCH"])
@super_admin_required
def set_user_role(current_user, user_id):
    body = request.get_json(silent=True) or {}
    role = (body.get("role") or "").strip().lower()
    if role not in ("admin", "attendee", "assistant"):
        return jsonify({"error": "Role must be 'admin', 'assistant' or 'attendee'."}), 400
    if user_id == current_user["sub"]:
        return jsonify({"error": "You can’t change your own role."}), 400
    target = user_model.find_by_id(user_id)
    if not target:
        return jsonify({"error": "User not found"}), 404

    user_model.set_role(user_id, role)
    audit_model.log(current_user["sub"], "user.role_change", f"{target.get('email', user_id)} → {role}")
    return jsonify({"id": user_id, "role": role}), 200


@admin_bp.route("/users/<user_id>/disable", methods=["PATCH"])
@super_admin_required
def toggle_disable_user(current_user, user_id):
    if user_id == current_user["sub"]:
        return jsonify({"error": "You can't disable your own account."}), 400
    target = user_model.find_by_id(user_id)
    if not target:
        return jsonify({"error": "User not found"}), 404

    body = request.get_json(silent=True) or {}
    disabled = bool(body.get("disabled", True))
    user_model.set_disabled(user_id, disabled)
    action = "user.disable" if disabled else "user.enable"
    audit_model.log(current_user["sub"], action, target.get("email", user_id))
    return jsonify({"id": user_id, "disabled": disabled}), 200


@admin_bp.route("/users/<user_id>", methods=["DELETE"])
@super_admin_required
def delete_user(current_user, user_id):
    if user_id == current_user["sub"]:
        return jsonify({"error": "You can't delete your own account."}), 400
    target = user_model.find_by_id(user_id)
    if not target:
        return jsonify({"error": "User not found"}), 404

    redemption_model.delete_by_user(user_id)
    ban_model.delete_by_user(user_id)
    user_model.delete_user(user_id)
    audit_model.log(current_user["sub"], "user.delete", target.get("email", user_id))
    return jsonify({"id": user_id, "deleted": True}), 200


@admin_bp.route("/audit", methods=["GET"])
@jwt_required
def audit_log(current_user):
    # Tiered access: a platform super_admin sees everything; an org owner/admin sees
    # only entries for the org(s) they administer; staff and attendees get nothing.
    # (Guarded by membership/platform, not the legacy global role, so it stays correct
    # for org admins introduced by self-service in P4.)
    actor = user_model.find_by_id(current_user["sub"])
    is_super = user_model.is_super_admin(actor)

    clauses = []
    if not is_super:
        org_ids = membership_model.admin_orgs_for_user(current_user["sub"])
        if not org_ids:
            return jsonify({"error": "Admin access required."}), 403
        clauses.append({"org_id": {"$in": org_ids}})

    # Search by USER (email/name -> actor) or EVENT (name -> event_id), server-side
    # over indexed fields; actor_email regex also matches entries whose user is gone.
    q = (request.args.get("q") or "").strip()
    if q:
        clauses.append({"$or": [
            {"actor_id": {"$in": user_model.search_ids(q)}},
            {"event_id": {"$in": event_model.search_ids(q)}},
            {"actor_email": {"$regex": re.escape(q), "$options": "i"}},
        ]})

    filt = {"$and": clauses} if clauses else {}
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (TypeError, ValueError):
        page = 1

    entries, total = audit_model.query(filt, page, audit_model.PAGE_SIZE)
    return jsonify({
        "entries": entries,
        "page": page,
        "page_size": audit_model.PAGE_SIZE,
        "total": total,
        "has_more": page * audit_model.PAGE_SIZE < total,
    }), 200
