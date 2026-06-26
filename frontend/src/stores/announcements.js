import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, readApiError } from '@/services/api'

// Platform-wide announcements. Any authenticated user can read; only a super_admin
// can create/edit/delete (enforced server-side — the store just calls the endpoints).
export const useAnnouncementsStore = defineStore('announcements', () => {
  const items = ref([])
  const unreadCount = ref(0)
  const error = ref(null)
  const loading = ref(false)
  const loaded = ref(false)

  const hasUnread = computed(() => unreadCount.value > 0)

  async function fetchAnnouncements() {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/announcements')
      items.value = Array.isArray(data?.announcements) ? data.announcements : []
      unreadCount.value = data?.unread_count ?? 0
      loaded.value = true
    } catch (e) {
      error.value = readApiError(e, 'Could not load announcements.')
    } finally {
      loading.value = false
    }
  }

  // Stamp everything read server-side, then clear the local unread markers so the
  // indicators disappear immediately without a refetch.
  async function markSeen() {
    if (!unreadCount.value) return
    try {
      await api.post('/announcements/seen')
      unreadCount.value = 0
      items.value = items.value.map((a) => ({ ...a, unread: false }))
    } catch {
      /* non-critical — indicators simply persist until next successful call */
    }
  }

  async function create(payload) {
    error.value = null
    try {
      const { data } = await api.post('/announcements', payload)
      return data
    } catch (e) {
      error.value = readApiError(e, 'Could not post the announcement.')
      throw e
    }
  }

  async function update(id, payload) {
    error.value = null
    try {
      const { data } = await api.patch(`/announcements/${id}`, payload)
      return data
    } catch (e) {
      error.value = readApiError(e, 'Could not update the announcement.')
      throw e
    }
  }

  async function remove(id) {
    error.value = null
    try {
      await api.delete(`/announcements/${id}`)
    } catch (e) {
      error.value = readApiError(e, 'Could not delete the announcement.')
      throw e
    }
  }

  return {
    items,
    unreadCount,
    error,
    loading,
    loaded,
    hasUnread,
    fetchAnnouncements,
    markSeen,
    create,
    update,
    remove,
  }
})
