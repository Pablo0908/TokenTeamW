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

  async function addBadge(eventId, payload) {
    error.value = null
    try {
      const { data } = await api.post(`/admin/events/${eventId}/badge`, payload)
      return data
    } catch (e) {
      error.value = readApiError(e, 'Could not create the badge.')
      throw e
    }
  }

  async function fetchAdminBadges(eventId) {
    error.value = null
    try {
      const { data } = await api.get(`/admin/events/${eventId}/badges`)
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
    fetchAdminBadges,
  }
})
