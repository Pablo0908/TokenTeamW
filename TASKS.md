# TASKS — Lyfter Badge App

> **Project:** TokenTeamW · **Company:** Lyfter · **Event:** Costa Rica, November 2026
> **Team:** 5 members · **Duration:** 3 weeks

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Flask + JWT + MongoDB + PyMongo |
| Frontend | Vue.js + Tailwind CSS + DaisyUI |
| Deploy Backend | Render |
| Deploy Frontend | Vercel |
| AI Tool | Claude |

---

## Folder Structure

```
TokenTeamW/
├── backend/
│   ├── config/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── utils/
│   ├── .env
│   └── app.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── views/
│   │   └── main.js
│   ├── .env
│   └── index.html
└── TASKS.md
```

---

## MongoDB Collections

### `users`
```json
{
  "_id": "ObjectId",
  "username": "String",
  "password": "String (bcrypt hash)",
  "email": "String (unique)",
  "rol": "String (enum: ['admin', 'attendee'])",
  "verification": "Boolean",
  "name": "String",
  "lastname": "String"
}
```

### `badges`
```json
{
  "_id": "ObjectId",
  "event": "ObjectId → Event",
  "name": "String",
  "description": "String",
  "image": "String (URL)",
  "token": "String (UUID, unique, indexed)",
  "date": "Date",
  "qr": "String (image URL)"
}
```

### `events`
```json
{
  "_id": "ObjectId",
  "name": "String",
  "description": "String",
  "date": "Date",
  "prize": "String",
  "badges_id": ["ObjectId → Badge"]
}
```

### `achievements`
```json
{
  "_id": "ObjectId",
  "events_id": "ObjectId → Event",
  "users_id": "ObjectId → User",
  "date": "Date",
  "prize": "String"
}
```

### `assistance`
```json
{
  "_id": "ObjectId",
  "users_id": "ObjectId → User",
  "badge_id": "ObjectId → Badge",
  "events_id": "ObjectId → Event"
}
```

---

## API Endpoints

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| GET | `/redeem/<event_id>/<token>` | Public | QR scan. Registers badge for authenticated user. Redirects to login if no active session. |
| POST | `/auth/register` | Public | Register new attendee with name, email, and password. |
| POST | `/auth/login` | Public | Attendee login. Returns JWT. |
| GET | `/events/` | Authenticated | List all active events. |
| GET | `/events/<id>` | Authenticated | Event detail: name, description, badge list, and prize. |
| GET | `/me/badges` | Attendee | All badges earned by the user, grouped by event. |
| POST | `/admin/event` | Admin | Create new event with name, description, dates, and prize config. |
| POST | `/admin/events/<id>/badge` | Admin | Add badge to event. Auto-generates UUID token and QR image. |
| GET | `/admin/events/<id>/badges` | Admin | List all badges for an event with QR and redemption status. |

---

## Week 1 — Training

> Goal: arrive at Week 2 with core concepts clear and tools configured.

- [ ] **W1-MON** Kickoff — team presentation, project overview, Git & GitHub practice
- [ ] **W1-TUE** Data modeling + MongoDB practice
- [ ] **W1-WED** Flask + REST + AI practice (build a small API with AI assistance)
- [ ] **W1-THU** HTML + CSS + JS + Tailwind + DaisyUI + Vue.js — UI practice with AI
- [ ] **W1-FRI** Flexible day — reinforce topics that generated doubts

---

## Week 2 — Core Development

### Monday — Project Setup
> Goal: project runs locally, repo configured, everyone has access.

**Backend**
- [ ] **W2-MON-BE-01** Create repo on GitHub, configure team access
- [ ] **W2-MON-BE-02** Set up folder structure (`backend/` and `frontend/`)
- [ ] **W2-MON-BE-03** Configure `.env` for backend (MongoDB URI, JWT secret)
- [ ] **W2-MON-BE-04** Define MongoDB models: `users`, `events`, `badges`, `achievements`, `assistance`
- [ ] **W2-MON-BE-05** Connect MongoDB with PyMongo
- [ ] **W2-MON-BE-06** Install all backend dependencies (Flask, PyJWT, PyMongo, qrcode, etc.)

**Frontend**
- [ ] **W2-MON-FE-01** Initialize Vue project
- [ ] **W2-MON-FE-02** Install Tailwind CSS + DaisyUI
- [ ] **W2-MON-FE-03** Configure frontend `.env` variables
- [ ] **W2-MON-FE-04** Set up frontend folder structure (`views/`, `components/`)
- [ ] **W2-MON-FE-05** Verify blank screen runs in local — project boots without errors

---

### Tuesday — Auth + Event Management

**Backend**
- [ ] **W2-TUE-BE-01** `POST /auth/register` — register attendee with name, email, password (hashed)
- [ ] **W2-TUE-BE-02** `POST /auth/login` — authenticate and return JWT
- [ ] **W2-TUE-BE-03** JWT generation and validation middleware
- [ ] **W2-TUE-BE-04** Role system: `admin` / `attendee` — protect routes by role
- [ ] **W2-TUE-BE-05** `GET /events/` — list all active events (authenticated)
- [ ] **W2-TUE-BE-06** `POST /admin/event` — create event with name, description, dates, prize (admin only)

**Frontend**
- [ ] **W2-TUE-FE-01** Register screen — form with all user fields
- [ ] **W2-TUE-FE-02** Login screen — email + password form
- [ ] **W2-TUE-FE-03** Save JWT in `localStorage` after login
- [ ] **W2-TUE-FE-04** Redirect by role on login (admin → admin panel, attendee → events)
- [ ] **W2-TUE-FE-05** Create event view (admin) — form with name, description, dates, prize
- [ ] **W2-TUE-FE-06** Event list view — show active events
- [ ] **W2-TUE-FE-07** Form validation on register and login

---

### Wednesday — Badges + QR Generation

**Backend**
- [ ] **W2-WED-BE-01** `POST /admin/events/<id>/badge` — add badge to event, auto-generate UUID token + QR image
- [ ] **W2-WED-BE-02** `GET /events/<id>` — event detail with badge list and prize (authenticated)

**Frontend**
- [ ] **W2-WED-FE-01** Add badge to event view — form with badge name, description, image
- [ ] **W2-WED-FE-02** Show generated QR on screen after badge creation
- [ ] **W2-WED-FE-03** Download and print button for the QR

---

### Thursday — Badge Redemption (QR Scan)

**Backend**
- [ ] **W2-THU-BE-01** `GET /redeem/<event_id>/<token>` — validate token, verify not already redeemed, register badge for user, detect if user completed all event badges

**Frontend**
- [ ] **W2-THU-FE-01** Public redemption page (no login required to land on it)
- [ ] **W2-THU-FE-02** Redirect to login if no active session, then back to redemption
- [ ] **W2-THU-FE-03** Clear visual feedback on successful badge redemption
- [ ] **W2-THU-FE-04** Special message if user completes all badges in the event

---

### Friday — Profile + End-to-End Integration

**Backend**
- [ ] **W2-FRI-BE-01** `GET /me/badges` — all badges earned by the current user, grouped by event, including prize description on completion

**Frontend**
- [ ] **W2-FRI-FE-01** Badge profile view — show badges grouped by event
- [ ] **W2-FRI-FE-02** Progress bar per event — how many badges earned vs total
- [ ] **W2-FRI-FE-03** Congratulations message + prize reveal when event is completed
- [ ] **W2-FRI-TEST-01** End-to-end test: create event → generate QR → scan → see badge in profile

---

## Week 3 — Polish & Demo

### Monday — Admin Panel

**Backend**
- [ ] **W3-MON-BE-01** `GET /admin/events/<id>/badges` — list all badges for an event with QR and redemption status per attendee

**Frontend**
- [ ] **W3-MON-FE-01** Admin panel — event list with status and attendee list per event

---

### Tuesday — Admin Stats + UX Improvements

**Backend**
- [ ] **W3-TUE-BE-01** Summary endpoint — total attendees, badges redeemed, completion percentage
- [ ] **W3-TUE-BE-02** Improved error validation on all endpoints — clear error responses

**Frontend**
- [ ] **W3-TUE-FE-01** Visual indicator of how many badges were redeemed per event
- [ ] **W3-TUE-FE-02** Error handling in UI — clear messages when something fails

---

### Wednesday — Deploy to Production

**Backend**
- [ ] **W3-WED-BE-01** Deploy Flask backend to Render
- [ ] **W3-WED-BE-02** Set environment variables in Render (MongoDB URI, JWT secret)
- [ ] **W3-WED-BE-03** Verify QR codes point to the production domain

**Frontend**
- [ ] **W3-WED-FE-01** Deploy Vue frontend to Vercel
- [ ] **W3-WED-FE-02** Set frontend environment variables in Vercel
- [ ] **W3-WED-FE-03** Full flow test from production URL

---

### Thursday — Demo Prep

- [ ] **W3-THU-01** Clean up code, remove debug comments
- [ ] **W3-THU-02** Complete README with setup instructions
- [ ] **W3-THU-03** Load real test data in production
- [ ] **W3-THU-04** Full rehearsal of demo flow — every team member must be able to answer technical questions about the code

---

### Friday — Final Demo

> Live presentation in front of Lyfter instructors. Evaluated from production with real data.

- [ ] **W3-FRI-01** Demo: attendee UI — scan, profile, progress, prize
- [ ] **W3-FRI-02** Demo: admin panel — create event, add badges, view QRs
- [ ] **W3-FRI-03** Demo: complete application flow end-to-end

---

## Evaluation Criteria

| Criterion | Points |
|---|---|
| Core functionality (all endpoints, full flow in production) | 40 pts |
| Code quality and structure | 20 pts |
| Frontend design and UX | 20 pts |
| Demo and final presentation | 20 pts |
| **Total** | **100 pts** |

**Bonus features (only evaluated if core is complete):**

| Feature | Bonus |
|---|---|
| Admin stats dashboard | +10 pts |
| Real-time progress counter | +10 pts |
| Past events history | +10 pts |
| Share badge on social media | +10 pts |

---

## Git Workflow

- **Branch for tasks:** `tasks` (this branch)
- **Feature branches:** `feature/TASK-ID-short-description`
- **Commits:** `feat: W2-TUE-BE-01 description` / `fix: W2-WED-FE-02 description`
- Open a Pull Request from your feature branch → `tasks` when done
- At least 1 reviewer per PR
