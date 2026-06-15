# Product Requirements Document — Lyfter Badge App (Frontend)

**Version:** 1.0
**Stack:** Vue.js · Tailwind CSS · DaisyUI · Pinia · Vue Router · Vite · Vercel
**Event Target:** Lyfter Hackathon, Costa Rica — November 2026

> **Companion document:** This PRD covers the **client application** only. The API it consumes
> (authentication, events, badges, redemption, statistics) is specified in
> `Documentation/PRD-Backend.md`. Where this document references an endpoint, it does so as a
> dependency the frontend calls — it does not define backend behavior.

---

## 1. Problem Statement

The Lyfter Badge App backend can issue badges, validate QR redemptions, and count engagement — but a
backend alone is invisible to the people at the event. Attendees can't scan, see, or show off
anything; organizers can't create a badge or watch their booth's traffic without a developer running
queries. The **frontend is the entire experience** for both audiences.

The client must turn the core loop into something that feels instant and playful on a phone at a
crowded venue: point camera → earn badge → celebrate → see your collection grow toward a prize. For
organizers it must be a self-service web UI — create an event, mint a badge, print its QR, and watch
live counts — with **zero developer help on the day**.

**Who has the problem:**
- **Attendees / participants** who want a memorable, interactive artifact and a reason to explore every
  booth — but only have their phone's browser and a few seconds of patience per interaction.
- **Event organizers** (Lyfter teams, booth owners, ops) who need a point-and-click admin surface, not
  a database client, to run badges and read engagement in real time.

**Why now:** The backend is scoped and the November 2026 hackathon is a controlled first audience.
A polished, mobile-first client is what makes the concept demonstrable — and pitchable to external
clients afterward.

---

## 2. Goals & Success Metrics

### Goal 1 — Make badge collection feel instant and fun
The scan → earn → celebrate loop must feel immediate and rewarding on a phone.

| KPI | Target |
|-----|--------|
| Scan decode → confirmation screen rendered | < 2 seconds on 4G |
| Median time from app-open to first successful scan | < 90 seconds |
| Percentage of registered attendees who scan ≥ 1 badge | ≥ 70% |

### Goal 2 — Give organizers self-service visibility
Issuers create badges and read engagement entirely through the UI.

| KPI | Target |
|-----|--------|
| Admin creates a badge + sees its QR end-to-end in the UI | < 5 minutes, no dev help |
| Dashboard reflects a new scan after refresh/poll | < 3 seconds of scan |
| Badge gallery first contentful paint (up to 50 earned badges) | < 1.5 seconds |

### Goal 3 — Never break in front of an attendee
The client must degrade gracefully, never crash, never dead-end.

| KPI | Target |
|-----|--------|
| Duplicate / invalid / inactive scans shown gracefully (no crash) | 100% |
| Unrecognized (non-Lyfter) QR handled with a friendly message | 100% |
| Attendee flow completable on a mobile browser with no install | 100% |

---

## 3. Target Users

### Persona 1 — Valentina, the Engaged Attendee
- **Role:** Developer attendee at the Lyfter Hackathon.
- **Device:** Her own phone, mobile browser only — she will not install a native app.
- **Goals:** Scan fast, collect all badges, watch her progress, unlock the event prize, maybe share a
  badge on social.
- **Frustrations:** Sign-up walls before she can do anything; earning something and then having no way
  to see or show it; a scanner that fights her camera.

### Persona 2 — Diego, the Booth Organizer
- **Role:** Lyfter team lead running a sponsorship booth.
- **Device:** A tablet or laptop at his booth.
- **Goals:** Create a badge + QR himself, print it, and watch how many people scanned his booth in
  near-real time.
- **Frustrations:** Admin tooling that takes 20 clicks; not being able to tell at a glance how his
  booth is doing.

### Persona 3 — Sofía, the Event Admin
- **Role:** Lyfter ops, managing the whole event.
- **Device:** Laptop/desktop before and during the event.
- **Goals:** Set up the event, manage badges across booths, and monitor a unified live count of all
  redemptions.
- **Frustrations:** Babysitting the system; attendees getting stuck on a confusing screen with no clear
  next step.

---

## 4. Functional Requirements

### 4.1 Collector (End User / Attendee)

**Registration & Authentication**
- The app shall provide a **login** view (email + password) that authenticates against the API and
  stores the returned JWT client-side.
- The app shall provide a **self-registration** view (name, email, password) so attendees can create
  their own account without admin help.
- The app shall store the JWT client-side and attach it to the `Authorization` header on all
  authenticated requests (via an Axios interceptor).
- The app shall redirect the user after login based on their role (attendee → scan/home; admin →
  admin dashboard).
- On a `401` (expired/invalid token) the app shall clear the session and redirect to login.

**QR Scanning (in-app camera scanner)**
- The app shall provide a **Scan view** that activates the device camera via the browser Web API.
- The app shall request camera permission and show a clear prompt/explanation; if permission is denied,
  it shall show a recovery message rather than a blank screen.
- The app shall decode a QR code **client-side** (live, on detection) and parse a redemption URL of the
  form `/scan/{event_id}/{qr_token}`.
- The app shall **auto-call the redemption API immediately** after a successful decode — no extra tap
  required.
- The app shall recognize when a scanned QR is **not** a Lyfter badge URL and show
  "This QR code is not a Lyfter badge." without crashing.

**Badge Earning**
- On a successful redemption (`200`), the app shall display a **confirmation/celebration screen** with
  the badge name + image and a **confetti** animation.
- The confirmation screen shall offer a clear CTA to "View My Collection".
- The app shall show a **friendly message** (not an error crash) for each backend outcome:
  - Already earned → friendly "You already have this badge" (API `409`).
  - QR invalid or event not active → friendly message (API `403`).
  - Badge redemption limit reached → friendly message (API `410`).
  - Session expired → prompt to log in again (API `401`).

**Badge Collection / Gallery**
- The app shall provide a **personal gallery** view (`/me/badges`) listing all badges the user has
  earned.
- Each badge card shall display the badge name, image, event name, and date earned.
- The gallery shall present badges grouped per event; not-yet-earned badges in an event may appear
  greyed-out to communicate what's left to collect.
- The app shall allow the user to tap a badge for a **detail view**.

**Progress & Prize (gamification)**
- For each event, the app shall display a **progress indicator** (e.g. `3 / 5 badges`) using a
  `<ProgressBar>`.
- When a user collects **all** badges in an event, the app shall render a **prize reveal**
  (`<PrizeReveal>`) celebrating the unlocked prize.

**Sharing**
- The app shall allow the user to **download an earned badge as an image** file.
- The app shall offer a **native share** option (Web Share API) on supported devices, with a graceful
  fallback (e.g. download/copy) where unsupported.

---

### 4.2 Issuer (Admin / Organizer)

**Authentication & Access**
- The app shall let an admin log in and route them to the **admin dashboard**.
- Admin routes shall be protected by a route guard; non-admin users attempting to reach them are
  redirected away.

**Dashboard & Monitoring**
- The app shall display a **dashboard** showing total redemptions per badge, per event.
- The dashboard shall refresh redemption counts in **near-real-time** (polling is acceptable) so
  organizers see scans increment during the event.

**Event Management**
- The app shall provide an **event create** form (name, description, date(s), location/prize as
  applicable) that submits to the API.

**Badge & QR Management**
- The app shall provide a **badge create** form (name, description, image, optional redemption limit)
  tied to an event.
- After creation, the app shall **render the generated QR code image inline** on the badge view.
- The app shall provide a **badge list** view per event showing each badge with its QR thumbnail, a
  **Download QR** action (for printing), and its live redemption count.

---

## 5. Non-Functional Requirements

### Performance
- **Badge gallery first contentful paint:** < 1.5 seconds for up to 50 earned badges.
- **Cached-first rendering:** the gallery shall render instantly from local state (Pinia store) if
  already fetched, then refresh in the background.
- **Scan-to-confirmation:** the confirmation screen shall render within < 2 seconds of a successful
  decode on a 4G connection (API round-trip dependent).

### Usability & Accessibility
- The **entire attendee flow** (register → scan → earn → view gallery) shall be completable on a
  **mobile browser** with **no native app install**.
- The Scan view shall require **no extra interaction** after pointing the camera at a QR (auto-decode
  on detection).
- The UI shall meet **WCAG 2.1 AA** minimums for color contrast and text sizing.
- All user-facing error messages shall be in **plain language with a suggested next action** (never a
  raw error code or stack).

### Reliability
- If the backend is unreachable during a scan, the app shall show a **timeout message and a retry CTA**
  — it must not silently fail. The badge is considered earned only once the server confirms.
- The app shall **not crash on malformed or unrecognized QR content** — it shows
  "This QR code is not a Lyfter badge." instead.
- Route guards shall prevent reaching authenticated views without a valid session.

### Installability (PWA)
- The app shall be an installable **PWA** (web app manifest + service-worker app shell) so attendees
  can add it to their home screen for an app-like launch. (Offline data sync is out of scope — see §6.)

### Compatibility
- The app shall function on current **iOS Safari** and **Android Chrome** (the primary attendee
  browsers) and on desktop Chrome/Edge for admin use.

### Security (client-side)
- The JWT is stored client-side and attached to requests; no secrets or API keys are bundled into the
  client.
- The client expects the API to enforce CORS to the production frontend origin and localhost in
  development; the client makes no cross-origin assumptions beyond `VITE_API_URL`.

---

## 6. Scope

### In Scope — v1

- Login + **self-registration** views; client-side JWT handling and role-based redirect.
- **In-app camera QR scanner** with client-side decode and auto-redeem.
- Badge earning **celebration screen + confetti** and friendly outcome messages (409 / 403 / 410 / 401).
- **Badge gallery** + badge **detail view**.
- **Per-event progress bar** and **prize reveal** on completion.
- **Badge sharing**: image download + Web Share API.
- Admin: **dashboard** (live redemption counts), **event create**, **badge create** with inline QR,
  **badge list** with QR download.
- **PWA** install (manifest + app-shell service worker).
- Deployment: Vue SPA on **Vercel**.

### Out of Scope — v1

- **Offline mode / data sync** — a live event has WiFi; a timeout + retry message is sufficient.
- **Leaderboards / public ranking UI** — deferred (privacy/fairness for a first event).
- **Badge trading / transfer UI** — adds social complexity that dilutes the collect loop.
- **Push notifications** — infra overhead not justified for a one-day event.
- **Native iOS / Android app** — the PWA + mobile browser is sufficient.
- **Multi-tenant theming / white-label UI** — single-org deployment for v1.
- **In-app analytics export (CSV/PDF) UI** — the live dashboard is sufficient for v1.

---

## 7. User Flows

### Flow 1 — Badge Collector: First Scan

1. User opens the app URL on their phone (no install required; may install the PWA when prompted).
2. If not logged in → redirected to `/login`. User logs in, or taps through to `/register` to create
   an account.
3. On successful auth → JWT stored client-side. User lands on the scan entry point (`/scan` or home).
4. User taps **Scan Badge** → app requests camera permission via the browser.
5. Camera view opens. User points it at a booth QR code.
6. App decodes the QR URL `{APP_URL}/scan/{event_id}/{qr_token}` client-side.
7. App calls the redemption endpoint with `{ event_id, qr_token }` + JWT header.
8. **Happy path:** API returns `200`. App navigates to the badge-earned screen.
9. **Celebration screen:** badge image, name, confetti, "View My Collection" CTA.
10. User taps **View My Collection** → gallery (`/me/badges`).
11. Gallery shows earned badges grouped by event, each with a **progress bar**; if an event is fully
    collected, the **prize reveal** is shown.

### Flow 2 — Badge Issuer: Create Badge + Print QR

1. Admin logs in with admin credentials → lands on the **admin dashboard** (event list + redemption
   totals).
2. Admin opens an event → clicks **Add Badge**.
3. Admin fills in the badge form: name, description, image, optional redemption limit.
4. Admin clicks **Create Badge** → the app submits to the API.
5. The app renders the returned **QR code image inline** on the badge view.
6. Admin clicks **Download QR** → QR image downloads for printing.
7. Admin prints the QR and places it at the physical booth.
8. Admin returns to the dashboard throughout the event and watches the **live redemption count**
   increment.

### Flow 3 — Edge Cases (UI Behavior)

| Scenario | Frontend behavior |
|----------|-------------------|
| QR is not a Lyfter URL / corrupted | Client decode fails to match the expected pattern → "This QR code is not a Lyfter badge. Try again." (no crash) |
| User scans without being logged in | Route guard intercepts before the camera opens → redirect to `/login` |
| Badge already earned | API `409` → friendly "You already have this badge" screen |
| Event not active | API `403` → friendly "This badge isn't available right now" |
| Redemption limit reached | API `410` → friendly "This badge is no longer available" |
| Session expired mid-scan | API `401` → clear session, prompt to log in again |
| Network timeout during redemption | Show a retry CTA after a short timeout; badge is not shown as earned until the server confirms |

---

## 8. Technical Considerations

### Architecture Overview

```
[Vue SPA — Vercel CDN]
       │ HTTPS / Axios (JWT in Authorization header)
       ▼
[Flask API — Render]   ← specified in PRD-Backend.md
       │
       ▼
[MongoDB Atlas]
```

The frontend is a **static SPA** deployed to the Vercel CDN. There is no server-side rendering. All
client state lives in the Vue app (Pinia store); the API holds persistent data.

### Project Structure (reference — see TDD §4.1)

```
frontend/
├── index.html
├── vite.config.js          # Vite + PWA plugin
├── tailwind.config.js      # Tailwind + DaisyUI plugin
├── .env / .env.production
└── src/
    ├── main.js             # app init: router + Pinia
    ├── App.vue
    ├── api/                # axios.js (instance + interceptors), auth.js, events.js, badges.js, admin.js
    ├── router/index.js     # routes + beforeEach navigation guard
    ├── store/              # auth.js, events.js (Pinia)
    ├── views/
    │   ├── public/         # LoginView, RegisterView, ScanView, RedeemResultView
    │   ├── participant/    # EventListView, EventDetailView, BadgeProfileView
    │   └── admin/          # AdminDashboardView, AdminEventCreateView, AdminBadgeCreateView, AdminBadgeListView
    └── components/         # NavBar, BadgeCard, ProgressBar, QRCard, PrizeReveal, Confetti
```

### Routing & Guards
- Vue Router with route `meta` flags: `public`, `requiresAuth`, and `role: "admin"`.
- A `beforeEach` guard reads the token/role from the auth store: public routes pass; missing token →
  `/login`; role mismatch → redirect to the attendee home.
- Key routes include the **in-app** `/scan` route (camera scanner) plus `/login`, `/register`,
  `/events`, `/events/:id`, `/me/badges`, and the `/admin/...` set.

### State Management
- **Pinia** stores: `auth` (token, user, login/logout actions, persisted to client storage) and
  `events` (cache for instant gallery render + background refresh).

### API Access
- A single **Axios** instance keyed off `VITE_API_URL`, with a request interceptor that attaches the
  `Bearer` token and a response interceptor that logs out + redirects on `401`.

### QR Scanning Approach
- The Scan view uses the **browser camera Web API** plus a **client-side QR-decode library**
  (`BarcodeDetector` where available, falling back to a JS decoder such as `qr-scanner` /
  `html5-qrcode`).
- On decode, it parses the encoded `/scan/{event_id}/{qr_token}` URL, extracts the params, and calls
  the redemption API. Non-matching content is rejected client-side with the "not a Lyfter badge"
  message.

### Celebration & Gamification UI
- A confetti effect + confirmation screen on earn; a `<ProgressBar>` per event; a `<PrizeReveal>`
  component that animates when an event is fully collected.

### PWA
- Configure `vite-plugin-pwa` to emit a web app manifest (name, icons, theme color) and a
  service-worker app shell so the SPA is installable and launches app-like. (No offline data caching
  beyond the shell in v1.)

### Deployment (Vercel)
- Framework preset **Vite**; build `npm run build`; output `dist`.
- Set `VITE_API_URL` to the production API origin.
- Add `vercel.json` with a catch-all rewrite so Vue Router history mode works on reload:
  ```json
  { "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }
  ```
- **Render cold start:** the API free tier sleeps after inactivity; the client shall show a loading
  state on the first request and may issue a lightweight keepalive ping so the first real scan isn't
  blocked by a cold start.

### Environment Variables (frontend)
```bash
# .env (local dev)
VITE_API_URL=http://localhost:5000
# .env.production (Vercel)
VITE_API_URL=https://<your-api>.onrender.com
```

---

## 9. Open Questions

| # | Question | Why It Matters | Options |
|---|----------|----------------|---------|
| 1 | **What exactly is the shared badge artifact?** | "Download badge as image" + Web Share are in scope. Does the image need branding (Lyfter logo, event name, date, user's name)? | Needs a design mockup before implementation |
| 2 | **Which QR-decode library?** | `BarcodeDetector` isn't supported on all iOS Safari versions; a JS fallback affects bundle size and decode speed. | (A) `BarcodeDetector` + JS fallback; (B) `html5-qrcode`; (C) `qr-scanner` |
| 3 | **DaisyUI theme / design tokens?** | Determines look-and-feel, color contrast (WCAG AA), and dark mode. | Pick a DaisyUI theme + brand palette before UI build |
| 4 | **After self-registration, auto-login or route to login?** | Affects the onboarding flow length at the door. | (A) Auto-login on register; (B) Redirect to `/login` |
| 5 | **First-request cold-start handling.** | A 30–60s Render cold start on the first scan is a bad first impression. | (A) Keepalive ping on app load; (B) Loading state only; (C) Pre-warm before doors open |
| 6 | **Minimum supported screen size / orientation for the scanner.** | The camera view and confirmation screen must work on small phones in portrait. | Define a minimum viewport + portrait-first layout |

---

## 10. Launch Criteria

### Functional Checklist (all must pass before go-live)

- [ ] User can register a new account and log in; JWT is stored and attached to requests.
- [ ] User is redirected by role after login (attendee vs admin).
- [ ] In-app scanner opens the camera, decodes a QR, and auto-calls the redemption API.
- [ ] Earning a badge shows the celebration screen + confetti.
- [ ] Earned badge appears in the gallery immediately after scan.
- [ ] Per-event progress bar is correct; prize reveal fires when an event is fully collected.
- [ ] Duplicate scan shows a friendly message and does not dead-end (no crash).
- [ ] Invalid / non-Lyfter QR shows "This QR code is not a Lyfter badge." (no crash).
- [ ] Badge sharing (download image) works on iOS Safari and Android Chrome.
- [ ] Admin can create an event and a badge, and see the QR rendered inline.
- [ ] Admin can download the QR image for printing.
- [ ] Admin dashboard shows the correct redemption count per badge and updates during the event.
- [ ] App is installable (PWA) and usable on mobile without installing anything native.

### QA Bar

- No CORS console errors from the frontend → API in production.
- Route guards verified: authenticated views are unreachable without a valid session; admin views are
  unreachable by attendees.
- `401` handling verified: an expired token clears the session and redirects to login.
- No uncaught exceptions on malformed QR, denied camera permission, or network timeout.

### Performance Threshold

- Badge gallery load (50 badges): < 1.5 seconds on throttled 4G (Chrome DevTools).
- Scan decode → confirmation screen: < 2 seconds over 20 real scan attempts.

### Stakeholder Sign-Off

- [ ] **PM / Team Lead:** Functional checklist verified in staging.
- [ ] **Lyfter Ops (Sofía):** Can create event + badge + download QR with no developer help.
- [ ] **Test Attendee:** Completes register → scan → earn → gallery on a real phone with no guidance.
- [ ] **Design:** UI meets WCAG 2.1 AA contrast/text; sharing artifact approved.
- [ ] **Deployment:** Vercel project configured, `VITE_API_URL` set, `vercel.json` rewrite in place,
      PWA installable.
