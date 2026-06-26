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

// Keep the "All" view uncluttered: past/ended events are hidden by default (they still
// have their own Past tab). A persisted toggle brings them back when wanted.
const showPast = ref(localStorage.getItem('eventsShowPast') === '1')
function toggleShowPast() {
  showPast.value = !showPast.value
  try { localStorage.setItem('eventsShowPast', showPast.value ? '1' : '0') } catch { /* storage unavailable */ }
}
const hasPast = computed(() => events.events.some((e) => e.status === 'past'))

const onRefresh = () => events.fetchEvents()

onMounted(() => {
  if (!events.loaded) events.fetchEvents()
})

const visible = computed(() => {
  if (filter.value === 'active') return events.events.filter((e) => e.status === 'active')
  if (filter.value === 'past') return events.events.filter((e) => e.status === 'past')
  // "All": hide past unless the user opts to show it.
  return showPast.value ? events.events : events.events.filter((e) => e.status !== 'past')
})

// Org-grouped feed (P7): cluster the visible events under their organization.
const grouped = computed(() => {
  const m = new Map()
  for (const ev of visible.value) {
    const key = ev.org?.name || '__other__'
    if (!m.has(key)) m.set(key, [])
    m.get(key).push(ev)
  }
  return [...m.entries()].map(([name, list]) => ({ name, list }))
})
</script>

<template>
  <div class="space-y-5 px-4 lg:px-8 pb-4 pt-6">
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

    <label v-if="filter === 'all' && hasPast" class="flex cursor-pointer items-center gap-2 px-1 text-xs text-base-content/60">
      <input type="checkbox" class="toggle toggle-xs" :checked="showPast" @change="toggleShowPast" />
      {{ $t('events.showPast') }}
    </label>

    <AlertMessage type="warning" :message="events.error || ''" />
    <LoadingSpinner v-if="events.loading && !events.loaded" :label="$t('events.loading')" />

    <div v-else-if="visible.length" class="space-y-5">
      <section v-for="g in grouped" :key="g.name" class="space-y-3">
        <h2 class="px-1 text-xs font-semibold uppercase tracking-wide text-base-content/45">{{ g.name === '__other__' ? $t('events.other') : g.name }}</h2>
        <div class="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
          <EventCard
            v-for="ev in g.list"
            :key="ev.id"
            :event="ev"
            @select="router.push(`/events/${ev.id}`)"
          />
        </div>
      </section>
    </div>

    <div v-else class="surface p-8 text-center text-sm text-base-content/60">
      {{ $t('events.empty') }}
    </div>
  </div>
</template>
