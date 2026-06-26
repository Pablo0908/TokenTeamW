<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useEventsStore } from '@/stores/events'
import EventCard from '@/components/domain/EventCard.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'

const router = useRouter()
const events = useEventsStore()

onMounted(() => events.fetchEvents())
</script>

<template>
  <div class="space-y-5">
    <RouterLink to="/admin/events/new" class="btn btn-primary w-full tap-target">
      <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <path d="M12 5v14M5 12h14" />
      </svg>
      {{ $t('admin.newEvent') }}
    </RouterLink>

    <AlertMessage type="warning" :message="events.error || ''" />
    <LoadingSpinner v-if="events.loading && !events.loaded" :label="$t('admin.loadingEvents')" />

    <div v-else-if="events.events.length" class="grid grid-cols-1 gap-3 lg:grid-cols-2 xl:grid-cols-3">
      <EventCard
        v-for="ev in events.events"
        :key="ev.id"
        :event="ev"
        @select="router.push(`/admin/events/${ev.id}`)"
      />
    </div>

    <div v-else class="surface p-8 text-center text-sm text-base-content/60">
      {{ $t('admin.noEventsAdmin') }}
    </div>
  </div>
</template>
