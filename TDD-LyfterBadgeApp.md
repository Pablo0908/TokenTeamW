# Technical Design Document — Lyfter Badge App

**Version:** 1.0  
**Date:** 2026-06-09  
**Project:** Lyfter Badge App  
**Author:** Senior Software Architect

---

> **Note:** This document is a reference guide, not a strict specification. The team is not expected to follow it exactly — use it to understand the intended architecture, key flows, and design decisions. Adapt, simplify, or deviate as needed during implementation. When in doubt, prioritize what works over what's written here.

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Backend** | Flask, JWT, MongoDB, PyMongo |
| **Frontend** | Vue.js, Tailwind CSS, DaisyUI, CSS |
| **Deploy** | Render (backend), Vercel (frontend), GitHub |

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [MongoDB Data Models](#2-mongodb-data-models)
3. [Backend Design (Flask)](#3-backend-design-flask)
4. [Frontend Design (Vue.js)](#4-frontend-design-vuejs)
5. [Key Flows](#5-key-flows)
6. [Environment Variables](#6-environment-variables)
7. [Deploy Checklist](#7-deploy-checklist)
8. [Development Timeline Alignment](#8-development-timeline-alignment)

---

## 1. System Architecture

### 1.1 High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│                                                                 │
│   ┌──────────────┐    ┌──────────────┐    ┌─────────────────┐  │
│   │  Admin Views │    │  Participant │    │   Public QR     │  │
│   │  (Vue.js)    │    │  Views       │    │   Scan Page     │  │
│   └──────┬───────┘    └──────┬───────┘    └────────┬────────┘  │
│          └──────────────────┴──────────────────────┘           │
│                              │ HTTPS / Axios                    │
│                    (JWT in Authorization header)                │
└──────────────────────────────┼──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API LAYER (Render)                      │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    Flask Application                    │   │
│   │                                                         │   │
│   │  ┌────────────┐  ┌────────────┐  ┌──────────────────┐  │   │
│   │  │  /auth     │  │  /events   │  │  /admin          │  │   │
│   │  │  routes    │  │  routes    │  │  routes          │  │   │
│   │  └─────┬──────┘  └─────┬──────┘  └────────┬─────────┘  │   │
│   │        └───────────────┴──────────────────┘             │   │
│   │                        │                                │   │
│   │              ┌─────────▼─────────┐                      │   │
│   │              │  Business Logic   │                      │   │
│   │              │  (models + utils) │                      │   │
│   │              └─────────┬─────────┘                      │   │
│   │                        │                                │   │
│   │              ┌─────────▼─────────┐                      │   │
│   │              │  JWT Middleware   │                      │   │
│   │              │  + CORS Handler   │                      │   │
│   │              └───────────────────┘                      │   │
│   └─────────────────────────────────────────────────────────┘   │
└──────────────────────────────┼──────────────────────────────────┘
                               │ PyMongo
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER (MongoDB Atlas)                 │
│                                                                 │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│   │  users   │  │  events  │  │  badges  │  │ redemptions  │  │
│   └──────────┘  └──────────┘  └──────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      STORAGE (QR Images)                        │
│                                                                 │
│   ⚠️ Option A: Cloudinary (recommended — free tier, CDN)        │
│   Option B: Serve static files from Flask /static/qr/          │
│   Option C: AWS S3 (overkill for MVP)                          │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Separation of Concerns

| Layer | Responsibility | Location |
|---|---|---|
| Routes | HTTP request/response, param validation | `app/routes/` |
| Models | DB queries, data shaping, business rules | `app/models/` |
| Utils | QR generation, JWT helpers, decorators | `app/utils/` |
| Config | Env vars, DB connection, app factory | `config.py` |

### 1.3 JWT Auth Flow

```
Client                        Flask                         MongoDB
  │                             │                              │
  │── POST /auth/login ────────►│                              │
  │   {email, password}         │── find_one({email}) ────────►│
  │                             │◄─ user document ─────────────│
  │                             │   bcrypt.verify(password)    │
  │                             │   jwt.encode({               │
  │                             │     sub: user_id,            │
  │                             │     role: "admin|participant",│
  │                             │     exp: now + 24h           │
  │                             │   }, SECRET_KEY)             │
  │◄── {token: "eyJ..."} ───────│                              │
  │                             │                              │
  │── GET /me/badges ──────────►│                              │
  │   Authorization:            │   @require_auth decorator    │
  │   Bearer eyJ...             │   jwt.decode(token)          │
  │                             │   → attach user to g.user    │
  │                             │── query redemptions ────────►│
  │◄── {badges: [...]} ─────────│◄─ results ───────────────────│
```

**Role enforcement:** Two decorators — `@require_auth` (any valid JWT) and `@require_admin` (validates `g.user["role"] == "admin"`). Both return `401` on missing/expired token and `403` on role mismatch.

---

## 2. MongoDB Data Models

### 2.1 Collection: `users`

```python
{
    "_id":             ObjectId,          # auto-generated
    "name":            str,               # display name
    "email":           str,               # unique, indexed
    "hashed_password": str,               # bcrypt hash
    "role":            str,               # "admin" | "participant"
    "created_at":      datetime           # UTC
}
```

**Indexes:**
```python
db.users.create_index("email", unique=True)
```

---

### 2.2 Collection: `events`

```python
{
    "_id":         ObjectId,
    "name":        str,               # event title
    "description": str,
    "start_date":  datetime,          # UTC
    "end_date":    datetime,          # UTC
    "prize":       str,               # prize description or URL
    "created_by":  ObjectId,          # ref → users._id
    "created_at":  datetime           # UTC
}
```

**Indexes:**
```python
db.events.create_index("created_by")
db.events.create_index([("start_date", 1), ("end_date", 1)])  # active events filter
```

---

### 2.3 Collection: `badges`

```python
{
    "_id":         ObjectId,
    "event_id":    ObjectId,          # ref → events._id
    "name":        str,               # badge display name
    "description": str,
    "token":       str,               # UUID4, unique — embedded in QR URL
    "qr_image_url":str,               # URL to stored QR image
    "created_at":  datetime           # UTC
}
```

**Indexes:**
```python
db.badges.create_index("event_id")
db.badges.create_index("token", unique=True)
```

---

### 2.4 Collection: `redemptions`

```python
{
    "_id":         ObjectId,
    "badge_id":    ObjectId,          # ref → badges._id
    "event_id":    ObjectId,          # denormalized for fast grouping
    "user_id":     ObjectId,          # ref → users._id
    "redeemed_at": datetime           # UTC
}
```

**Indexes:**
```python
db.redemptions.create_index([("user_id", 1), ("event_id", 1)])
db.redemptions.create_index([("badge_id", 1), ("user_id", 1)], unique=True)  # prevent duplicates
```

> The compound unique index on `(badge_id, user_id)` is the critical safeguard — it prevents double redemption at the DB level even under race conditions.

---

## 3. Backend Design (Flask)

### 3.1 Folder Structure

```
backend/
├── run.py                  # entry point: creates and runs app
├── config.py               # Config class, loads .env
├── requirements.txt
├── .env
└── app/
    ├── __init__.py         # app factory: create_app()
    ├── routes/
    │   ├── __init__.py
    │   ├── auth.py         # /auth/register, /auth/login
    │   ├── events.py       # /events/, /events/<id>
    │   ├── participant.py  # /me/badges, /redeem/<event_id>/<token>
    │   └── admin.py        # /admin/event, /admin/events/<id>/badge, etc.
    ├── models/
    │   ├── __init__.py
    │   ├── user.py         # UserModel: find_by_email, create, etc.
    │   ├── event.py        # EventModel: create, find_active, etc.
    │   ├── badge.py        # BadgeModel: create, find_by_event, etc.
    │   └── redemption.py   # RedemptionModel: redeem, get_by_user, etc.
    └── utils/
        ├── __init__.py
        ├── auth.py         # JWT encode/decode, decorators
        ├── qr.py           # QR generation, upload
        └── db.py           # PyMongo client singleton
```

---

### 3.2 Endpoint Specifications

#### `POST /auth/register`

| Field | Value |
|---|---|
| Auth | None (public) |
| Body | `{ "name": str, "email": str, "password": str, "role": "participant" }` |
| Response 201 | `{ "message": "User created", "user_id": str }` |
| Error 400 | `{ "error": "Email already registered" }` |

> ⚠️ `role` should default to `"participant"` on the backend — never trust client-sent role values. Admin accounts should be created via a separate seeding script or a protected endpoint.

---

#### `POST /auth/login`

| Field | Value |
|---|---|
| Auth | None (public) |
| Body | `{ "email": str, "password": str }` |
| Response 200 | `{ "token": "eyJ...", "role": str, "name": str }` |
| Error 401 | `{ "error": "Invalid credentials" }` |

---

#### `GET /events/`

| Field | Value |
|---|---|
| Auth | JWT required (any role) |
| Params | None |
| Response 200 | `{ "events": [ { "id": str, "name": str, "description": str, "start_date": str, "end_date": str, "badge_count": int } ] }` |
| Notes | Returns only events where `end_date >= today` |

---

#### `GET /events/<id>`

| Field | Value |
|---|---|
| Auth | JWT required |
| Response 200 | `{ "id": str, "name": str, "description": str, "prize": str, "badges": [ { "id": str, "name": str, "description": str } ], "redeemed_badge_ids": [str] }` |
| Error 404 | `{ "error": "Event not found" }` |
| Notes | `redeemed_badge_ids` is populated from the authenticated user's redemptions |

---

#### `GET /me/badges`

| Field | Value |
|---|---|
| Auth | JWT required (participant) |
| Response 200 | `{ "events": [ { "event_id": str, "event_name": str, "total_badges": int, "redeemed": int, "prize": str, "prize_unlocked": bool, "badges": [ { "badge_id": str, "name": str, "redeemed_at": str \| null } ] } ] }` |

---

#### `GET /redeem/<event_id>/<token>`

| Field | Value |
|---|---|
| Auth | JWT required |
| Params | `event_id` (path), `token` (path, UUID) |
| Response 200 | `{ "message": "Badge redeemed", "badge": { "name": str }, "prize_unlocked": bool, "prize": str \| null }` |
| Error 404 | `{ "error": "Badge not found" }` |
| Error 409 | `{ "error": "Already redeemed" }` |
| Notes | Completion check: `redemptions.count(user_id, event_id) == badges.count(event_id)` |

---

#### `POST /admin/event`

| Field | Value |
|---|---|
| Auth | JWT required, role = admin |
| Body | `{ "name": str, "description": str, "start_date": str (ISO), "end_date": str (ISO), "prize": str }` |
| Response 201 | `{ "event_id": str }` |

---

#### `POST /admin/events/<id>/badge`

| Field | Value |
|---|---|
| Auth | JWT required, role = admin |
| Body | `{ "name": str, "description": str }` |
| Response 201 | `{ "badge_id": str, "token": str, "qr_image_url": str }` |
| Notes | Backend auto-generates UUID token and QR image; client sends only name + description |

---

#### `GET /admin/events/<id>/badges`

| Field | Value |
|---|---|
| Auth | JWT required, role = admin |
| Response 200 | `{ "badges": [ { "id": str, "name": str, "token": str, "qr_image_url": str, "redemption_count": int } ] }` |

---

### 3.3 JWT Middleware

```python
# app/utils/auth.py

from functools import wraps
from flask import request, g, jsonify
import jwt, os

def decode_token(token):
    return jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing token"}), 401
        try:
            payload = decode_token(auth_header.split(" ")[1])
            g.user = payload          # { sub, role, exp }
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    @require_auth
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.user.get("role") != "admin":
            return jsonify({"error": "Forbidden"}), 403
        return f(*args, **kwargs)
    return decorated
```

---

### 3.4 QR Generation Utility

**Library:** `qrcode[pil]` + `Pillow`

```python
# app/utils/qr.py

import qrcode, uuid, os
from io import BytesIO

def generate_badge_token():
    return str(uuid.uuid4())

def generate_qr_image(event_id: str, token: str) -> bytes:
    base_url = os.getenv("FRONTEND_URL")
    qr_url = f"{base_url}/redeem/{event_id}/{token}"
    img = qrcode.make(qr_url)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
```

**Storage strategy:**

```
⚠️ Two valid options — pick one before Week 2:

Option A (Recommended — Cloudinary):
  - upload_result = cloudinary.uploader.upload(image_bytes)
  - store upload_result["secure_url"] in badges.qr_image_url
  - Pros: CDN, persistent, free tier sufficient for MVP
  - Cons: extra dependency, Cloudinary account needed

Option B (Flask static files):
  - Save PNG to /app/static/qr/<token>.png
  - qr_image_url = f"{API_URL}/static/qr/{token}.png"
  - Pros: zero external services
  - Cons: ephemeral on Render free tier (disk resets on redeploy)
```

---

### 3.5 Error Handling Convention

All errors return JSON with a consistent shape:

```json
{
  "error": "Human-readable message"
}
```

| Scenario | Status Code |
|---|---|
| Missing/invalid request body | 400 |
| Invalid credentials | 401 |
| Missing or expired JWT | 401 |
| Insufficient role | 403 |
| Resource not found | 404 |
| Duplicate (already redeemed) | 409 |
| Unhandled server error | 500 |

Register a global 500 handler in `create_app()`:

```python
@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"error": "Internal server error"}), 500
```

---

## 4. Frontend Design (Vue.js)

> **Styling:** Uses **Tailwind CSS** for utility classes and **DaisyUI** as the component layer on top of Tailwind. Custom CSS is used where DaisyUI components don't cover the need.

### 4.1 Folder Structure

```
frontend/
├── index.html
├── vite.config.js
├── tailwind.config.js        # Tailwind + DaisyUI plugin config
├── .env
├── .env.production
└── src/
    ├── main.js               # app init, router, state store
    ├── App.vue
    ├── assets/
    │   └── main.css          # Tailwind directives (@tailwind base/components/utilities)
    ├── api/
    │   ├── axios.js          # Axios instance + interceptor
    │   ├── auth.js           # login(), register()
    │   ├── events.js         # getEvents(), getEvent()
    │   ├── badges.js         # getMyBadges(), redeemBadge()
    │   └── admin.js          # createEvent(), createBadge(), getAdminBadges()
    ├── router/
    │   └── index.js          # route definitions + navigation guards
    ├── store/
    │   ├── auth.js           # user, token, login(), logout()
    │   └── events.js         # events cache
    ├── views/
    │   ├── public/
    │   │   ├── LoginView.vue
    │   │   ├── RegisterView.vue
    │   │   └── RedeemView.vue     # /redeem/:event_id/:token
    │   ├── participant/
    │   │   ├── EventListView.vue
    │   │   ├── EventDetailView.vue
    │   │   └── BadgeProfileView.vue
    │   └── admin/
    │       ├── AdminEventCreateView.vue
    │       ├── AdminBadgeCreateView.vue
    │       └── AdminBadgeListView.vue
    └── components/
        ├── NavBar.vue
        ├── BadgeCard.vue
        ├── ProgressBar.vue
        ├── QRCard.vue
        └── PrizeReveal.vue
```

---

### 4.2 Route Map

```javascript
// src/router/index.js

const routes = [
  // --- PUBLIC ---
  { path: "/login",                   component: LoginView,            meta: { public: true } },
  { path: "/register",                component: RegisterView,         meta: { public: true } },
  { path: "/redeem/:event_id/:token", component: RedeemView,           meta: { requiresAuth: true } },

  // --- PARTICIPANT ---
  { path: "/events",                  component: EventListView,        meta: { requiresAuth: true } },
  { path: "/events/:id",              component: EventDetailView,      meta: { requiresAuth: true } },
  { path: "/me/badges",               component: BadgeProfileView,     meta: { requiresAuth: true } },

  // --- ADMIN ---
  { path: "/admin/events/create",     component: AdminEventCreateView, meta: { requiresAuth: true, role: "admin" } },
  { path: "/admin/events/:id/badges", component: AdminBadgeListView,   meta: { requiresAuth: true, role: "admin" } },
  { path: "/admin/events/:id/badge/create", component: AdminBadgeCreateView, meta: { requiresAuth: true, role: "admin" } },

  // Fallback
  { path: "/", redirect: "/events" },
  { path: "/:pathMatch(.*)*", redirect: "/events" }
]
```

**Navigation guard:**

```javascript
router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.public) return next()
  if (!auth.token) return next("/login")
  if (to.meta.role && auth.user?.role !== to.meta.role) return next("/events")
  next()
})
```

---

### 4.3 Axios Interceptor

```javascript
// src/api/axios.js

import axios from "axios"
import { useAuthStore } from "@/store/auth"

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
})

api.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      useAuthStore().logout()       // clear token + redirect to /login
    }
    return Promise.reject(err)
  }
)

export default api
```

---

### 4.4 State Management

> Use whatever state management approach fits your team — Pinia, Vuex, or simple reactive composables. The example below uses Pinia as a reference.

```javascript
// src/store/auth.js

import { defineStore } from "pinia"
import { useRouter } from "vue-router"

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: localStorage.getItem("token") || null,
    user:  JSON.parse(localStorage.getItem("user") || "null"),
  }),
  actions: {
    login(token, user) {
      this.token = token
      this.user  = user
      localStorage.setItem("token", token)
      localStorage.setItem("user", JSON.stringify(user))
    },
    logout() {
      this.token = null
      this.user  = null
      localStorage.removeItem("token")
      localStorage.removeItem("user")
      useRouter().push("/login")
    },
  },
})
```

> ⚠️ `localStorage` is sufficient for an MVP. For higher security, consider `httpOnly` cookies — but this requires backend session support and CORS credential handling, which adds complexity.

---

### 4.5 Key View Behaviors

| View | Key Behavior |
|---|---|
| `LoginView` | POST /auth/login → store token + role → redirect by role |
| `RegisterView` | POST /auth/register → auto-login or redirect to /login |
| `EventListView` | GET /events/ → display cards with badge count |
| `EventDetailView` | GET /events/:id → badges grid with redeemed state overlaid |
| `BadgeProfileView` | GET /me/badges → per-event sections with `<ProgressBar>` |
| `RedeemView` | Calls GET /redeem/:event_id/:token on mount → shows result or error. If prize unlocked, renders `<PrizeReveal>` |
| `AdminEventCreateView` | Form → POST /admin/event → redirect to badge list |
| `AdminBadgeCreateView` | Form → POST /admin/events/:id/badge → shows QR image inline |
| `AdminBadgeListView` | GET /admin/events/:id/badges → table with QR thumbnails + download links + redemption counts |

---

## 5. Key Flows

### Flow 1 — Admin Creates Event and Badge

```
1.  Admin fills EventCreate form (name, description, dates, prize)
2.  Frontend → POST /admin/event {name, description, start_date, end_date, prize}
3.  Flask: @require_admin validates JWT role
4.  EventModel.create() inserts document into `events`, returns event_id
5.  Flask → 201 {event_id}
6.  Frontend navigates to /admin/events/:id/badge/create

7.  Admin fills BadgeCreate form (name, description)
8.  Frontend → POST /admin/events/:id/badge {name, description}
9.  Flask: generate_badge_token() → UUID4 token
10. generate_qr_image(event_id, token) → PNG bytes
11. Upload PNG to Cloudinary → qr_image_url
12. BadgeModel.create() inserts {event_id, name, description, token, qr_image_url} into `badges`
13. Flask → 201 {badge_id, token, qr_image_url}
14. Frontend renders QR image inline with a download button
```

---

### Flow 2 — Participant Scans QR → Badge Redeemed → Prize Check

```
1.  Participant points phone camera at printed QR code
2.  QR encodes: https://lyfter-badges.vercel.app/redeem/{event_id}/{token}
3.  Browser opens RedeemView — Vue router extracts params
4.  RedeemView.onMounted() → GET /redeem/{event_id}/{token}
    (JWT sent via Axios interceptor — user must be logged in)
5.  Flask: lookup badge by token + event_id → 404 if not found
6.  Check redemptions for (badge_id, user_id) unique index → 409 if duplicate
7.  RedemptionModel.create() inserts redemption document
8.  Completion check:
      total  = badges.count_documents({event_id})
      earned = redemptions.count_documents({user_id, event_id})
      prize_unlocked = (earned == total)
9.  Flask → 200 {message, badge.name, prize_unlocked, prize (if unlocked)}
10. RedeemView displays:
      - Success toast with badge name
      - If prize_unlocked: <PrizeReveal> component animates prize reveal
      - Link to /me/badges to see full progress
```

---

### Flow 3 — Participant Views Badge Profile

```
1.  Participant navigates to /me/badges
2.  Frontend → GET /me/badges
3.  Flask: g.user.sub → query redemptions WHERE user_id = g.user.sub
4.  Group redemptions by event_id
5.  For each event_id:
      a. Fetch event document (name, prize)
      b. Fetch all badges for event (total_badges)
      c. Map redeemed badge_ids from redemptions
      d. Compute prize_unlocked = (redeemed == total)
6.  Flask → 200 {events: [...]}
7.  BadgeProfileView renders one section per event:
      - Event name + date range
      - <ProgressBar :value="redeemed" :max="total" />
      - Grid of <BadgeCard> — greyed out if not yet redeemed
      - Prize banner if prize_unlocked == true
```

---

## 6. Environment Variables

### Backend (`.env`)

```bash
# Flask
FLASK_ENV=development           # "production" on Render
SECRET_KEY=your-flask-secret    # used by Flask session (keep random)

# JWT
JWT_SECRET=your-jwt-secret      # strong random string, never expose

# MongoDB
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/lyfter_badges

# CORS
FRONTEND_URL=http://localhost:5173   # Vercel URL in production

# QR Storage (if using Cloudinary)
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

### Frontend (`.env` / `.env.production`)

```bash
# .env (local dev)
VITE_API_URL=http://localhost:5000

# .env.production (Vercel)
VITE_API_URL=https://lyfter-badges-api.onrender.com
```

> ⚠️ Never commit `.env` files. Add them to `.gitignore`. Set all variables as environment variables in the Render and Vercel dashboards.

---

## 7. Deploy Checklist

### 7.1 Backend → Render

```
1. Push backend code to GitHub (separate repo or /backend subfolder)

2. Create new Render Web Service:
   - Environment: Python 3
   - Build command: pip install -r requirements.txt
   - Start command: gunicorn run:app
   - Add gunicorn to requirements.txt

3. Set environment variables in Render dashboard:
   FLASK_ENV=production
   SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
   JWT_SECRET=<generate same way>
   MONGO_URI=<MongoDB Atlas connection string>
   FRONTEND_URL=https://your-app.vercel.app
   CLOUDINARY_* (if using Cloudinary)

4. MongoDB Atlas:
   - Create free M0 cluster
   - Add Render's outbound IP to Atlas Network Access (or allow 0.0.0.0/0 for MVP)
   - Create DB user with readWrite on lyfter_badges database
   - Copy SRV connection string → MONGO_URI

5. Test deployed API:
   curl https://lyfter-badges-api.onrender.com/auth/login \
     -d '{"email":"test@test.com","password":"test"}' \
     -H "Content-Type: application/json"

6. Verify QR URLs:
   - QR must encode production Vercel URL, not localhost
   - FRONTEND_URL env var controls this — set before generating any QR
```

### 7.2 Frontend → Vercel

```
1. Push frontend code to GitHub

2. Import project in Vercel dashboard:
   - Framework preset: Vite
   - Build command: npm run build
   - Output directory: dist

3. Set environment variable:
   VITE_API_URL=https://lyfter-badges-api.onrender.com

4. Configure SPA routing (prevent 404 on reload):
   Create vercel.json in frontend root:

   {
     "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
   }

5. Deploy and test full flow:
   - Register as participant
   - Log in as admin, create event + badge
   - Download QR and scan with phone
   - Verify redemption registers and prize check works
```

> ⚠️ Render free tier spins down after 15 minutes of inactivity. First request after sleep takes ~30s. Upgrade to a paid instance or use a cron ping service (e.g., UptimeRobot) if this affects the demo.

---

## 8. Development Timeline Alignment

### Week 1 — Study and Setup

| Day | Focus | TDD Sections |
|---|---|---|
| Mon | Read full TDD, understand all flows | All sections |
| Tue | Set up MongoDB Atlas, study data models | §2 |
| Tue | Set up Flask project structure, connect PyMongo | §3.1, §6 |
| Wed | Study JWT auth flow, implement `require_auth`/`require_admin` | §1.3, §3.3 |
| Thu | Set up Vue project, Pinia, Axios interceptor, router guards | §4.1–4.3 |
| Fri | Test backend skeleton (health check, DB ping), commit structure | §3.5 |

---

### Week 2 — Core Implementation

| Day | Focus | Endpoints / Views |
|---|---|---|
| Mon | Auth backend: register + login | `POST /auth/register`, `POST /auth/login` |
| Mon | Auth frontend: Login + Register views, store token | `LoginView`, `RegisterView`, `store/auth.js` |
| Tue | Events backend: list + detail | `GET /events/`, `GET /events/<id>` |
| Tue | Events frontend: EventList + EventDetail views | `EventListView`, `EventDetailView` |
| Wed | Badge creation backend: token + QR generation | `POST /admin/events/<id>/badge` |
| Wed | Admin frontend: AdminBadgeCreate, render QR inline | `AdminBadgeCreateView` |
| Thu | Redemption backend: QR scan flow, duplicate guard, prize check | `GET /redeem/<event_id>/<token>` |
| Thu | Redeem frontend: RedeemView, PrizeReveal component | `RedeemView`, `PrizeReveal.vue` |
| Fri | Profile backend + frontend: badges grouped by event | `GET /me/badges`, `BadgeProfileView` |

---

### Week 3 — Admin Panel, Polish, Deploy

| Day | Focus |
|---|---|
| Mon | Admin event create flow end-to-end: `POST /admin/event`, `AdminEventCreateView` |
| Mon | Admin badge list: `GET /admin/events/<id>/badges`, `AdminBadgeListView` with QR download |
| Tue | UI polish: NavBar, ProgressBar, BadgeCard redeemed state, loading states |
| Tue | Error handling: toast notifications, 401 redirect, 409 duplicate message |
| Wed | Deploy backend to Render, set all env vars, test API live |
| Wed | Deploy frontend to Vercel, configure `vercel.json`, set `VITE_API_URL` |
| Thu | End-to-end test on production: create event → scan QR on phone → prize reveal |
| Thu | Fix any prod-only issues (CORS, QR URL pointing to wrong domain) |
| Fri | Buffer: final fixes, demo prep, documentation |

---

*End of Technical Design Document — Lyfter Badge App v1.0*
