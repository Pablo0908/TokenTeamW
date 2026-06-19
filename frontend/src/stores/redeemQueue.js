import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/services/api'
import { t } from '@/i18n'

// Offline redemption queue. Event venues often have poor connectivity, so a scan made
// while offline is saved here (localStorage) and replayed automatically when the
// connection returns (and on app start / when the Scan screen opens).
const KEY = 'lyfter_redeem_queue'

function load() {
  try {
    const v = JSON.parse(localStorage.getItem(KEY) || '[]')
    return Array.isArray(v) ? v : []
  } catch {
    return []
  }
}

export const useRedeemQueueStore = defineStore('redeemQueue', () => {
  const queue = ref(load())
  const syncing = ref(false)
  const syncMessage = ref('') // surfaced as a toast by App.vue
  const pending = computed(() => queue.value.length)

  function persist() {
    try {
      localStorage.setItem(KEY, JSON.stringify(queue.value))
    } catch {
      /* storage unavailable */
    }
  }

  // Add a scan to the queue (deduped on event+token).
  function enqueue(eventId, token) {
    if (!queue.value.some((i) => i.eventId === eventId && i.token === token)) {
      queue.value = [...queue.value, { eventId, token, queuedAt: Date.now() }]
      persist()
    }
  }

  // Replay queued redemptions. Successes and permanently-resolved items (already owned /
  // invalid) are dropped; still-offline items are kept for the next attempt.
  async function flush() {
    if (syncing.value || !queue.value.length) return
    if (typeof navigator !== 'undefined' && navigator.onLine === false) return
    const { useAuthStore } = await import('@/stores/auth')
    if (!useAuthStore().isAuthenticated) return

    syncing.value = true
    let earned = 0
    let already = 0
    let failed = 0
    const remaining = []
    try {
      for (const item of queue.value) {
        try {
          await api.get(`/redeem/${item.eventId}/${item.token}`)
          earned += 1
        } catch (e) {
          const status = e.response?.status
          if (status === 409) already += 1 // already owned → resolved
          else if (status === 403 || status === 410) failed += 1 // invalid / limit → drop
          else if (status === 401) {
            remaining.push(item) // session expired → keep, stop trying
            break
          } else if (!e.response) {
            remaining.push(item) // still offline → keep
          } else failed += 1
        }
      }
    } finally {
      queue.value = remaining
      persist()
      syncing.value = false
    }

    const done = earned + already
    if (done > 0) {
      syncMessage.value =
        done === 1 ? t('queue.syncedOne') : t('queue.syncedMany', { n: done })
      // Refresh the gallery so newly synced badges appear.
      const { useBadgesStore } = await import('@/stores/badges')
      useBadgesStore().fetchMyBadges()
    } else if (failed > 0) {
      syncMessage.value = t('queue.syncFailed')
    }
  }

  function clearMessage() {
    syncMessage.value = ''
  }

  // Replay on reconnect + once at startup. Idempotent — safe to call repeatedly.
  let wired = false
  function init() {
    if (typeof window === 'undefined' || wired) return
    wired = true
    window.addEventListener('online', () => flush())
    flush()
  }

  return { queue, pending, syncing, syncMessage, enqueue, flush, init, clearMessage }
})
