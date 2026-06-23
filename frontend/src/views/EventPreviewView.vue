<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import EventPreviewCard from '@/components/domain/EventPreviewCard.vue'

const route  = useRoute()
const router = useRouter()
const auth   = useAuthStore()

const loading   = ref(true)
const eventData = ref(null)

onMounted(async () => {
  // Authenticated users don't need the pre-login landing — send them home.
  if (auth.isAuthenticated) {
    router.replace({ name: 'home' })
    return
  }
  try {
    const { data } = await api.get(`/events/${route.params.eventId}/preview`)
    eventData.value = data
  } catch {
    // silently fall back to card defaults if endpoint doesn't exist yet
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-if="loading" class="min-h-screen bg-[#0a0b10] flex items-center justify-center">
    <span class="loading loading-spinner loading-lg text-primary"></span>
  </div>

  <EventPreviewCard
    v-else-if="eventData"
    :event-name="eventData.name"
    :event-status="eventData.status_label ?? 'En vivo'"
  />

  <!-- fallback with defaults while /preview endpoint is pending -->
  <EventPreviewCard v-else />
</template>
