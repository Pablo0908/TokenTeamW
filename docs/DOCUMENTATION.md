# Technical Documentation — Lyfter Badge App

## Overview

Lyfter Badge App is a web platform for managing digital badges at in-person events. Organizers create events and badges; attendees collect them by scanning QR codes on-site.

### System Actors

| Actor | Role |
|---|---|
| **Admin** | Creates events, adds badges, generates QR codes, monitors redemption status |
| **Participant** | Registers, logs in, scans QR codes to redeem badges, views their collection |
| **QR System** | Validates unique UUID tokens at scan time and records the redemption in the database |

---

## Flow Diagram

```
Admin
  │
  ├─► POST /admin/event            → Creates an event
  │
  └─► POST /admin/events/:id/badge → Generates badge + UUID + QR code
                                          │
                                          ▼
                                   [QR code printed/displayed at the event]
                                          │
                                          ▼
Attendee scans QR with their phone
  │
  └─► GET /redeem/:event_id/:token
            │
            ├─ Valid & unredeemed token → records redemption → 200 OK
            ├─ Already redeemed token   → 409 Conflict
            └─ Invalid/missing token    → 404 Not Found
```

Participant authentication flow:

```
POST /auth/register  →  create account
POST /auth/login     →  returns JWT
GET  /me/badges      →  view collection (requires JWT in header)
```

---

## Tech Stack

### Backend

| Technology | Recommended Version | Role |
|---|---|---|
| **Python** | 3.11+ | Base language |
| **Flask** | 3.x | Web framework — defines routes and business logic |
| **Flask-JWT-Extended** | 4.x | Stateless authentication with JWT tokens |
| **PyMongo** | 4.x | Official MongoDB driver |
| **MongoDB Atlas** | — | NoSQL database — stores users, events, badges, and redemptions |
| **qrcode** | 7.x | QR code generation from badge UUID |
| **Gunicorn / Eventlet** | — | WSGI server for production on Render |

### Frontend

| Technology | Recommended Version | Role |
|---|---|---|
| **Vue.js** | 3.x (Composition API) | Reactive SPA framework |
| **Vite** | 5.x | Bundler and dev server |
| **Tailwind CSS** | 3.x | Utility-first CSS |
| **DaisyUI** | 4.x | UI components on top of Tailwind |
| **Axios** | 1.x | HTTP client for API consumption |

### Infrastructure

| Service | Usage |
|---|---|
| **Render** | Flask backend deployment (web service) |
| **Vercel** | Vue frontend deployment (static site) |
| **MongoDB Atlas** | Cloud database |

---

## API Endpoints

### Authentication

| Method | Route | Role | Description |
|---|---|---|---|
| `POST` | `/auth/register` | Public | Register a new participant |
| `POST` | `/auth/login` | Public | Authenticate and return JWT |

**POST /auth/register — Request body:**
```json
{
  "name": "Franco Saenz",
  "email": "franco@lyfter.cc",
  "password": "myPassword123"
}
```

**POST /auth/register — Response 201:**
```json
{
  "message": "User registered successfully",
  "user_id": "64abc123..."
}
```

**POST /auth/login — Request body:**
```json
{
  "email": "franco@lyfter.cc",
  "password": "myPassword123"
}
```

**POST /auth/login — Response 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### Events

| Method | Route | Role | Description |
|---|---|---|---|
| `GET` | `/events/` | Public | List all active events |
| `GET` | `/events/<id>` | Public | Get a specific event's details |

**GET /events/ — Response 200:**
```json
[
  {
    "id": "64abc123...",
    "name": "Lyfter Summit 2025",
    "date": "2025-09-15",
    "location": "Buenos Aires"
  }
]
```

**GET /events/\<id\> — Response 200:**
```json
{
  "id": "64abc123...",
  "name": "Lyfter Summit 2025",
  "date": "2025-09-15",
  "location": "Buenos Aires",
  "description": "Annual technology event"
}
```

---

### Participant Badges

| Method | Route | Role | Description |
|---|---|---|---|
| `GET` | `/me/badges` | Participant (JWT) | List the user's badges grouped by event |

**GET /me/badges — Required headers:**
```
Authorization: Bearer <access_token>
```

**GET /me/badges — Response 200:**
```json
{
  "Lyfter Summit 2025": [
    {
      "badge_id": "uuid-1234...",
      "name": "Early Adopter",
      "redeemed_at": "2025-09-15T10:30:00Z"
    }
  ]
}
```

---

### QR Redemption

| Method | Route | Role | Description |
|---|---|---|---|
| `GET` | `/redeem/<event_id>/<token>` | Participant (JWT) | Scans QR, records badge redemption |

**Response 200:**
```json
{
  "message": "Badge redeemed successfully",
  "badge": {
    "name": "Early Adopter",
    "event": "Lyfter Summit 2025"
  }
}
```

**Response 409 (already redeemed):**
```json
{ "error": "This badge has already been redeemed" }
```

**Response 404 (invalid token):**
```json
{ "error": "Badge not found" }
```

---

### Admin

| Method | Route | Role | Description |
|---|---|---|---|
| `POST` | `/admin/event` | Admin (JWT) | Create a new event |
| `POST` | `/admin/events/<id>/badge` | Admin (JWT) | Add a badge to an event, generates UUID and QR |
| `GET` | `/admin/events/<id>/badges` | Admin (JWT) | List event badges with redemption status |

**POST /admin/event — Request body:**
```json
{
  "name": "Lyfter Summit 2025",
  "date": "2025-09-15",
  "location": "Buenos Aires",
  "description": "Annual technology event"
}
```

**POST /admin/events/\<id\>/badge — Request body:**
```json
{
  "name": "Early Adopter",
  "description": "First to register for the event"
}
```

**POST /admin/events/\<id\>/badge — Response 201:**
```json
{
  "badge_id": "uuid-1234...",
  "qr_url": "https://api.lyfter.cc/redeem/64abc123/uuid-1234"
}
```

**GET /admin/events/\<id\>/badges — Response 200:**
```json
[
  {
    "badge_id": "uuid-1234...",
    "name": "Early Adopter",
    "redeemed": true,
    "redeemed_by": "franco@lyfter.cc",
    "redeemed_at": "2025-09-15T10:30:00Z"
  },
  {
    "badge_id": "uuid-5678...",
    "name": "Speaker",
    "redeemed": false,
    "redeemed_by": null,
    "redeemed_at": null
  }
]
```

---

## Recommended Folder Structure

### Backend

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   ├── auth/
│   │   └── routes.py
│   ├── events/
│   │   └── routes.py
│   ├── badges/
│   │   └── routes.py
│   └── admin/
│       └── routes.py
├── requirements.txt
├── Procfile
└── .env.example
```

### Frontend

```
frontend/
├── src/
│   ├── main.js
│   ├── App.vue
│   ├── router/index.js
│   ├── stores/auth.js
│   ├── api/index.js
│   ├── components/
│   │   ├── BadgeCard.vue
│   │   ├── EventCard.vue
│   │   └── Navbar.vue
│   └── views/
│       ├── HomeView.vue
│       ├── LoginView.vue
│       ├── RegisterView.vue
│       ├── MyBadgesView.vue
│       └── admin/
│           ├── AdminDashboard.vue
│           ├── CreateEvent.vue
│           └── ManageBadges.vue
├── index.html
└── vite.config.js
```

---

## Environment Variables

### Backend (`.env`)

| Variable | Description |
|---|---|
| `MONGO_URI` | MongoDB Atlas connection URI (includes user, password, and cluster) |
| `JWT_SECRET_KEY` | Secret key for signing and verifying JWT tokens — must be long and random |
| `FLASK_ENV` | Runtime environment: `development` or `production` |
| `ADMIN_EMAIL` | Email of the user with admin role |
| `ADMIN_PASSWORD` | Admin initial password (seed only — do not use in production) |
| `PORT` | Port the server listens on (injected automatically by Render) |

### Frontend (`.env`)

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | Backend base URL (e.g. `https://lyfter-api.onrender.com`) |
