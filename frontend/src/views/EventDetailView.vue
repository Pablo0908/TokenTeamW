<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { locale, t } from '@/i18n'
import { api } from '@/services/api'
import { useEventsStore } from '@/stores/events'
import BadgeCard from '@/components/domain/BadgeCard.vue'
import ProgressBar from '@/components/domain/ProgressBar.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'
import { applyOrgTheme, clearOrgTheme } from '@/utils/orgTheme'

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

// --- Prize claim QR ---
// Once the attendee has completed the event, fetch a signed claim code to show staff. It's
// an assertion only (the server's atomic flip is the real award), and short-lived, so we
// refresh it while it's on screen. If the prize was already handed over, show that instead.
const claim = ref(null)
let claimTimer = null
async function loadClaim() {
  if (!completed.value || !ev.value) return
  try {
    claim.value = (await api.get(`/events/${ev.value.id}/claim/qr`)).data
  } catch {
    claim.value = null // not completed server-side, or transient — silently skip the QR
  }
}
function claimedAwardLabel() {
  const c = claim.value?.claim
  if (!c) return ''
  const on = c.awarded_on ? t('eventDetail.claimedOn', { date: c.awarded_on }) : ''
  const by = c.awarded_by_name ? t('eventDetail.claimedBy', { name: c.awarded_by_name }) : ''
  return [on, by].filter(Boolean).join(' ')
}
watch(completed, (done) => {
  clearInterval(claimTimer)
  if (!done) { claim.value = null; return }
  loadClaim()
  // Keep the signed code fresh (TTL is short) while the screen is open.
  claimTimer = setInterval(() => { if (!claim.value?.claimed) loadClaim() }, 50000)
}, { immediate: true })

// Theme the page with the owning org's brand colors while it's open.
watch(() => ev.value?.org?.theme, (th) => applyOrgTheme(th || {}), { deep: true })
onMounted(() => events.fetchEvent(route.params.id))
onUnmounted(() => { clearOrgTheme(); clearInterval(claimTimer) })
</script>

<template>
  <div class="space-y-5 px-4 lg:px-8 pb-4 pt-6">
    <button class="tap-target -ml-1 flex items-center gap-1 text-sm text-base-content/70" @click="router.back()">
      <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M15 19l-7-7 7-7" />
      </svg>
      {{ $t('common.back') }}
    </button>

    <AlertMessage type="warning" :message="events.error || ''" />
    <LoadingSpinner v-if="events.loading || !ev" :label="$t('eventDetail.loading')" />

    <template v-else>
      <div class="grid grid-cols-1 gap-5 lg:grid-cols-2 lg:items-start">
      <div class="space-y-5">
      <header class="space-y-2">
        <div v-if="ev.org?.name" class="flex items-center gap-2 text-xs text-base-content/55">
          <img v-if="ev.org.theme?.logo_url" :src="ev.org.theme.logo_url" alt="" class="h-5 w-5 rounded object-cover ring-1 ring-base-300" />
          <span class="font-medium">{{ ev.org.name }}</span>
        </div>
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

      <!-- Prize claim: shown only once the event is completed. Either the live claim QR
           (assertion the attendee shows to staff) or, if already handed over, the record. -->
      <div v-if="completed && claim?.claimed" class="surface flex items-center gap-3 border border-success/40 bg-success/10 p-4">
        <span class="text-xl">✅</span>
        <div class="min-w-0">
          <p class="text-sm font-semibold text-success">{{ $t('eventDetail.claimed') }}</p>
          <p v-if="claimedAwardLabel()" class="truncate text-xs text-base-content/60">{{ claimedAwardLabel() }}</p>
        </div>
      </div>
      <div v-else-if="completed && claim?.qr" class="surface flex flex-col items-center gap-3 p-4">
        <p class="text-sm font-semibold">{{ $t('eventDetail.claimTitle') }}</p>
        <div class="rounded-2xl bg-white p-3 shadow-lg">
          <img :src="claim.qr" :alt="$t('eventDetail.claimTitle')" class="block h-auto w-full max-w-[220px] rounded-lg" />
        </div>
        <p class="text-center text-xs text-base-content/55">{{ $t('eventDetail.claimHint') }}</p>
      </div>
      </div>

      <section class="space-y-3">
        <h2 class="font-semibold">{{ $t('eventDetail.badges') }}</h2>
        <div v-if="ev.badges?.length" class="grid grid-cols-4 md:grid-cols-6 gap-2.5">
          <BadgeCard v-for="b in ev.badges" :key="b.id" :badge="b" />
        </div>
        <p v-else class="text-sm text-base-content/50">{{ $t('eventDetail.noBadges') }}</p>
      </section>
      </div>
    </template>
  </div>
</template>
