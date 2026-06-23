import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, readApiError } from '@/services/api'

// Admin-only: the registered-user directory with per-user badge counts, plus
// role promotion/demotion. Backed by GET /admin/users and PATCH /admin/users/<id>/role.
export const useUsersStore = defineStore('users', () => {
  const users = ref([])
  const current = ref(null) // { user, events } for the user being inspected
  const analytics = ref(null) // { activity, favorite_event_type, login_count? } for that user
  const error = ref(null)
  const loading = ref(false)
  const loaded = ref(false)

  const adminCount = computed(() => users.value.filter((u) => u.role === 'admin').length)
  const assistantCount = computed(() => users.value.filter((u) => u.role === 'assistant').length)
  const attendeeCount = computed(() => users.value.filter((u) => u.role === 'attendee').length)

  async function fetchUsers() {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/admin/users')
      users.value = Array.isArray(data) ? data : (data.users ?? [])
      loaded.value = true
    } catch (e) {
      error.value = readApiError(e, 'Could not load users. Please try again.')
    } finally {
      loading.value = false
    }
  }

  // One user's progress across every event, with the badges they've claimed.
  async function fetchUserBadges(id) {
    loading.value = true
    error.value = null
    current.value = null
    try {
      const { data } = await api.get(`/admin/users/${id}/badges`)
      current.value = data
      return data
    } catch (e) {
      error.value = readApiError(e, "Could not load this user's progress.")
      return null
    } finally {
      loading.value = false
    }
  }

  // Per-user analytics (activity graph, favorite event type, login count). Tier-scoped
  // server-side. Supplementary — failures don't disrupt the rest of the detail view.
  async function fetchUserAnalytics(id, period = 'day') {
    try {
      const { data } = await api.get(`/admin/users/${id}/analytics`, { params: { period } })
      analytics.value = data
      return data
    } catch {
      analytics.value = null
      return null
    }
  }

  // Promote ('admin') or demote ('attendee'). Optimistic update on success.
  async function setRole(id, role) {
    error.value = null
    try {
      await api.patch(`/admin/users/${id}/role`, { role })
      const u = users.value.find((x) => x.id === id)
      if (u) u.role = role
      return true
    } catch (e) {
      error.value = readApiError(e, 'Could not update the role.')
      throw e
    }
  }

  async function disableUser(id, disabled) {
    error.value = null
    try {
      await api.patch(`/admin/users/${id}/disable`, { disabled })
      const u = users.value.find((x) => x.id === id)
      if (u) u.disabled = disabled
      return true
    } catch (e) {
      error.value = readApiError(e, 'Could not update the account status.')
      throw e
    }
  }

  async function deleteUser(id) {
    error.value = null
    try {
      await api.delete(`/admin/users/${id}`)
      users.value = users.value.filter((x) => x.id !== id)
      return true
    } catch (e) {
      error.value = readApiError(e, 'Could not delete the account.')
      throw e
    }
  }

  return { users, current, analytics, error, loading, loaded, adminCount, assistantCount, attendeeCount, fetchUsers, fetchUserBadges, fetchUserAnalytics, setRole, disableUser, deleteUser }
})
