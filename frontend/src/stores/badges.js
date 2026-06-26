import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, readApiError } from '@/services/api'
import { t } from '@/i18n'
import { useAuthStore } from '@/stores/auth'

const readError = (e) => readApiError(e, t('errors.badges'))

// Per-user "high-water-mark" of the streak we've already shown the user, persisted across
// sessions. We celebrate only when the freshly fetched streak EXCEEDS this mark — so the
// first load (or a re-fetch with no change) never triggers the animation, but a genuine
// increase does, whether it came from scanning live or from the value changing between visits.
function streakSeenKey() {
  const uid = useAuthStore().user?.id ?? 'anon'
  return `lyfter_streak_seen_${uid}`
}
function readStreakSeen() {
  try {
    const v = localStorage.getItem(streakSeenKey())
    return v == null ? null : Number(v)
  } catch {
    return null
  }
}
function writeStreakSeen(n) {
  try {
    localStorage.setItem(streakSeenKey(), String(n))
  } catch {
    /* storage unavailable — degrade gracefully (just won't celebrate next session) */
  }
}

export const useBadgesStore = defineStore('badges', () => {
  const groups = ref([])
  const error = ref(null)
  const loading = ref(false)
  const loaded = ref(false)
  const lastEarned = ref(null)
  // Authoritative consecutive-event-day streak, computed server-side (GET /me/streak).
  const streak = ref(0)
  // When a streak increase is detected, holds { from, to } and the global StreakUpOverlay
  // plays the full-screen celebration; null when nothing should be playing.
  const streakCelebration = ref(null)

  const allBadges = computed(() => groups.value.flatMap((g) => g.badges.map((b) => ({ ...b, event: g.event }))))
  const earnedBadges = computed(() => allBadges.value.filter((b) => b.earned))
  const totalEarned = computed(() => earnedBadges.value.length)
  const eventsCount = computed(() => groups.value.length)
  const completedEvents = computed(() => groups.value.filter((g) => g.completed).length)

  async function fetchMyBadges() {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/me/badges')
      groups.value = Array.isArray(data) ? data : (data.events ?? [])
      loaded.value = true
    } catch (e) {
      error.value = readError(e)
    } finally {
      loading.value = false
    }
  }

  // Authoritative streak from the backend (consecutive event-days of completed events).
  // Detects a genuine increase vs. the persisted high-water-mark and arms the celebration.
  async function fetchStreak() {
    try {
      const { data } = await api.get('/me/streak')
      const next = Number(data?.streak) || 0
      streak.value = next
      const seen = readStreakSeen()
      // seen === null → first time we've ever recorded this user's streak: don't celebrate.
      if (seen !== null && next > seen) {
        streakCelebration.value = { from: seen, to: next }
      }
      writeStreakSeen(next)
    } catch {
      /* non-critical: leave the previous value in place */
    }
  }

  function clearStreakCelebration() {
    streakCelebration.value = null
  }

  // Public QR redemption. Returns the result payload (caller drives the celebration UI).
  async function redeem(eventId, token) {
    error.value = null
    try {
      const { data } = await api.get(`/redeem/${eventId}/${token}`)
      lastEarned.value = data
      loaded.value = false // gallery should refetch next time it opens
      fetchStreak() // completing an event may advance the streak — refresh it
      return { ok: true, data }
    } catch (e) {
      // No HTTP response (or the browser reports offline) ⇒ a network failure the caller
      // can recover from by queueing the scan for later sync.
      const offline = !e.response || (typeof navigator !== 'undefined' && navigator.onLine === false)
      return { ok: false, offline, status: e.response?.status, error: readError(e) }
    }
  }

  return {
    groups,
    error,
    loading,
    loaded,
    lastEarned,
    streak,
    streakCelebration,
    clearStreakCelebration,
    allBadges,
    earnedBadges,
    totalEarned,
    eventsCount,
    completedEvents,
    fetchMyBadges,
    fetchStreak,
    redeem,
  }
})
