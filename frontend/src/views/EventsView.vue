<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useEventsStore } from '@/stores/events'
import EventCard from '@/components/domain/EventCard.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'
import PullToRefresh from '@/components/ui/PullToRefresh.vue'

const router = useRouter()
const events = useEventsStore()

const filters = ['all', 'active', 'past']
const filter = ref('all')

const onRefresh = () => events.fetchEvents()

onMounted(() => {
  if (!events.loaded) events.fetchEvents()
})

const visible = computed(() => {
  if (filter.value === 'active') return events.events.filter((e) => e.status === 'active')
  if (filter.value === 'past') return events.events.filter((e) => e.status === 'past')
  return events.events
})
</script>

<template>
  <div class="space-y-5 px-4 pb-4 pt-6">
    <PullToRefresh :on-refresh="onRefresh" />
    <header>
      <h1 class="text-2xl font-bold">{{ $t('events.title') }}</h1>
    </header>

    <div role="tablist" class="flex gap-2">
      <button
        v-for="f in filters"
        :key="f"
        role="tab"
        :aria-selected="filter === f"
        class="tap-target flex-1 rounded-full px-4 py-2 text-sm font-medium transition-colors"
        :class="filter === f ? 'bg-primary text-primary-content' : 'bg-base-100/60 text-base-content/60'"
        @click="filter = f"
      >
        {{ $t('events.' + f) }}
      </button>
    </div>

    <AlertMessage type="warning" :message="events.error || ''" />
    <LoadingSpinner v-if="events.loading && !events.loaded" :label="$t('events.loading')" />

    <div v-else-if="visible.length" class="space-y-3">
      <EventCard
        v-for="ev in visible"
        :key="ev.id"
        :event="ev"
        @select="router.push(`/events/${ev.id}`)"
      />
    </div>

    <div v-else class="surface p-8 text-center text-sm text-base-content/60">
      {{ $t('events.empty') }}
    </div>
  </div>
</template>
