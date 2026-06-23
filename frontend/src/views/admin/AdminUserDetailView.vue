<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUsersStore } from '@/stores/users'
import BadgeCard from '@/components/domain/BadgeCard.vue'
import ProgressBar from '@/components/domain/ProgressBar.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'

const route = useRoute()
const router = useRouter()
const users = useUsersStore()
const id = route.params.id

const data = computed(() => users.current)
const person = computed(() => data.value?.user)
const events = computed(() => data.value?.events ?? [])
const fullName = computed(() =>
  person.value ? [person.value.name, person.value.lastname].filter(Boolean).join(' ') || person.value.email : '',
)

// Every badge this user has actually claimed, flattened across events (for the "claimed badges" section).
const claimed = computed(() =>
  events.value.flatMap((ev) => ev.badges.filter((b) => b.earned).map((b) => ({ ...b, event: ev.event }))),
)

// --- Analytics (activity graph + favorite type + login count) ---
const PERIODS = ['day', 'week', 'month']
const period = ref('day')
const analytics = computed(() => users.analytics)
const activity = computed(() => analytics.value?.activity ?? [])
const maxCount = computed(() => activity.value.reduce((m, b) => Math.max(m, b.count), 0))
const favorite = computed(() => analytics.value?.favorite_event_type || null)

function barLabel(bucket) {
  if (!bucket) return ''
  const d = new Date(bucket)
  if (Number.isNaN(d.getTime())) return ''
  if (period.value === 'month') return d.toLocaleDateString(undefined, { month: 'short', year: '2-digit' })
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}
function barHeight(count) {
  return maxCount.value > 0 ? `${Math.max(6, (count / maxCount.value) * 100)}%` : '6%'
}
function setPeriod(p) {
  if (p === period.value) return
  period.value = p
  users.fetchUserAnalytics(id, p)
}

onMounted(() => {
  users.fetchUserBadges(id)
  users.fetchUserAnalytics(id, period.value)
})
</script>

<template>
  <div class="space-y-5 px-4 pb-10 pt-6">
    <button
      class="tap-target -ml-1 flex items-center gap-1 text-sm text-base-content/70"
      @click="router.push('/admin/users')"
    >
      <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M15 19l-7-7 7-7" />
      </svg>
      Users
    </button>

    <AlertMessage type="warning" :message="users.error || ''" />
    <LoadingSpinner v-if="users.loading && !data" label="Loading progress…" />

    <template v-else-if="person">
      <header class="flex items-center gap-3">
        <span class="grid h-12 w-12 shrink-0 place-items-center rounded-full bg-base-300/60 text-base font-semibold uppercase">
          {{ (person.name || person.email || '?').slice(0, 1) }}
        </span>
        <div class="min-w-0">
          <h1 class="flex items-center gap-2 truncate text-xl font-bold">
            {{ fullName }}
            <span class="badge badge-sm" :class="person.role === 'admin' ? 'badge-secondary' : person.role === 'assistant' ? 'badge-accent' : 'badge-ghost'">{{ person.role }}</span>
          </h1>
          <p class="truncate text-sm text-base-content/55">{{ person.email }}</p>
        </div>
        <div class="ml-auto shrink-0 text-center">
          <p class="text-2xl font-bold leading-none text-primary">{{ person.badges_count ?? 0 }}</p>
          <p class="text-[0.65rem] uppercase tracking-wide text-base-content/45">badges</p>
        </div>
      </header>

      <!-- Analytics -->
      <section v-if="analytics" class="space-y-3">
        <div class="flex items-center justify-between">
          <h2 class="font-semibold">Activity</h2>
          <div role="tablist" class="tabs tabs-boxed tabs-xs bg-base-300/40">
            <button
              v-for="p in PERIODS"
              :key="p"
              role="tab"
              class="tab capitalize"
              :class="{ 'tab-active': period === p }"
              @click="setPeriod(p)"
            >{{ p }}</button>
          </div>
        </div>

        <div class="surface p-4">
          <div v-if="activity.length" class="flex h-32 items-end gap-1">
            <div
              v-for="b in activity"
              :key="b.bucket"
              class="group relative flex-1 rounded-t bg-primary/70 transition-colors hover:bg-primary"
              :style="{ height: barHeight(b.count) }"
              :title="`${barLabel(b.bucket)}: ${b.count}`"
            />
          </div>
          <p v-else class="py-8 text-center text-sm text-base-content/50">No activity in range.</p>
          <div v-if="activity.length" class="mt-2 flex justify-between text-[0.65rem] text-base-content/45">
            <span>{{ barLabel(activity[0].bucket) }}</span>
            <span>{{ barLabel(activity[activity.length - 1].bucket) }}</span>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div class="surface p-4">
            <p class="text-[0.65rem] uppercase tracking-wide text-base-content/45">Favorite type</p>
            <p class="mt-1 truncate font-semibold capitalize">
              {{ favorite ? favorite.event_type : '—' }}
              <span v-if="favorite?.tie" class="text-[0.6rem] font-normal text-base-content/45">(tie)</span>
            </p>
          </div>
          <div v-if="'login_count' in analytics" class="surface p-4">
            <p class="text-[0.65rem] uppercase tracking-wide text-base-content/45">Logins</p>
            <p class="mt-1 font-semibold">{{ analytics.login_count }}</p>
          </div>
        </div>
      </section>

      <!-- Progress per event -->
      <section class="space-y-3">
        <h2 class="font-semibold">Progress by event</h2>
        <div v-if="events.length" class="space-y-3">
          <div v-for="ev in events" :key="ev.event_id" class="surface p-4">
            <div class="mb-2 flex items-center justify-between gap-2">
              <p class="truncate font-medium">{{ ev.event }}</p>
              <span
                class="badge badge-sm shrink-0"
                :class="ev.completed ? 'badge-success' : ev.status === 'active' ? 'badge-primary' : 'badge-ghost'"
              >{{ ev.completed ? 'Completed' : ev.status }}</span>
            </div>
            <ProgressBar :value="ev.badges_earned" :max="ev.badges_total" />
          </div>
        </div>
        <p v-else class="surface p-6 text-center text-sm text-base-content/50">None</p>
      </section>

      <!-- Claimed badges -->
      <section class="space-y-3">
        <h2 class="font-semibold">Claimed badges</h2>
        <div v-if="claimed.length" class="grid grid-cols-3 gap-3">
          <BadgeCard v-for="b in claimed" :key="b.id" :badge="b" />
        </div>
        <p v-else class="surface p-6 text-center text-sm text-base-content/50">None</p>
      </section>
    </template>
  </div>
</template>
