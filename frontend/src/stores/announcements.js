import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api, readApiError } from '@/services/api'

export const useAnnouncementsStore = defineStore('announcements', () => {
  const announcements = ref([])
  const error = ref(null)
  const loading = ref(false)
  const loaded = ref(false)

  async function fetchAnnouncements() {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get('/announcements')
      announcements.value = data
      loaded.value = true
    } catch (e) {
      error.value = readApiError(e, 'Could not load announcements.')
    } finally {
      loading.value = false
    }
  }

  async function createAnnouncement(payload) {
    const { data } = await api.post('/admin/announcements', payload)
    announcements.value.unshift(data)
    return data
  }

  async function updateAnnouncement(id, payload) {
    const { data } = await api.put(`/admin/announcements/${id}`, payload)
    const idx = announcements.value.findIndex((a) => a.id === id)
    if (idx !== -1) announcements.value[idx] = data
    return data
  }

  async function deleteAnnouncement(id) {
    await api.delete(`/admin/announcements/${id}`)
    announcements.value = announcements.value.filter((a) => a.id !== id)
  }

  return {
    announcements,
    error,
    loading,
    loaded,
    fetchAnnouncements,
    createAnnouncement,
    updateAnnouncement,
    deleteAnnouncement,
  }
})
