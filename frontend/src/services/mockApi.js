// In-memory demo backend that mirrors the Flask API contract (see Technical-Design-Frontend §3).
// Active only when VITE_USE_MOCK=true. State persists for the page session so the full
// scan -> earn -> profile flow is demoable without the real backend.

const DELAY = 420

const ok = (value, ms = DELAY) =>
  new Promise((resolve) => setTimeout(() => resolve({ data: value }), ms))

const err = (status, message, ms = DELAY) =>
  new Promise((_, reject) => setTimeout(() => reject({ response: { status, data: { error: message } } }), ms))

let eventSeq = 100
let badgeSeq = 100

const db = {
  attendee: { id: 'u_john', name: 'John', lastname: 'Rivas', username: 'john', email: 'john@lyfter.cc', role: 'attendee' },
  events: [
    {
      id: 'ev_cit',
      name: 'CIT Hackathon 2025',
      description: '48 hours of building, mentoring and demos across every booth.',
      date: '2026-06-14',
      endDate: '2026-06-15',
      location: 'San José, CR',
      prize: 'VIP pass to Lyfter Conf 2027',
      status: 'active',
      badges: [
        { id: 'b_cit1', name: 'First scan', description: 'Scanned your first booth', icon: '🔗', color: 'primary', token: 'cit-first', earnedAt: '2026-06-14', redeemedBy: 41 },
        { id: 'b_cit2', name: 'Explorer', description: 'Visited 3 sponsor booths', icon: '🧭', color: 'success', token: 'cit-explorer', earnedAt: '2026-06-14', redeemedBy: 33 },
        { id: 'b_cit3', name: 'Streak', description: 'Scanned 3 days in a row', icon: '🔥', color: 'error', token: 'cit-streak', earnedAt: null, redeemedBy: 18 },
        { id: 'b_cit4', name: 'Top 10', description: 'Finished in the top 10', icon: '🏆', color: 'secondary', token: 'cit-top10', earnedAt: null, redeemedBy: 9 },
        { id: 'b_cit5', name: 'Closing', description: 'Attended the closing keynote', icon: '🎤', color: 'info', token: 'cit-closing', earnedAt: null, redeemedBy: 5 },
      ],
    },
    {
      id: 'ev_techfair',
      name: 'Tech Fair 2025',
      description: 'Meet the sponsors, try the demos and collect the fair set.',
      date: '2026-06-20',
      endDate: '2026-06-20',
      location: 'Cartago, CR',
      prize: 'Lyfter swag kit',
      status: 'upcoming',
      badges: [
        { id: 'b_tf1', name: 'Welcome', description: 'Checked in at the entrance', icon: '🎟️', color: 'info', token: 'tf-welcome', earnedAt: null, redeemedBy: 0 },
        { id: 'b_tf2', name: 'Sponsor', description: 'Visited a sponsor booth', icon: '🤝', color: 'secondary', token: 'tf-sponsor', earnedAt: null, redeemedBy: 0 },
        { id: 'b_tf3', name: 'Workshop', description: 'Joined a hands-on workshop', icon: '🛠️', color: 'warning', token: 'tf-workshop', earnedAt: null, redeemedBy: 0 },
      ],
    },
    {
      id: 'ev_devsummit',
      name: 'Dev Summit',
      description: 'A full day of talks, lightning sessions and hallway track.',
      date: '2026-05-09',
      endDate: '2026-05-09',
      location: 'Heredia, CR',
      prize: 'Summit certificate + hoodie',
      status: 'past',
      badges: [
        { id: 'b_ds1', name: 'Keynote', description: 'Attended the opening keynote', icon: '⭐', color: 'warning', token: 'ds-keynote', earnedAt: '2026-05-09', redeemedBy: 58 },
        { id: 'b_ds2', name: 'Hallway', description: 'Joined the hallway track', icon: '🗣️', color: 'info', token: 'ds-hallway', earnedAt: '2026-05-09', redeemedBy: 47 },
        { id: 'b_ds3', name: 'Lightning', description: 'Watched the lightning talks', icon: '⚡', color: 'accent', token: 'ds-lightning', earnedAt: '2026-05-09', redeemedBy: 39 },
        { id: 'b_ds4', name: 'Closing', description: 'Stayed for the closing party', icon: '🎉', color: 'success', token: 'ds-closing', earnedAt: '2026-05-09', redeemedBy: 44 },
      ],
    },
  ],
}

const summary = (ev) => {
  const total = ev.badges.length
  const earned = ev.badges.filter((b) => b.earnedAt).length
  return {
    id: ev.id,
    name: ev.name,
    description: ev.description,
    date: ev.date,
    endDate: ev.endDate,
    location: ev.location,
    prize: ev.prize,
    status: ev.status,
    badges_total: total,
    badges_earned: earned,
    completed: total > 0 && earned === total,
  }
}

const publicBadge = (b) => ({
  id: b.id,
  name: b.name,
  description: b.description,
  icon: b.icon,
  color: b.color,
  earned: !!b.earnedAt,
  date: b.earnedAt,
})

const base = () => import.meta.env.VITE_PUBLIC_URL || window.location.origin
const today = () => new Date().toISOString().slice(0, 10)

function login(body) {
  const email = (body?.email || '').trim().toLowerCase()
  if (!email || !body?.password) return err(400, 'Email and password are required.')
  const isAdmin = email.includes('admin')
  const role = isAdmin ? 'admin' : 'attendee'
  const user = isAdmin
    ? { id: 'u_admin', name: 'Diego', lastname: 'Soto', username: 'diego', email, role }
    : { ...db.attendee, email }
  return ok({ token: `demo.${btoa(email)}.jwt`, role, user })
}

function register(body) {
  if (!body?.email || !body?.password || !body?.name) {
    return err(400, 'Name, email and password are required.')
  }
  return ok({ message: 'Account created', user_id: `u_${Math.random().toString(36).slice(2, 8)}` }, 600)
}

function listEvents() {
  return ok(db.events.map(summary))
}

function getEvent(id) {
  const ev = db.events.find((e) => e.id === id)
  if (!ev) return err(404, 'Event not found.')
  return ok({ ...summary(ev), badges: ev.badges.map(publicBadge) })
}

function myBadges() {
  return ok(
    db.events.map((ev) => {
      const earned = ev.badges.filter((b) => b.earnedAt)
      return {
        event_id: ev.id,
        event: ev.name,
        date: ev.date,
        status: ev.status,
        prize: ev.prize,
        badges_total: ev.badges.length,
        badges_earned: earned.length,
        completed: ev.badges.length > 0 && earned.length === ev.badges.length,
        badges: ev.badges.map(publicBadge),
      }
    }),
  )
}

function redeem(eventId, token) {
  const ev = db.events.find((e) => e.id === eventId)
  if (!ev) return err(403, 'This badge isn’t available right now.')
  const badge = ev.badges.find((b) => b.token === token)
  if (!badge) return err(403, 'This QR code is not a Lyfter badge.')
  if (badge.earnedAt) return err(409, 'You already have this badge.')
  badge.earnedAt = today()
  badge.redeemedBy += 1
  const earned = ev.badges.filter((b) => b.earnedAt).length
  const completed = earned === ev.badges.length
  return ok(
    {
      message: completed ? '¡Event completed!' : 'Badge earned',
      badge: publicBadge(badge),
      event: ev.name,
      event_id: ev.id,
      event_completed: completed,
      prize: completed ? ev.prize : null,
      badges_earned: earned,
      badges_total: ev.badges.length,
    },
    700,
  )
}

function createEvent(body) {
  if (!body?.name) return err(400, 'Event name is required.')
  const ev = {
    id: `ev_${++eventSeq}`,
    name: body.name,
    description: body.description || '',
    date: body.date || body.start_date || '',
    endDate: body.end_date || '',
    location: body.location || '',
    prize: body.prize || '',
    status: 'upcoming',
    badges: [],
  }
  db.events.unshift(ev)
  return ok({ id: ev.id, name: ev.name }, 600)
}

function addBadge(eventId, body) {
  const ev = db.events.find((e) => e.id === eventId)
  if (!ev) return err(404, 'Event not found.')
  if (!body?.name) return err(400, 'Badge name is required.')
  const token = `tok_${Math.random().toString(36).slice(2, 10)}`
  const badge = {
    id: `b_${++badgeSeq}`,
    name: body.name,
    description: body.description || '',
    icon: body.icon || '🏅',
    color: body.color || 'primary',
    image: body.image || '',
    token,
    earnedAt: null,
    redeemedBy: 0,
  }
  ev.badges.push(badge)
  return ok(
    {
      id: badge.id,
      name: badge.name,
      token,
      qr_url: `${base()}/redeem/${ev.id}/${token}`,
      redeem_path: `/redeem/${ev.id}/${token}`,
    },
    600,
  )
}

function adminBadges(eventId) {
  const ev = db.events.find((e) => e.id === eventId)
  if (!ev) return err(404, 'Event not found.')
  // Simulate a live redemption count ticking up while the dashboard polls.
  const pick = ev.badges[Math.floor(Math.random() * ev.badges.length)]
  if (pick && pick.redeemedBy < 60) pick.redeemedBy += Math.random() < 0.4 ? 1 : 0
  return ok(
    ev.badges.map((b) => ({
      id: b.id,
      name: b.name,
      description: b.description,
      icon: b.icon,
      color: b.color,
      token: b.token,
      qr_url: `${base()}/redeem/${ev.id}/${b.token}`,
      redeem_path: `/redeem/${ev.id}/${b.token}`,
      redeemed_by: b.redeemedBy,
      total_attendees: 60,
    })),
  )
}

const path = (url) => url.split('?')[0]

export const mockApi = {
  get(url) {
    const p = path(url)
    let m
    if (p === '/events' || p === '/events/') return listEvents()
    if ((m = p.match(/^\/admin\/events\/([^/]+)\/badges$/))) return adminBadges(m[1])
    if ((m = p.match(/^\/events\/([^/]+)$/))) return getEvent(m[1])
    if (p === '/me/badges') return myBadges()
    if ((m = p.match(/^\/redeem\/([^/]+)\/([^/]+)$/))) return redeem(m[1], m[2])
    return err(404, `Not found (mock): ${p}`)
  },
  post(url, body) {
    const p = path(url)
    let m
    if (p === '/auth/login') return login(body)
    if (p === '/auth/register') return register(body)
    if (p === '/admin/event') return createEvent(body)
    if ((m = p.match(/^\/admin\/events\/([^/]+)\/badge$/))) return addBadge(m[1], body)
    return err(404, `Not found (mock): ${p}`)
  },
}
