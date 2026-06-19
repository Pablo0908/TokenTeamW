# TokenTeamW — Backend (Lyfter Badge App API)

Flask + PyMongo REST API for the badge-collection app. Connects to **MongoDB Atlas**
(`beeworking` database) and serves the exact JSON contract the Vue frontend consumes.

## Stack

Flask · PyMongo · PyJWT (HS256, 8h) · bcrypt · `qrcode[pil]` · flask-cors · python-dotenv

## Layout

```
backend/
├── run.py                 # entrypoint (gunicorn run:app in prod)
├── config.py              # env-driven Config
├── seed_admin.py          # creates the first admin; --fresh wipes events/badges
├── requirements.txt
├── .env                   # secrets (gitignored — copy from .env.example)
└── app/
    ├── __init__.py        # app factory: Atlas connect (fail-fast), CORS, indexes, blueprints
    ├── routes/            # auth.py · events.py · badges.py · redemptions.py · admin.py
    ├── models/            # user.py · event.py · badge.py · redemption.py
    └── utils/             # auth.py (JWT + bcrypt + decorators) · qr.py (token + QR PNG)
```

> `admin.py` is an addition to the prescribed route set: it groups every admin operation
> (event/badge creation, badge stats, **and the new user-management endpoints**) in one place.

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate            # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
copy .env.example .env            # then fill in MONGO_URI + secrets
```

**Atlas:** add your machine's public IP to **Atlas → Network Access → IP Access List**
(or `0.0.0.0/0` for the hackathon). Without this the TLS handshake is refused
(`TLSV1_ALERT_INTERNAL_ERROR`) and the app exits on startup by design — it never falls
back to a local DB.

## Run

```bash
python seed_admin.py              # create the admin account (idempotent)
python run.py                     # dev server on http://localhost:5000
# health check:
curl http://localhost:5000/health
```

Default admin (override in `.env`): **admin@lyfter.cc / Admin123!**

The app starts with **no events and no badges** — admins create them in-app. Attendees
self-register (role is always forced to `attendee` server-side).

To reset to a clean launch state at any time: `python seed_admin.py --fresh`
(clears events/badges/redemptions, keeps users). Full integration check: `python _livetest.py`.

## API

Base URL = `VITE_API_URL` (no `/api` prefix). All errors are `{"error": "..."}`.

| Method | Route | Auth | Notes |
|---|---|---|---|
| POST | `/auth/register` | public | `{name, lastname?, email, password}` → `{message, user_id}` |
| POST | `/auth/login` | public | → `{token, role, user}` |
| GET | `/events/` | JWT | all events with per-user `badges_earned`/`completed`/`status` |
| GET | `/events/<id>` | JWT | event detail + `badges[]` with `earned` flags |
| GET | `/me/badges` | JWT | events grouped, with progress + prize |
| GET | `/redeem/<event_id>/<token>` | JWT | redeem a badge (409 duplicate · 403 invalid/inactive) |
| POST | `/admin/event` | admin | create event |
| POST | `/admin/events/<id>/badge` | admin | create badge → generates UUID token + QR (`qr_url`, `qr_image`) |
| GET | `/admin/events/<id>/badges` | admin | badges with live `redeemed_by`/`total_attendees` |
| GET | `/admin/users` | admin | **all users with `badges_count`** (badge tracking) |
| PATCH | `/admin/users/<id>/role` | admin | **promote/demote** (`{role: "admin"\|"attendee"}`) |
| GET | `/health` | public | keepalive ping |

**QR strategy:** each badge gets a UUID `token`; the QR encodes
`{FRONTEND_URL}/redeem/<event_id>/<token>`. The PNG is generated server-side
(`qrcode[pil]`, error-correction H) and stored as a base64 data URL on the badge.
Set `FRONTEND_URL` to the production Vercel URL **before** generating QR codes for the event.

**Duplicate prevention:** a compound unique index on `redemptions (badge_id, user_id)`
blocks double redemption at the DB level (race-safe), returning `409`.

## Connecting the frontend

The frontend defaults to demo mode. To talk to this API, set in `frontend/.env`:
`VITE_USE_MOCK=false` and `VITE_API_URL=http://localhost:5000` (or the Render URL).

## Deploy (Render)

Build: `pip install -r requirements.txt` · Start: `gunicorn run:app` · set env vars
(`MONGO_URI`, `JWT_SECRET`, `SECRET_KEY`, `FRONTEND_URL`, `DB_NAME`) in the dashboard.
