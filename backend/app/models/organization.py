from datetime import datetime, timezone

from bson import ObjectId

from app import mongo


# An organization is a tenant. Events (and, transitively, their badges and
# redemptions) hang off an org. Attendee accounts stay platform-level, so they are
# NOT modelled here — org membership for staff/admins lives in `memberships`.
#
# `theme` is intentionally an empty object for now: Phase 1 only fixes its SHAPE.
# Per-org theme values are deferred to the theming phase (P7).
_THEME_SHAPE = {}


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
            "theme": dict(theme) if isinstance(theme, dict) else dict(_THEME_SHAPE),
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


def find_by_slug(slug):
    return mongo.db.organizations.find_one({"slug": slug})


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
    }
