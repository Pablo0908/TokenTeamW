from datetime import datetime, timedelta, timezone

from bson import ObjectId

from app import mongo

# Shared, date-range-aware aggregation layer for the analytics surfaces (platform
# insights + org attendee insights). Reuses the $dateTrunc + $group idiom established in
# redemption.scans_over_time / audit.activity_buckets so every view computes the same way.

_UNITS = ("day", "week", "month")
DEFAULT_WINDOW_DAYS = 30


def _oid(value):
    return value if isinstance(value, ObjectId) else ObjectId(value)


def _parse_dt(value):
    """Accept an ISO date/datetime string -> aware UTC datetime, or None."""
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def parse_range(args, now=None):
    """Resolve (period, start, end) from request args.
      period: 'day' | 'week' | 'month'  (bucket granularity; default 'day')
      start/end: ISO dates; default = last DEFAULT_WINDOW_DAYS ending now.
    `args` is a Mapping (request.args). `now` is injectable for tests."""
    now = now or datetime.now(timezone.utc)
    period = args.get("period", "day")
    if period not in _UNITS:
        period = "day"
    end = _parse_dt(args.get("end")) or now
    start = _parse_dt(args.get("start")) or (end - timedelta(days=DEFAULT_WINDOW_DAYS))
    if start > end:
        start, end = end, start
    return period, start, end


def _range_match(date_field, start, end, base=None):
    match = dict(base or {})
    match[date_field] = {"$gte": start, "$lte": end}
    return match


def _bucketize(cursor):
    out = []
    for doc in cursor:
        b = doc["_id"]
        out.append({"bucket": b.isoformat() if b else None, "count": doc["count"]})
    return out


def series_count(collection, date_field, period, start, end, match=None):
    """Generic per-bucket document counter over a date window. Powers scans-over-time,
    signups/user-growth, etc. Returns [{bucket, count}] oldest->newest."""
    pipeline = [
        {"$match": _range_match(date_field, start, end, match)},
        {"$group": {"_id": {"$dateTrunc": {"date": f"${date_field}", "unit": period}}, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    return _bucketize(mongo.db[collection].aggregate(pipeline))


def active_users(period, start, end, org_id=None):
    """Distinct interacting actors per bucket from audit_log (DAU/MAU-style). Counts each
    actor once per bucket. Optionally scoped to one org. [{bucket, count}] oldest->newest.
    NOTE: only accrues from when audit interaction logging began — not reconstructable."""
    base = {"actor_id": {"$ne": None}}
    if org_id:
        base["org_id"] = str(org_id)
    pipeline = [
        {"$match": _range_match("ts", start, end, base)},
        {"$group": {"_id": {"$dateTrunc": {"date": "$ts", "unit": period}}, "actors": {"$addToSet": "$actor_id"}}},
        {"$project": {"count": {"$size": "$actors"}}},
        {"$sort": {"_id": 1}},
    ]
    return _bucketize(mongo.db.audit_log.aggregate(pipeline))


def window_counts(org_id, start, end):
    """{scans, unique_participants} for an org's redemptions inside [start, end] — the
    building block for period-over-period deltas. Two cheap aggregations, no join."""
    match = _range_match("redeemed_at", start, end, {"org_id": _oid(org_id)})
    scans = mongo.db.redemptions.count_documents(match)
    pipeline = [{"$match": match}, {"$group": {"_id": "$user_id"}}, {"$count": "n"}]
    res = list(mongo.db.redemptions.aggregate(pipeline))
    unique = res[0]["n"] if res else 0
    return {"scans": scans, "unique_participants": unique}


def platform_totals():
    """Headline platform counts (all-time): scans, events, orgs, users."""
    return {
        "scans": mongo.db.redemptions.count_documents({}),
        "events": mongo.db.events.count_documents({}),
        "orgs": mongo.db.organizations.count_documents({}),
        "users": mongo.db.users.count_documents({}),
    }


def org_leaderboard(start, end, limit=10):
    """Top orgs by scans in [start, end]: [{id, name, scans, participants}], busiest first."""
    pipeline = [
        {"$match": _range_match("redeemed_at", start, end, {"org_id": {"$ne": None}})},
        {"$group": {"_id": "$org_id", "scans": {"$sum": 1}, "users": {"$addToSet": "$user_id"}}},
        {"$project": {"scans": 1, "participants": {"$size": "$users"}}},
        {"$sort": {"scans": -1}},
        {"$limit": limit},
        {"$lookup": {"from": "organizations", "localField": "_id", "foreignField": "_id", "as": "org"}},
        {"$unwind": "$org"},
    ]
    return [{"id": str(d["_id"]), "name": d["org"].get("name", ""),
             "scans": d["scans"], "participants": d["participants"]}
            for d in mongo.db.redemptions.aggregate(pipeline)]


def event_type_mix(start, end, org_id=None):
    """Scans grouped by the joined event's type in [start, end]: [{event_type, count}].
    Platform-wide by default; scoped to one org when org_id is given."""
    base = {"org_id": _oid(org_id)} if org_id else {}
    pipeline = [
        {"$match": _range_match("redeemed_at", start, end, base)},
        {"$lookup": {"from": "events", "localField": "event_id", "foreignField": "_id", "as": "ev"}},
        {"$unwind": "$ev"},
        {"$group": {"_id": "$ev.event_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    return [{"event_type": d["_id"] or "uncategorized", "count": d["count"]}
            for d in mongo.db.redemptions.aggregate(pipeline)]


def pct_delta(current, previous):
    """Percentage change current vs previous, rounded. None when there's no prior baseline
    (avoids a misleading +100%/inf when previous is 0)."""
    if not previous:
        return None
    return round((current - previous) / previous * 100, 1)


# --- Org attendee insights (Phase I) ---

def new_vs_returning(org_id, start, end):
    """Among attendees with ≥1 scan in [start, end]: how many are NEW to the org (their
    first-ever org scan falls in the window) vs RETURNING (first scan predates it).
    One aggregation. Returns {new, returning}."""
    oid = _oid(org_id)
    pipeline = [
        {"$match": {"org_id": oid}},
        {"$group": {
            "_id": "$user_id",
            "first": {"$min": "$redeemed_at"},
            "in_range": {"$max": {"$cond": [
                {"$and": [{"$gte": ["$redeemed_at", start]}, {"$lte": ["$redeemed_at", end]}]}, 1, 0]}},
        }},
        {"$match": {"in_range": 1}},
        {"$group": {
            "_id": None,
            "new": {"$sum": {"$cond": [{"$gte": ["$first", start]}, 1, 0]}},
            "returning": {"$sum": {"$cond": [{"$lt": ["$first", start]}, 1, 0]}},
        }},
    ]
    res = list(mongo.db.redemptions.aggregate(pipeline))
    return {"new": res[0]["new"], "returning": res[0]["returning"]} if res else {"new": 0, "returning": 0}


def new_attendees_series(org_id, period, start, end):
    """Acquisition trend: count of attendees whose FIRST-ever org scan lands in each bucket
    of the window. [{bucket, count}] oldest→newest."""
    oid = _oid(org_id)
    pipeline = [
        {"$match": {"org_id": oid}},
        {"$group": {"_id": "$user_id", "first": {"$min": "$redeemed_at"}}},
        {"$match": {"first": {"$gte": start, "$lte": end}}},
        {"$group": {"_id": {"$dateTrunc": {"date": "$first", "unit": period}}, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    return _bucketize(mongo.db.redemptions.aggregate(pipeline))


def org_retention(org_id):
    """Loyalty signal: share of the org's attendees who scanned across ≥2 distinct events.
    Returns {return_rate (%), attendees, repeat}."""
    oid = _oid(org_id)
    pipeline = [
        {"$match": {"org_id": oid}},
        {"$group": {"_id": "$user_id", "events": {"$addToSet": "$event_id"}}},
        {"$project": {"n": {"$size": "$events"}}},
        {"$group": {"_id": None, "attendees": {"$sum": 1},
                    "repeat": {"$sum": {"$cond": [{"$gte": ["$n", 2]}, 1, 0]}}}},
    ]
    res = list(mongo.db.redemptions.aggregate(pipeline))
    if not res:
        return {"return_rate": 0.0, "attendees": 0, "repeat": 0}
    a, r = res[0]["attendees"], res[0]["repeat"]
    return {"return_rate": round(r / a * 100, 1) if a else 0.0, "attendees": a, "repeat": r}


def event_attendance(org_id):
    """{event_id_str: distinct_attendees} across an org's events (one aggregation)."""
    oid = _oid(org_id)
    pipeline = [
        {"$match": {"org_id": oid}},
        {"$group": {"_id": "$event_id", "users": {"$addToSet": "$user_id"}}},
        {"$project": {"attendees": {"$size": "$users"}}},
    ]
    return {str(d["_id"]): d["attendees"] for d in mongo.db.redemptions.aggregate(pipeline)}
