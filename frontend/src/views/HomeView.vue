<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useBadgesStore } from '@/stores/badges'
import { useEventsStore } from '@/stores/events'
import StatTile from '@/components/domain/StatTile.vue'
import BadgeCard from '@/components/domain/BadgeCard.vue'
import EventCard from '@/components/domain/EventCard.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'

const router = useRouter()
const auth = useAuthStore()
const badges = useBadgesStore()
const events = useEventsStore()

onMounted(() => {
  if (!badges.loaded) badges.fetchMyBadges()
  if (!events.loaded) events.fetchEvents()
})

const WEEK = 7 * 24 * 60 * 60 * 1000
const newThisWeek = computed(
  () =>
    badges.earnedBadges.filter((b) => {
      const t = new Date(b.date).getTime()
      return !Number.isNaN(t) && Date.now() - t <= WEEK
    }).length,
)
const streak = computed(() => new Set(badges.earnedBadges.map((b) => b.date).filter(Boolean)).size)

const previewBadges = computed(() => badges.allBadges.slice(0, 4))

const order = { active: 0, upcoming: 1, past: 2 }
const previewEvents = computed(() =>
  [...events.events].sort((a, b) => (order[a.status] ?? 3) - (order[b.status] ?? 3)).slice(0, 2),
)

const loading = computed(() => badges.loading && !badges.loaded)
</script>

<template>
  <div class="space-y-6 px-4 pb-4 pt-6">
    <!-- Header -->
    <header class="flex items-start justify-between">
      <div>
        <h1 class="text-2xl font-bold">Hey, {{ auth.displayName }}</h1>
        <p class="text-sm text-base-content/60">
          {{ newThisWeek }} new badge{{ newThisWeek === 1 ? '' : 's' }} this week
        </p>
      </div>
      <span class="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-primary to-info text-xl shadow-lg shadow-primary/20">
        🏅
      </span>
    </header>

    <AlertMessage type="warning" :message="badges.error || ''" />

    <!-- Stats -->
    <section class="grid grid-cols-3 gap-3">
      <StatTile :value="badges.totalEarned" label="Badges" tone="primary" />
      <StatTile :value="badges.eventsCount" label="Events" tone="secondary" />
      <StatTile :value="streak" label="Streak" tone="accent" />
    </section>

    <!-- Scan CTA -->
    <button
      type="button"
      class="surface flex w-full items-center gap-4 bg-gradient-to-r from-primary/20 to-secondary/15 p-4 text-left transition-transform active:scale-[0.98]"
      @click="router.push('/scan')"
    >
      <span class="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-primary/20 text-primary">
        <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
          <path d="M7 3.75h-1A2.25 2.25 0 003.75 6v1M17 3.75h1A2.25 2.25 0 0120.25 6v1M7 20.25h-1A2.25 2.25 0 013.75 18v-1M17 20.25h1A2.25 2.25 0 0020.25 18v-1" />
          <path d="M3.75 12h16.5" />
        </svg>
      </span>
      <span>
        <span class="block font-semibold">Scan a QR code</span>
        <span class="block text-sm text-base-content/60">Point at any event badge station</span>
      </span>
    </button>

    <LoadingSpinner v-if="loading" label="Loading your badges…" />

    <template v-else>
      <!-- My badges -->
      <section class="space-y-3">
        <div class="flex items-center justify-between">
          <h2 class="font-semibold">My badges</h2>
          <RouterLink to="/badges" class="text-sm font-medium text-primary tap-target">see all</RouterLink>
        </div>
        <div v-if="previewBadges.length" class="grid grid-cols-4 gap-2.5">
          <BadgeCard v-for="b in previewBadges" :key="b.id" :badge="b" />
        </div>
        <p v-else class="text-sm text-base-content/50">No badges yet — scan your first one!</p>
      </section>

      <!-- Events -->
      <section class="space-y-3">
        <div class="flex items-center justify-between">
          <h2 class="font-semibold">Events</h2>
          <RouterLink to="/events" class="text-sm font-medium text-primary tap-target">see all</RouterLink>
        </div>
        <div class="space-y-3">
          <EventCard
            v-for="ev in previewEvents"
            :key="ev.id"
            :event="ev"
            @select="router.push(`/events/${ev.id}`)"
          />
        </div>
      </section>
    </template>
  </div>
</template>
