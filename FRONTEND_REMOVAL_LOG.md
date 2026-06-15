# Frontend Removal Log — PRD.md

**Date:** 2026-06-15
**Source:** `Documentation/PRD.md` (PRD branch)
**Purpose:** This file records all frontend-related content removed from or reframed in `Documentation/PRD.md`, so the committed PRD becomes a backend-focused document. **This file is git-ignored and must NOT be uploaded to the repo.**

Frontend stack identified and stripped: **Vue.js, Tailwind CSS, DaisyUI, Pinia, Vite, Vue Router, Vercel**, plus all client-side UI pages, routes, browser-API behaviors, and client deployment config.

---

## Header / Stack line

**Original:**
> **Stack:** Flask · PyMongo · MongoDB · JWT · Vue.js · Tailwind CSS · DaisyUI · Render · Vercel

**Removed tokens:** `Vue.js`, `Tailwind CSS`, `DaisyUI`, `Vercel`
**New:** `**Stack:** Flask · PyMongo · MongoDB · JWT · Render`

---

## Section 2 — Goals & Success Metrics

**Goal 2 KPI reframed** (page load is a frontend metric):
- Original: `| Redemption stats page load time | < 1 second |`
- New: `| Redemption stats API response time | < 1 second |`

**Goal 3 KPI reframed** ("shown gracefully" implies frontend rendering):
- Original: `| Duplicate-scan error rate shown gracefully | 100% (no crashes) |`
- New: `| Duplicate-scan returns a clean 409 (no crashes) | 100% |`

---

## Section 4.1 — Collector (End User / Attendee)

The original section was largely client/UI requirements. Removed bullets:

**Registration & Auth**
- "The system shall store the JWT client-side and attach it to all authenticated requests." *(client-side storage / request handling)*

**QR Scanning** (entire sub-block removed; reframed to a backend "QR Redemption" endpoint)
- "The system shall provide a scan page that activates the device camera via the browser Web API."
- "The system shall parse a QR code containing a redemption URL in the format `/scan/{event_id}/{qr_token}`." *(client-side QR parsing)*
- "The system shall call the redemption API immediately after a successful scan decode." *(client behavior)*

**Badge Earning** (removed client display bullets; kept the backend crediting logic)
- "The system shall display a confirmation screen (animation + badge name/image) immediately after earning."
- "The system shall display a friendly message (not an error crash) if the badge was already earned." *(reframed to API returning 409)*
- "The system shall display a friendly message if the QR is invalid or the event is not active." *(reframed to API returning error/403)*

**Badge Collection / Gallery** (entire UI sub-block removed; reframed to a backend list endpoint)
- "The system shall provide a personal gallery page listing all badges the user has earned."
- "The system shall display each badge's name, image, event name, and date earned."
- "The system shall allow the user to tap a badge for a detail view."

**Sharing** (entire sub-block removed — purely frontend)
- "The system shall allow the user to download their earned badge as an image file."
- "The system shall provide a native share option (Web Share API) on supported devices."

---

## Section 4.2 — Issuer (Admin / Organizer)

Reframed UI references to backend capabilities:
- "The system shall display a dashboard showing total redemptions per badge, per event." → reframed to "expose statistics".
- "The system shall display the QR code image on the badge detail page for printing or downloading." → reframed to "make the generated QR code image available for printing/downloading" (removed "badge detail page").

---

## Section 5 — Non-Functional Requirements

**Performance** — removed/reframed frontend metrics:
- Removed: "Badge gallery page load (first contentful paint): **< 1.5 seconds** for up to 50 earned badges." *(frontend FCP)*
- Reframed: "Admin dashboard stats load: **< 1 second** for up to 500 redemptions." → "Admin stats endpoint responds: **< 1 second** for up to 500 redemptions."

**Security** — CORS wording de-branded:
- Original: "CORS is configured to allow requests only from the production Vercel frontend domain and localhost in development."
- New: "CORS is configured to allow requests only from the production frontend domain and localhost in development." *(removed "Vercel")*

**Usability** — entire section was frontend; removed:
- "The entire attendee flow (register → scan → earn → view gallery) shall be completable on a **mobile browser** without installing a native app."
- "The scan page shall not require any extra user interaction after pointing the camera at a QR code (auto-decode on detection)."
- "UI shall follow **WCAG 2.1 AA** minimum for color contrast and text sizing."
- "All user-facing error messages shall be in plain language with a suggested next action." *(reframed to: API error responses include a plain-language message — kept as a backend NFR.)*

**Reliability** — removed frontend behaviors:
- "If the backend is unreachable during a scan attempt, the frontend shall display a timeout message and allow the user to retry — it must not silently fail."
- "The app shall not crash on malformed QR codes — unrecognized QR content shall show \"This QR code is not a Lyfter badge.\"" *(client-side QR parsing)*
- "The gallery page shall load from local state (Vue store) instantly if already fetched, and refresh in the background." *(Vue/Pinia store)*

---

## Section 6 — Scope (In Scope — v1)

Removed/reframed:
- Removed: "QR code scanning via mobile browser camera"
- Reframed: "Badge gallery for attendees (earned badges list)" → "Endpoint returning an attendee's earned badges"
- Removed: "Badge detail view (name, image, event, date earned)" *(backend data still available via endpoint)*
- Reframed: "Admin dashboard: per-event redemption counts per badge" → "Admin stats endpoint: per-event redemption counts per badge"
- Removed: "Badge sharing: image download + Web Share API"
- Reframed: "Deployment: Flask API on Render, Vue SPA on Vercel" → "Deployment: Flask API on Render" *(removed "Vue SPA on Vercel")*

*(Out of Scope — v1 list left intact; those are product-level deferral decisions, not frontend implementation.)*

---

## Section 7 — User Flows

**Flow 1 — "Badge Collector: First Scan"** — entire client journey replaced with a backend API sequence. Removed original steps:
1. "User opens the app URL on their phone (no install required)."
2. "If not logged in → redirected to `/login`. User enters email + password."
3. "On successful auth → JWT stored in `localStorage`. User lands on `/home` (scan entry point)."
4. "User taps \"Scan Badge\" → app requests camera permission via browser."
5. "Camera view opens. User points camera at a QR code at a booth."
6. "App decodes QR URL: `{APP_URL}/scan/{event_id}/{qr_token}`."
7. "App calls `POST /api/redenciones/validar` with `{ event_id, qr_token }` + JWT header." *(kept as backend interaction)*
8. "**Happy path:** API returns `200` with badge data. App navigates to `/badge-ganado/{badge_id}`." *(kept the API response; removed navigation)*
9. "Celebration screen: badge image, name, confetti animation, \"View My Collection\" CTA."
10. "User taps \"View My Collection\" → navigates to `/mis-badges` gallery."
11. "Gallery displays all earned badges as a card grid."

**Flow 2 — "Badge Issuer: Create Badge + Print QR"** — removed UI navigation steps (kept backend generation). Removed:
1. "Admin logs in at `/login` with admin credentials." *(kept as: admin authenticates)*
2. "Admin lands on `/admin/dashboard` — sees event list with redemption totals."
3. "Admin navigates to an existing event → clicks \"Add Badge.\""
4. "Admin fills in: badge name, description, image URL, optional redemption limit." *(kept as request payload)*
5. "Admin clicks \"Create Badge.\""
7. "Admin sees badge detail page with: badge info + rendered QR code image."
8. "Admin clicks \"Download QR\" → QR image downloads to device for printing."
9. "Admin prints QR and places it at the physical booth." *(physical step — kept)*
10. "Admin returns to dashboard throughout the event — sees live redemption count increment." *(reframed to stats endpoint)*

**Flow 3 — Edge Cases** — removed frontend "App shows: ..." display copy; kept API status codes. Removed entire frontend-only rows:
- "QR code is invalid (not a Lyfter URL, corrupted) | Frontend QR parser fails to match expected URL pattern. App shows: \"This QR code doesn't match a Lyfter badge. Try again.\"" *(client-side parsing — removed)*
- "User scans without being logged in | Frontend route guard intercepts before camera opens. User redirected to `/login`." *(client route guard — removed)*
- "Network timeout during redemption API call | Frontend shows retry CTA after 5-second timeout. Badge is not credited until server confirms." *(frontend timeout/retry — removed; "badge not credited until server confirms" retained as backend behavior)*

Removed the "App shows:" frontend copy from the retained rows (409 / 403 / 410 / 401), keeping only the API behavior.

---

## Section 8 — Technical Considerations

**Architecture Overview** — removed frontend node and description:
- Diagram node "[Vue SPA — Vercel]" → reframed to "[Client / API consumer]".
- Removed prose: "The Vue frontend is a static SPA deployed to Vercel CDN. ... There is no server-side rendering. All state management lives in the Vue app (Pinia store) and MongoDB." *(kept: Flask API on Render's free tier, MongoDB Atlas.)*

**QR Code Strategy** — retained (backend generation). `{FRONTEND_URL}` reference in the encoded URL retained because the backend builds that URL; no removal.

**Authentication Flow** — removed:
- "Vue router guard reads token from `localStorage` on every navigation" *(Vue Router + localStorage)*

**Data Model Hints** — retained entirely (backend).

**Key Flask Endpoints** — retained entirely (backend).

**Deployment Notes** — removed/reframed:
- CORS: original "Flask must allow `https://{your-app}.vercel.app` in production. In development, allow `http://localhost:5173` (Vite dev server default). Use `flask-cors` with explicit origin allowlist — no wildcard `*` in production." → reframed to remove Vercel/Vite specifics: "Flask must allow the production frontend domain in production and the local dev frontend origin in development. Use `flask-cors` with an explicit origin allowlist — no wildcard `*` in production."
- Environment variables — removed the frontend block: "Vue (Vercel): `VITE_API_URL`". *(kept the Flask/Render block.)*
- Render cold starts: original "configure Vercel to call it on page load (or use a cron service like UptimeRobot)" → reframed to "configure a keepalive (e.g. UptimeRobot or a client ping)". *(removed "Vercel".)*
- Removed entirely — "Vercel SPA routing" block including the `vercel.json` snippet:
  > **Vercel SPA routing:** Add `vercel.json` with a catch-all rewrite to `index.html` so Vue Router history mode works:
  > ```json
  > { "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }
  > ```

---

## Section 9 — Open Questions

Removed Q7 (frontend/design artifact):
- "**What is the sharing artifact exactly?** | \"Download badge as image\" is in scope. Does the image need branding (Lyfter logo, event name, date)? Does it need the user's name on it? | Needs a design mockup before implementation begins"

Remaining questions renumbered 1–7 (was 1–8).

---

## Section 10 — Launch Criteria

**Functional Checklist** — removed/reframed:
- Reframed: "User can log in and be redirected based on role" → "User can log in and receive a JWT carrying their role" *(removed frontend redirect)*
- Reframed: "Admin can create a badge and see a downloadable QR code" → "Admin can create a badge and receive a downloadable QR code image"
- Reframed: "Attendee can scan QR and earn badge (end-to-end on a real mobile device)" → "Redemption endpoint credits the badge end-to-end for a valid request"
- Reframed: "Earned badge appears in gallery immediately after scan" → "Earned badge is returned by the my-badges endpoint immediately after redemption"
- Reframed: "Duplicate scan shows a friendly message, does not create a duplicate record" → "Duplicate scan returns 409 and does not create a duplicate record"
- Removed: "Invalid QR shows a friendly message, does not crash" *(client-side parsing)*
- Reframed: "Admin dashboard shows correct redemption count per badge" → "Admin stats endpoint returns the correct redemption count per badge"
- Removed: "Badge sharing (download image) works on iOS Safari and Android Chrome"
- Removed: "App is accessible on mobile without installing anything"

**QA Bar** — reframed:
- "CORS verified in production (no console CORS errors from Vercel → Render)" → "CORS verified in production (no CORS errors from the frontend → Render)"

**Performance Threshold** — removed:
- "Gallery load time (50 badges): < 1.5 seconds on 4G (Chrome DevTools throttling)" *(frontend)*

**Stakeholder Sign-Off** — left intact (sign-off roles, including a test-attendee end-to-end check, are product-level acceptance, not frontend implementation detail).
