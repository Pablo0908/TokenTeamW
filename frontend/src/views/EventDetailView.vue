<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { locale } from '@/i18n'
import { useEventsStore } from '@/stores/events'
import BadgeCard from '@/components/domain/BadgeCard.vue'
import ProgressBar from '@/components/domain/ProgressBar.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'

const route = useRoute()
const router = useRouter()
const events = useEventsStore()

const ev = computed(() => events.current)
// Derive from the per-badge flags (always present on the detail payload); fall back to
// server aggregates if the badge list is absent.
const total = computed(() => ev.value?.badges?.length ?? ev.value?.badges_total ?? 0)
const earned = computed(() =>
  ev.value?.badges ? ev.value.badges.filter((b) => b.earned).length : (ev.value?.badges_earned ?? 0),
)
const completed = computed(() => ev.value?.completed || (total.value > 0 && earned.value >= total.value))

const dateLabel = computed(() => {
  if (!ev.value) return ''
  const fmt = (iso) => {
    const d = new Date(iso)
    return Number.isNaN(d.getTime()) ? '' : d.toLocaleDateString(locale.value === 'es' ? 'es' : 'en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }
  const s = fmt(ev.value.date)
  const e = ev.value.endDate ? fmt(ev.value.endDate) : ''
  return e && e !== s ? `${s} – ${e}` : s
})

onMounted(() => events.fetchEvent(route.params.id))
</script>

<template>
  <div class="space-y-5 px-4 pb-4 pt-6">
    <button class="tap-target -ml-1 flex items-center gap-1 text-sm text-base-content/70" @click="router.back()">
      <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M15 19l-7-7 7-7" />
      </svg>
      {{ $t('common.back') }}
    </button>

    <AlertMessage type="warning" :message="events.error || ''" />
    <LoadingSpinner v-if="events.loading || !ev" :label="$t('eventDetail.loading')" />

    <template v-else>
      <header class="space-y-2">
        <h1 class="text-2xl font-bold">{{ ev.name }}</h1>
        <p v-if="ev.description" class="text-sm text-base-content/70">{{ ev.description }}</p>
        <div class="flex flex-wrap gap-x-4 gap-y-1 text-xs text-base-content/55">
          <span v-if="dateLabel">📅 {{ dateLabel }}</span>
          <span v-if="ev.location">📍 {{ ev.location }}</span>
        </div>
      </header>

      <!-- Moderation notices: a locked event is paused; an ended event is closed.
           In both cases earned badges remain visible but scanning is disabled. -->
      <div v-if="ev.status === 'locked'" class="surface flex items-center gap-3 border border-warning/40 bg-warning/10 p-4">
        <span class="text-xl">🔒</span>
        <p class="text-sm text-base-content/80">{{ $t('eventDetail.locked') }}</p>
      </div>
      <div v-else-if="ev.ended" class="surface flex items-center gap-3 bg-base-300/40 p-4">
        <span class="text-xl">🏁</span>
        <p class="text-sm text-base-content/80">{{ $t('eventDetail.ended') }}</p>
      </div>

      <div class="surface space-y-2 p-4">
        <ProgressBar :value="earned" :max="total" :label="completed ? $t('eventDetail.completed') : $t('eventDetail.yourProgress')" />
      </div>

      <div
        class="surface p-4"
        :class="completed ? 'bg-gradient-to-r from-warning/20 to-secondary/15' : ''"
      >
        <p class="text-xs uppercase tracking-wide text-base-content/55">
          {{ completed ? $t('eventDetail.prizeUnlocked') : $t('eventDetail.prizeLocked') }}
        </p>
        <p class="mt-1 font-semibold" :class="completed ? 'text-warning' : 'text-base-content'">
          🎁 {{ ev.prize || $t('eventDetail.prizeDefault') }}
        </p>
      </div>

      <section class="space-y-3">
        <h2 class="font-semibold">{{ $t('eventDetail.badges') }}</h2>
        <div v-if="ev.badges?.length" class="grid grid-cols-4 gap-2.5">
          <BadgeCard v-for="b in ev.badges" :key="b.id" :badge="b" />
        </div>
        <p v-else class="text-sm text-base-content/50">{{ $t('eventDetail.noBadges') }}</p>
      </section>
    </template>
  </div>
</template>
