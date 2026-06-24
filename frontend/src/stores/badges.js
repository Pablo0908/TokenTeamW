import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, readApiError } from '@/services/api'
import { t } from '@/i18n'

const readError = (e) => readApiError(e, t('errors.badges'))

export const useBadgesStore = defineStore('badges', () => {
  const groups = ref([])
  const error = ref(null)
  const loading = ref(false)
  const loaded = ref(false)
  const lastEarned = ref(null)
  // Authoritative consecutive-event-day streak, computed server-side (GET /me/streak).
  const streak = ref(0)

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
  async function fetchStreak() {
    try {
      const { data } = await api.get('/me/streak')
      streak.value = Number(data?.streak) || 0
    } catch {
      /* non-critical: leave the previous value in place */
    }
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
