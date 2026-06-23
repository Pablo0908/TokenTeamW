import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, readApiError } from '@/services/api'
import { t } from '@/i18n'

const readError = (e) => readApiError(e, t('errors.events'))

export const useEventsStore = defineStore('events', () => {
  const events = ref([])
  const current = ref(null)
  const adminBadges = ref([])
  const error = ref(null)
  const loading = ref(false)
  const loaded = ref(false)

  const activeEvents = computed(() => events.value.filter((e) => e.status === 'active'))
  const pastEvents = computed(() => events.value.filter((e) => e.status === 'past'))

  async function fetchEvents() {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/events/')
      events.value = Array.isArray(data) ? data : (data.events ?? [])
      loaded.value = true
    } catch (e) {
      error.value = readError(e)
    } finally {
      loading.value = false
    }
  }

  async function fetchEvent(id) {
    loading.value = true
    error.value = null
    current.value = null
    try {
      const { data } = await api.get(`/events/${id}`)
      current.value = data
      return data
    } catch (e) {
      error.value = readError(e)
      return null
    } finally {
      loading.value = false
    }
  }

  async function createEvent(payload) {
    error.value = null
    try {
      const { data } = await api.post('/admin/event', payload)
      return data
    } catch (e) {
      error.value = readApiError(e, 'Could not create the event.')
      throw e
    }
  }

  // Event/badge management hits the platform /admin path by default. Passing an
  // orgId routes to the org-scoped endpoints instead, so the same management UI
  // works for org owners/admins (who may not hold the legacy global admin role).
  const badgeBase = (eventId, orgId) =>
    orgId ? `/orgs/${orgId}/events/${eventId}` : `/admin/events/${eventId}`

  async function addBadge(eventId, payload, orgId = null) {
    error.value = null
    try {
      const { data } = await api.post(`${badgeBase(eventId, orgId)}/badge`, payload)
      return data
    } catch (e) {
      error.value = readApiError(e, 'Could not create the badge.')
      throw e
    }
  }

  // Create many badges at once. `badges` is an array of { name, description?, icon?, color? }.
  async function addBadgesBulk(eventId, badgesList, orgId = null) {
    error.value = null
    try {
      const { data } = await api.post(`${badgeBase(eventId, orgId)}/badges/bulk`, { badges: badgesList })
      return data // { created: [...], count }
    } catch (e) {
      error.value = readApiError(e, 'Could not create the badges.')
      throw e
    }
  }

  // Start/stop an event (manual activation override). orgId routes to the org path.
  async function setEventStarted(eventId, started, orgId = null) {
    error.value = null
    try {
      const { data } = await api.patch(`${badgeBase(eventId, orgId)}/status`, { started })
      return data // { id, started, status }
    } catch (e) {
      error.value = readApiError(e, 'Could not update the event status.')
      throw e
    }
  }

  async function fetchAdminBadges(eventId, orgId = null) {
    error.value = null
    try {
      const { data } = await api.get(`${badgeBase(eventId, orgId)}/badges`)
      adminBadges.value = Array.isArray(data) ? data : []
      return adminBadges.value
    } catch (e) {
      error.value = readError(e)
      return []
    }
  }

  return {
    events,
    current,
    adminBadges,
    error,
    loading,
    loaded,
    activeEvents,
    pastEvents,
    fetchEvents,
    fetchEvent,
    createEvent,
    addBadge,
    addBadgesBulk,
    setEventStarted,
    fetchAdminBadges,
  }
})
