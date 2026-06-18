import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, readApiError } from '@/services/api'

// Admin-only: the registered-user directory with per-user badge counts, plus
// role promotion/demotion. Backed by GET /admin/users and PATCH /admin/users/<id>/role.
export const useUsersStore = defineStore('users', () => {
  const users = ref([])
  const current = ref(null) // { user, events } for the user being inspected
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

  return { users, current, error, loading, loaded, adminCount, assistantCount, attendeeCount, fetchUsers, fetchUserBadges, setRole }
})
