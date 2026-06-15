# Product Requirements Document — Lyfter Badge App (Backend)

**Version:** 1.0
**Stack:** Flask · PyMongo · MongoDB · JWT · Render
**Event Target:** Lyfter Hackathon, Costa Rica — November 2026

---

## 1. Problem Statement

Physical events — conferences, hackathons, trade fairs, booth crawls — have an engagement problem. Attendees drift between sessions with no incentive to explore everything on offer. Organizers have no lightweight, real-time signal for which booths or activities are actually drawing traffic. Paper stamps, wristbands, and attendance sheets are friction-heavy and produce zero digital data.

**Who has the problem:**
- **Event organizers** (Lyfter internal teams, hackathon hosts) who want to drive booth engagement and measure participation without expensive hardware or integrations.
- **Attendees / participants** who want a memorable, playful artifact from the event and a reason to explore every corner of the venue — but currently get nothing interactive.

**Why now:** Lyfter's November 2026 hackathon is a controlled first environment. The team is small, the event is scoped, and the audience is technical enough to tolerate a v1 product. A working deployment here proves the concept before pitching it to external clients.

---

## 2. Goals & Success Metrics

### Goal 1 — Drive badge collection engagement
Attendees should actively scan QR codes, not passively receive them.

| KPI | Target |
|-----|--------|
| Percentage of registered attendees who scan ≥ 1 badge | ≥ 70% |
| Average badges earned per active user | ≥ 3 |
| Median time from app-open to first badge scan | < 90 seconds |

### Goal 2 — Give organizers real-time visibility
Issuers should see live redemption counts without refreshing a page.

| KPI | Target |
|-----|--------|
| Redemption stats API response time | < 1 second |
| Event dashboard reflects scan within | < 3 seconds of scan |
| Admin can create a new badge + QR end-to-end | < 5 minutes |

### Goal 3 — Reliable, low-friction scan experience
The core loop (scan → earn → see badge) must not fail at a live event.

| KPI | Target |
|-----|--------|
| Scan-to-badge-confirmed latency (p95) | < 2 seconds on 4G |
| API uptime during event window | ≥ 99.5% |
| Duplicate-scan returns a clean 409 (no crashes) | 100% |

---

## 3. Target Users

### Persona 1 — Valentina, the Engaged Attendee
- **Role:** Developer attendee at the Lyfter Hackathon
- **Context:** Has her phone, heard there are "digital badges" to collect. Curious but skeptical of QR-code experiences that go nowhere.
- **Goals:** Collect all badges, see what she's earned, maybe share one on social.
- **Frustrations:** Apps that require sign-up before letting her do anything. Earning a badge and then having no way to show it off.

### Persona 2 — Diego, the Booth Organizer
- **Role:** Lyfter team lead, running a sponsorship booth at the hackathon
- **Context:** Has a tablet at his booth. Wants attendees to scan his QR code to "unlock" a badge tied to his booth. Needs to generate the QR code himself and print it.
- **Goals:** Generate a badge + QR without needing developer help. See live how many people scanned his booth. Know if someone tries to scan twice (and what happens to them).
- **Frustrations:** Admin tooling that takes 20 steps to do something simple. QR codes that are generic and not tied to his specific activity.

### Persona 3 — Sofía, the Event Admin
- **Role:** Lyfter internal ops, managing the whole event
- **Context:** She sets up the event in the app before the day, assigns badges to activities, and monitors the global scan count throughout the event.
- **Goals:** Create the event, manage all badges across all booths, see a unified set of stats, export or share final redemption numbers after the event.
- **Frustrations:** Having to babysit the system. Attendees getting stuck because a QR is expired or invalid. No audit trail when something goes wrong.

---

## 4. Functional Requirements

### 4.1 Collector (End User / Attendee) — API Responsibilities

**Registration & Auth**
- The system shall allow a user to register with name, email, and password.
- The system shall authenticate users via email + password, returning a JWT on success.

**QR Redemption**
- The system shall expose a redemption endpoint accepting `{ event_id, qr_token }` with a JWT in the request header.
- The system shall credit the badge to the authenticated user's account on a valid, non-duplicate scan.
- The system shall return `409 Conflict` (without creating a duplicate record) when the badge was already earned.
- The system shall return a generic error / `403` when the QR token is invalid or the event is not `active`.

**Badge Collection**
- The system shall expose an endpoint returning all badges the authenticated user has earned, including each badge's name, image reference, event name, and date earned.

---

### 4.2 Issuer (Admin / Organizer)

**Event Management**
- The system shall allow an admin to create an event with: name, description, date, location.
- The system shall allow an admin to set event status: `draft`, `active`, `finished`.
- The system shall enforce that QR redemption only succeeds when the event status is `active`.

**Badge & QR Management**
- The system shall allow an admin to create a badge tied to an event, with: name, description, image URL.
- The system shall allow an admin to set an optional redemption limit per badge.
- The system shall automatically generate a unique QR token (UUID) and QR code image upon badge creation.
- The system shall make the generated QR code image available for printing or downloading.

**Redemption Monitoring**
- The system shall expose statistics showing total redemptions per badge, per event.
- The system shall update the redemption count in near-real-time (suitable for polling).
- The system shall allow an admin to retrieve a list of all redemptions with user, timestamp, and badge.

**Role Enforcement**
- The system shall restrict event creation, badge creation, and admin statistics access to users with `admin` role.
- The system shall return a `403 Forbidden` response to non-admin requests on protected routes.

---

## 5. Non-Functional Requirements

### Performance
- Scan-to-badge-confirmed API round trip: **p95 < 2 seconds** on a 4G mobile connection.
- Admin stats endpoint responds: **< 1 second** for up to 500 redemptions.

### Security
- All passwords stored as bcrypt hashes (cost factor ≥ 12). Plaintext passwords must never be logged or returned.
- JWT tokens expire after **8 hours**. No persistent sessions on the server.
- Each badge has a **unique, non-guessable `qr_token`** (UUID v4). Tokens are not sequential.
- Duplicate redemption prevention enforced via a **compound unique index** on `(badge_id, user_id)` in MongoDB — enforced at the DB layer, not just application logic.
- All API endpoints that mutate state require a valid JWT. Unauthenticated requests return `401`.
- CORS is configured to allow requests only from the production frontend domain and localhost in development.
- QR token validation does not leak information: invalid token and expired event return the same generic error message to the client.

### Scalability
- The system shall handle **500 concurrent users** scanning simultaneously without degradation (scoped to a single event).
- MongoDB collections shall have indexes on: `users.email`, `badges.qr_token`, `redemptions.(badge_id, user_id)`.
- The Flask app shall be stateless — no in-process session state — to enable horizontal scaling on Render if needed.

### Usability
- All API error responses shall include a plain-language message and a suggested next action.

### Reliability
- The redemption endpoint shall not credit a badge until the server confirms a successful, non-duplicate write.
- The API shall return structured error responses (never a raw stack trace) for malformed or unrecognized input.

---

## 6. Scope

### In Scope — v1

- User registration and JWT-based login
- Admin and attendee role distinction
- Event creation, status management (draft / active / finished)
- Badge creation with auto-generated QR token and QR image
- Redemption validation with duplicate prevention
- Endpoint returning an attendee's earned badges
- Admin stats endpoint: per-event redemption counts per badge
- Deployment: Flask API on Render
- Seeded demo data for the hackathon launch event

### Out of Scope — v1

- **Push notifications** — too much infrastructure overhead for a one-day event. Deferred to v2.
- **Badge trading or transferability** — adds social complexity that dilutes the core collect loop.
- **Leaderboards / public ranking** — privacy and fairness concerns for a first event; deferred.
- **QR code expiration by time** — redemption limits per badge are sufficient for v1. Time-expiry adds clock-sync complexity.
- **Native iOS / Android app** — a mobile browser is sufficient for the hackathon audience.
- **Multi-tenant / white-label** — v1 is a single-org deployment for Lyfter. SaaS mode is a v3 problem.
- **Analytics export (CSV/PDF)** — the in-app stats are sufficient for v1.
- **Offline mode** — a live event has WiFi. Graceful degradation (error message + retry) is sufficient.
- **Badge categories or collections** — flat badge list is fine for v1.
- **Email verification** — adds friction for a controlled hackathon audience who will be onboarded in person.

---

## 7. Flows (API Sequences)

### Flow 1 — Badge Collector: Redemption

1. Client authenticates via `POST /api/auth/login` and receives a JWT.
2. Client calls `POST /api/redenciones/validar` with `{ event_id, qr_token }` and the JWT header.
3. **Happy path:** the API validates that the event is `active`, the token is valid, and no prior redemption exists for `(badge_id, user_id)`. It creates the redemption record, increments the denormalized counter, and returns `200` with badge data.
4. The earned badge is immediately retrievable via `GET /api/usuarios/me/badges`.

### Flow 2 — Badge Issuer: Create Badge + Generate QR

1. Admin authenticates with admin credentials and receives a JWT.
2. Admin sends `POST /api/eventos/{id}/badges` with: badge name, description, image URL, optional redemption limit.
3. Backend generates `qr_token` (UUID v4), builds the QR code image, and stores both on the badge document.
4. The rendered QR code image is returned/available for download so it can be printed.
5. Admin prints the QR and places it at the physical booth.
6. Admin monitors redemption counts throughout the event via `GET /api/admin/estadisticas/{event_id}`.

### Flow 3 — Edge Cases (API Behavior)

| Scenario | API Behavior |
|----------|----------------|
| User redeems the same badge twice | API returns `409 Conflict`. No duplicate record created. |
| Event is not active (draft or finished) | API returns `403`. |
| Badge has reached its redemption limit | API returns `410 Gone`. |
| JWT is expired during a redemption | API returns `401`. |

---

## 8. Technical Considerations

### Architecture Overview

```
[Client / API consumer]
       │ HTTPS / REST
       ▼
[Flask API — Render]
       │ PyMongo
       ▼
[MongoDB Atlas]
```

The Flask API is a single Gunicorn-backed service on Render's free tier. There is no server-side rendering. Persistent state lives in MongoDB.

---

### QR Code Strategy

**Token structure:** Each badge has one `qr_token` — a UUID v4 generated server-side at badge creation. The token is globally unique and not guessable.

**What the QR encodes:** A full URL: `https://{FRONTEND_URL}/scan/{event_id}/{qr_token}`

**Why a URL (not raw JSON):** Allows scanning with any standard QR reader to open the app directly. No proprietary scanner needed.

**QR image generation:** Done server-side in Flask using the `qrcode` Python library. The image is returned as a base64 data URL and stored in MongoDB on the badge document. No external image storage needed for v1.

**No per-user QR:** A single QR serves all users. Duplicate prevention happens at redemption time (DB compound unique index), not at QR issuance. This keeps QR printing simple.

**No expiration by time (v1):** Redemption limits (`limite_redencion`) are the abuse control. Time expiry adds clock-sync risk at a live event.

---

### Authentication Flow

- `POST /api/auth/registro` — creates user, returns JWT
- `POST /api/auth/login` — validates credentials, returns JWT
- JWT payload: `{ user_id, email, rol, iat, exp }`
- Expiry: **8 hours** (sufficient for a hackathon day)
- No refresh token in v1 — re-login on expiry. (Acceptable for a single-day event)
- Flask middleware decorator (`@jwt_required`) validates token on protected routes

---

### Data Model Hints

```python
# usuarios
{
  "_id": ObjectId,
  "nombre": str,
  "email": str,          # unique index
  "password_hash": str,  # bcrypt, never returned in responses
  "rol": "admin" | "asistente",
  "badges_ganados": [ObjectId],  # ref → badges
  "activo": bool,
  "created_at": datetime,
  "updated_at": datetime
}

# eventos
{
  "_id": ObjectId,
  "nombre": str,
  "descripcion": str,
  "fecha": datetime,
  "lugar": str,
  "organizador": ObjectId,  # ref → usuarios
  "estado": "borrador" | "activo" | "finalizado",
  "created_at": datetime
}

# badges
{
  "_id": ObjectId,
  "nombre": str,
  "descripcion": str,
  "evento": ObjectId,       # ref → eventos
  "imagen_url": str,
  "qr_token": str,          # UUID v4, unique index
  "qr_imagen_b64": str,     # base64 PNG from qrcode lib
  "limite_redencion": int | None,
  "total_redimidos": int,   # denormalized counter
  "activo": bool,
  "created_at": datetime
}

# redenciones
{
  "_id": ObjectId,
  "badge_id": ObjectId,    # ref → badges
  "evento_id": ObjectId,   # ref → eventos
  "usuario_id": ObjectId,  # ref → usuarios
  "qr_token_usado": str,
  "fecha": datetime,
  "metadata": {
    "user_agent": str,
    "ip": str              # hashed or truncated for privacy
  }
}
# Compound unique index: (badge_id, usuario_id)
```

---

### Key Flask Endpoints (minimum surface for v1)

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| POST | `/api/auth/registro` | None | Create user |
| POST | `/api/auth/login` | None | Login, get JWT |
| GET | `/api/eventos` | JWT | List active events |
| POST | `/api/eventos` | JWT + admin | Create event |
| PATCH | `/api/eventos/{id}/estado` | JWT + admin | Change event status |
| GET | `/api/eventos/{id}/badges` | JWT | List badges for event |
| POST | `/api/eventos/{id}/badges` | JWT + admin | Create badge + gen QR |
| POST | `/api/redenciones/validar` | JWT | Validate + redeem QR |
| GET | `/api/usuarios/me/badges` | JWT | Get my badge collection |
| GET | `/api/admin/estadisticas/{event_id}` | JWT + admin | Redemption stats |

---

### Deployment Notes

**CORS:** Flask must allow the production frontend domain in production and the local dev frontend origin in development. Use `flask-cors` with an explicit origin allowlist — no wildcard `*` in production.

**Environment variables:**
- Flask (Render): `MONGO_URI`, `JWT_SECRET`, `JWT_EXPIRY_HOURS`, `CLIENT_URL`, `FLASK_ENV`

**Render cold starts:** The free tier sleeps after 15 minutes of inactivity. Implement a `/api/health` ping endpoint and configure a keepalive (e.g. UptimeRobot or a client ping) to keep the backend warm during the event.

---

## 9. Open Questions

| # | Question | Why It Matters | Options |
|---|----------|---------------|---------|
| 1 | **Do attendees self-register, or does the admin pre-create accounts?** | Self-registration adds friction but reduces admin prep work. Pre-created accounts require distributing credentials at check-in. | (A) Self-register at the door; (B) Admin bulk-creates accounts; (C) Magic link via email |
| 2 | **What happens when a badge hits its redemption limit?** | Do we return a 410? The edge case in Flow 3 assumes a friendly response, but the behavior needs sign-off. | (A) Hard block with `410`; (B) Allow overflow, flag for admin review; (C) No redemption limits in v1 |
| 3 | **Where are badge images hosted?** | Storing URLs (external CDN like Cloudinary) keeps MongoDB small. Storing base64 in Mongo is simpler to implement. At 50 badges/event this is fine; at 5,000 it breaks. | (A) Cloudinary/S3; (B) Base64 in MongoDB (v1 acceptable); (C) Static assets in the frontend repo |
| 4 | **How is the QR code printed and displayed at booths?** | A5 printout? Laptop screen? Phone screen? This affects minimum QR size and error correction level needed. | Decide on minimum display size before generating QR; recommend at least 200×200px, error correction H |
| 5 | **Who owns the "admin" role at the hackathon?** | Is it one Lyfter ops person, or do booth owners get admin access to create their own badges? Self-service for booth owners is faster on the day but requires more trust. | (A) Central admin creates all badges; (B) Each booth owner has an admin account; (C) Hybrid: central creates events, booth owners create badges within their event |
| 6 | **Do we need a PIN or passcode on redemption?** | Without a secondary check, a user could redeem the QR from a photo (e.g., screenshot) rather than visiting the physical location. Does that matter for this event? | (A) No — trust the honor system; (B) Booth attendant confirms; (C) Time-windowed QR (rotates every N minutes) |
| 7 | **What is the rollback plan if Render cold-starts during the event?** | Free tier cold starts take 30–60 seconds. If multiple attendees try to scan simultaneously after a period of inactivity, all requests queue. | (A) Upgrade to Render paid plan for the event day; (B) UptimeRobot keepalive; (C) Pre-warm by scanning a test badge 5 minutes before doors open |

---

## 10. Launch Criteria

### Functional Checklist (all must pass before go-live)

- [ ] User can register and receive a JWT
- [ ] User can log in and receive a JWT carrying their role
- [ ] Admin can create an event and set status to `active`
- [ ] Admin can create a badge and receive a downloadable QR code image
- [ ] Redemption endpoint credits the badge end-to-end for a valid request
- [ ] Earned badge is returned by the my-badges endpoint immediately after redemption
- [ ] Duplicate scan returns `409` and does not create a duplicate record
- [ ] Admin stats endpoint returns the correct redemption count per badge

### QA Bar

- Zero P0 bugs (crashes, data loss, auth bypass) at time of launch
- Duplicate-redemption prevention verified with concurrent requests (run 5 simultaneous POSTs to `/validar` for the same user/badge — only 1 must succeed)
- JWT expiry enforced (verified by sending an expired token — must return `401`)
- CORS verified in production (no CORS errors from the frontend → Render)
- QR codes scan successfully from printed paper at 20cm distance (test with iPhone + Android)

### Performance Threshold

- Scan-to-badge-confirmed: p95 < 2 seconds measured over 20 real scan attempts
- Render backend stays warm during 30-minute load test (no cold-start timeouts)

### Stakeholder Sign-Off

- [ ] **PM / Team Lead:** Functional checklist verified in staging environment
- [ ] **Lyfter Ops (Sofía persona):** Admin can create event + badges + download QR without developer assistance
- [ ] **Test Attendee:** End-to-end redemption flow completed without guidance
- [ ] **Security:** No plaintext passwords, JWT expiry confirmed, duplicate prevention confirmed
- [ ] **Deployment:** Production URLs configured, env vars set, CORS verified, keepalive configured