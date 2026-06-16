<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useEventsStore } from '@/stores/events'
import EventCard from '@/components/domain/EventCard.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'

const router = useRouter()
const auth = useAuthStore()
const events = useEventsStore()

onMounted(() => events.fetchEvents())

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="space-y-5 px-4 pb-10 pt-6">
    <header class="flex items-center justify-between">
      <div>
        <p class="text-xs uppercase tracking-wide text-secondary">Organizer</p>
        <h1 class="text-2xl font-bold">Events</h1>
      </div>
      <button class="btn btn-ghost btn-sm tap-target" @click="logout">Log out</button>
    </header>

    <RouterLink to="/admin/events/new" class="btn btn-primary w-full tap-target">
      <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <path d="M12 5v14M5 12h14" />
      </svg>
      New event
    </RouterLink>

    <AlertMessage type="warning" :message="events.error || ''" />
    <LoadingSpinner v-if="events.loading && !events.loaded" label="Loading events…" />

    <div v-else-if="events.events.length" class="space-y-3">
      <EventCard
        v-for="ev in events.events"
        :key="ev.id"
        :event="ev"
        @select="router.push(`/admin/events/${ev.id}`)"
      />
    </div>

    <div v-else class="surface p-8 text-center text-sm text-base-content/60">
      No events yet. Create your first one to start minting badges.
    </div>
  </div>
</template>
