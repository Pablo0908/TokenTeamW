import re
from datetime import datetime, timezone

from bson import ObjectId

from app import mongo


# An organization is a tenant. Events (and, transitively, their badges and
# redemptions) hang off an org. Attendee accounts stay platform-level, so they are
# NOT modelled here — org membership for staff/admins lives in `memberships`.
#
# `theme` is per-org white-label: brand colors + a logo. Empty strings mean "fall back
# to the platform (Lyfter) default". Sanitized on write — never trust client input.
_THEME_KEYS = ("primary", "secondary", "accent", "logo_url")
_THEME_SHAPE = {k: "" for k in _THEME_KEYS}
_HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_MAX_LOGO_LEN = 1_000_000  # allow a small data: URL or an external link


def sanitize_theme(raw):
    """Whitelist + validate a client-supplied theme. Unknown keys dropped; invalid hex
    colors and oversized/odd logo URLs become "" (fall back to the platform default)."""
    out = dict(_THEME_SHAPE)
    if not isinstance(raw, dict):
        return out
    for key in ("primary", "secondary", "accent"):
        val = raw.get(key)
        if isinstance(val, str) and _HEX_RE.match(val.strip()):
            out[key] = val.strip().lower()
    logo = raw.get("logo_url")
    if isinstance(logo, str):
        logo = logo.strip()
        if logo and len(logo) <= _MAX_LOGO_LEN and (logo.startswith("https://")
                                                    or logo.startswith("http://")
                                                    or logo.startswith("data:image/")):
            out["logo_url"] = logo
    return out


def create_indexes():
    mongo.db.organizations.create_index("slug", unique=True)


def _oid(value):
    return value if isinstance(value, ObjectId) else ObjectId(value)


def create_org(name, slug, created_by=None, description="", theme=None, status="active"):
    result = mongo.db.organizations.insert_one(
        {
            "name": name,
            "slug": slug,
            "description": description or "",
            "theme": sanitize_theme(theme),
            "status": status,
            "created_by": _oid(created_by) if created_by else None,
            "created_at": datetime.now(timezone.utc),
        }
    )
    return str(result.inserted_id)


def find_by_id(org_id):
    try:
        return mongo.db.organizations.find_one({"_id": _oid(org_id)})
    except Exception:
        return None


def update_org(org_id, fields):
    """Patch whitelisted org fields (name/description/status/theme). Theme is sanitized.
    Returns matched count > 0."""
    allowed = {k: v for k, v in fields.items() if k in ("name", "description", "status", "theme")}
    if "theme" in allowed:
        allowed["theme"] = sanitize_theme(allowed["theme"])
    if not allowed:
        return False
    res = mongo.db.organizations.update_one({"_id": _oid(org_id)}, {"$set": allowed})
    return res.matched_count > 0


def find_by_slug(slug):
    return mongo.db.organizations.find_one({"slug": slug})


def is_suspended(org_id):
    """True when the org exists and is suspended. A missing org_id (legacy/global
    resource) is never 'suspended', so callers can guard writes/scans uniformly."""
    if not org_id:
        return False
    org = find_by_id(org_id)
    return bool(org and org.get("status") == "suspended")


def all_orgs():
    return list(mongo.db.organizations.find().sort("created_at", 1))


def bootstrap_org_id():
    """The earliest-created org, as a string id, or None if no org exists yet.

    Used as a deterministic, non-hardcoded fallback when a write needs an org and
    the actor has no membership to resolve one from (e.g. a super_admin creating an
    event before org self-service exists). Never special-cases a brand by name.
    """
    doc = mongo.db.organizations.find_one({}, sort=[("created_at", 1)])
    return str(doc["_id"]) if doc else None


def public_org(org):
    """Minimal, additive org metadata for payloads. Never leaks internal fields."""
    if not org:
        return None
    return {
        "id": str(org["_id"]),
        "name": org.get("name", ""),
        "slug": org.get("slug", ""),
        "theme": {**_THEME_SHAPE, **(org.get("theme") or {})},
    }
