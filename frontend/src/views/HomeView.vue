<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useBadgesStore } from '@/stores/badges'
import { useEventsStore } from '@/stores/events'
import { useOnboardingStore } from '@/stores/onboarding'
import { useAnnouncementsStore } from '@/stores/announcements'
import StatTile from '@/components/domain/StatTile.vue'
import BadgeCard from '@/components/domain/BadgeCard.vue'
import EventCard from '@/components/domain/EventCard.vue'
import ShareSheet from '@/components/domain/ShareSheet.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'
import BrandLogo from '@/components/ui/BrandLogo.vue'
import LanguageModal from '@/components/ui/LanguageModal.vue'
import Coachmark from '@/components/ui/Coachmark.vue'
import { rarityMeta, rarityLabel } from '@/utils/rarity'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const badges = useBadgesStore()
const events = useEventsStore()
const onboarding = useOnboardingStore()
const anns = useAnnouncementsStore()

// Track which announcement IDs the user has already seen (persisted in localStorage).
// Unseen announcements show a ringing bell; after ~3 s on-page the bell settles and IDs are saved.
const SEEN_KEY = 'lyfter_seen_anns'
const seenIds = ref(new Set(JSON.parse(localStorage.getItem(SEEN_KEY) || '[]')))

function isSeen(id) {
  return seenIds.value.has(id)
}

let seenTimer = null

watch(
  () => anns.announcements.length,
  (len) => {
    if (!len) return
    if (!anns.announcements.some((a) => !seenIds.value.has(a.id))) return
    clearTimeout(seenTimer)
    seenTimer = setTimeout(() => {
      const updated = new Set([...seenIds.value, ...anns.announcements.map((a) => a.id)])
      seenIds.value = updated
      localStorage.setItem(SEEN_KEY, JSON.stringify([...updated]))
    }, 3500)
  },
)

onMounted(() => {
  if (!badges.loaded) badges.fetchMyBadges()
  if (!events.loaded) events.fetchEvents()
  if (!anns.loaded) anns.fetchAnnouncements()
  // Replay the first-run greeting + tutorial on demand (e.g. for a demo/test).
  if (route.query.welcome === '1') onboarding.forceStart(auth.user?.id)
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

const EMOJIS = ['🔥', '⚡', '🌟', '🚀', '💫', '🏆', '✨', '🎯', '👑', '🎉']
const emojiIndex = ref(0)
const currentEmoji = computed(() => EMOJIS[emojiIndex.value])

let emojiTimer
onMounted(() => {
  emojiTimer = setInterval(() => {
    emojiIndex.value = (emojiIndex.value + 1) % EMOJIS.length
  }, 2200)
})
onUnmounted(() => {
  clearInterval(emojiTimer)
  clearTimeout(seenTimer)
})

function goScan() {
  onboarding.dismissTip('scan')
  router.push('/scan')
}
function goBadges() {
  onboarding.dismissTip('badges')
  router.push('/badges')
}
function openEvent(id) {
  onboarding.dismissTip('events')
  router.push(`/events/${id}`)
}

// Badge detail modal
const selected = ref(null)
const flipped = ref(false)
const downloading = ref(false)

const rarity = computed(() => (selected.value?.badge?.earned ? rarityMeta(selected.value.badge.rarity) : null))

const apiBase = import.meta.env.VITE_API_URL || ''
const shareUrl = (id) => `${apiBase}/share/badge/${id}`
const shareText = (badge, event) => `${badge.name}${event ? ' — ' + event : ''}. Join us at Lyfter!`

function openBadge(badge) {
  selected.value = { badge, event: badge.event }
  flipped.value = false
}
function closeBadge() {
  selected.value = null
  flipped.value = false
}

async function downloadCard(badge) {
  downloading.value = true
  try {
    const res = await fetch(`${shareUrl(badge.id)}/image.png`)
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${badge.name}-lyfter.png`
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    window.open(`${shareUrl(badge.id)}/image.png`, '_blank', 'noopener')
  } finally {
    downloading.value = false
  }
}
</script>

<template>
  <div class="space-y-6 px-4 pb-4 pt-6">
    <!-- Header -->
    <header class="flex items-start justify-between">
      <div>
        <h1 class="flex items-center gap-2 text-2xl font-bold">
          {{ $t('home.greeting', { name: auth.displayName }) }}
          <transition name="emoji" mode="out-in">
            <span
              :key="currentEmoji"
              class="inline-block select-none drop-shadow-[0_0_10px_rgba(255,210,60,0.8)]"
            >{{ currentEmoji }}</span>
          </transition>
        </h1>
        <p class="text-sm text-base-content/60">
          {{ newThisWeek === 1 ? $t('home.newBadgeOne', { n: newThisWeek }) : $t('home.newBadgeMany', { n: newThisWeek }) }}
        </p>
      </div>
      <RouterLink to="/profile" class="surface grid h-11 w-11 place-items-center rounded-2xl p-2 active:scale-90 transition-transform">
        <BrandLogo :size="28" :show-wordmark="false" />
      </RouterLink>
    </header>

    <AlertMessage type="warning" :message="badges.error || ''" />

    <!-- Stats -->
    <section class="grid grid-cols-3 gap-3">
      <StatTile class="anim-rise" style="animation-delay: 0.05s" :value="badges.totalEarned" :label="$t('home.badges')" tone="primary" />
      <StatTile class="anim-rise" style="animation-delay: 0.12s" :value="badges.eventsCount" :label="$t('home.events')" tone="secondary" />
      <StatTile class="anim-rise" style="animation-delay: 0.19s" :value="streak" :label="$t('home.streak')" tone="accent" />
    </section>

    <!-- Announcements -->
    <section v-if="anns.announcements.length" class="space-y-3">
      <h2 class="font-semibold">{{ $t('announcements.title') }}</h2>
      <div class="space-y-3">
        <div v-for="ann in anns.announcements" :key="ann.id" class="surface relative space-y-2 p-4">
          <!-- Bell: only shown while unseen; rings for ~2.4 s then settles still -->
          <svg
            v-if="!isSeen(ann.id)"
            class="ann-bell absolute right-3 top-3 h-4 w-4 text-primary"
            viewBox="0 0 24 24"
            fill="currentColor"
            aria-hidden="true"
          >
            <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.63-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.64 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/>
          </svg>
          <p class="font-semibold leading-snug pr-6">{{ ann.title }}</p>
          <p v-if="ann.body" class="whitespace-pre-line text-sm text-base-content/70">{{ ann.body }}</p>
          <RouterLink
            v-if="ann.event_id"
            :to="`/events/${ann.event_id}`"
            class="inline-flex items-center gap-1.5 rounded-full bg-primary/15 px-3 py-1 text-xs font-medium text-primary tap-target"
          >
            <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
            {{ ann.event_name }}
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- Scan CTA -->
    <div :class="['relative', onboarding.showTip('scan') && 'z-30']">
      <button
        type="button"
        class="surface flex w-full items-center gap-4 bg-gradient-to-r from-primary/20 to-secondary/15 p-4 text-left transition-transform active:scale-[0.98]"
        @click="goScan"
      >
        <span class="anim-pulse-glow grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-primary/20 text-primary">
          <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M7 3.75h-1A2.25 2.25 0 003.75 6v1M17 3.75h1A2.25 2.25 0 0120.25 6v1M7 20.25h-1A2.25 2.25 0 013.75 18v-1M17 20.25h1A2.25 2.25 0 0020.25 18v-1" />
            <path d="M3.75 12h16.5" />
          </svg>
        </span>
        <span>
          <span class="block font-semibold">{{ $t('home.scanTitle') }}</span>
          <span class="block text-sm text-base-content/60">{{ $t('home.scanSub') }}</span>
        </span>
      </button>
      <transition name="coachmark">
        <Coachmark
          v-if="onboarding.showTip('scan')"
          class="absolute left-1/2 top-[calc(100%+10px)] z-30 -translate-x-1/2"
          :title="$t('coach.scanTitle')"
          :body="$t('coach.scanBody')"
          :step="1"
          :total="3"
          @dismiss="onboarding.dismissTip('scan')"
        />
      </transition>
    </div>

    <LoadingSpinner v-if="loading" :label="$t('home.loading')" />

    <template v-else>
      <!-- My badges -->
      <section class="space-y-3">
        <div :class="['relative flex items-center justify-between', onboarding.showTip('badges') && 'z-30']">
          <h2 class="font-semibold">{{ $t('home.badges') }}</h2>
          <button class="text-sm font-medium text-primary tap-target" @click="goBadges">{{ $t('common.seeAll') }}</button>
          <transition name="coachmark">
            <Coachmark
              v-if="onboarding.showTip('badges')"
              class="absolute right-0 top-[calc(100%+10px)] z-30"
              :title="$t('coach.badgesTitle')"
              :body="$t('coach.badgesBody')"
              :step="2"
              :total="3"
              @dismiss="onboarding.dismissTip('badges')"
            />
          </transition>
        </div>
        <div v-if="previewBadges.length" class="grid grid-cols-4 gap-2.5">
          <BadgeCard v-for="b in previewBadges" :key="b.id" :badge="b" clickable @select="openBadge(b)" />
        </div>
        <p v-else class="text-sm text-base-content/50">{{ $t('home.noBadges') }}</p>
      </section>

      <!-- Events -->
      <section class="space-y-3">
        <div :class="['relative flex items-center justify-between', onboarding.showTip('events') && 'z-30']">
          <h2 class="font-semibold">{{ $t('home.events') }}</h2>
          <RouterLink to="/events" class="text-sm font-medium text-primary tap-target" @click="onboarding.dismissTip('events')">{{ $t('common.seeAll') }}</RouterLink>
          <transition name="coachmark">
            <Coachmark
              v-if="onboarding.showTip('events')"
              class="absolute right-0 top-[calc(100%+10px)] z-30"
              :title="$t('coach.eventsTitle')"
              :body="$t('coach.eventsBody')"
              :step="3"
              :total="3"
              @dismiss="onboarding.dismissTip('events')"
            />
          </transition>
        </div>
        <div class="space-y-3">
          <EventCard
            v-for="ev in previewEvents"
            :key="ev.id"
            :event="ev"
            @select="openEvent(ev.id)"
          />
        </div>
      </section>
    </template>

    <!-- Dim backdrop while coachmark tips are showing — click to skip -->
    <transition name="tutorial-fade">
      <div
        v-if="onboarding.tipsActive && onboarding.currentTip"
        class="fixed inset-0 z-20 bg-black/55 backdrop-blur-[2px]"
        @click="onboarding.dismissTip(onboarding.currentTip)"
      />
    </transition>

    <!-- First-run greeting + language picker -->
    <LanguageModal v-if="onboarding.welcomeOpen" @choose="onboarding.chooseLanguage" />

    <!-- Badge detail modal -->
    <div
      v-if="selected"
      class="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-4 sm:items-center"
      @click.self="closeBadge"
    >
      <div class="surface w-full max-w-sm space-y-4 p-6 text-center">
        <button
          type="button"
          class="flip-card mx-auto block h-24 w-24"
          :class="{ flipped: flipped }"
          :aria-label="$t('rarity.tapToFlip')"
          @click="flipped = !flipped"
        >
          <div class="flip-inner">
            <span
              class="flip-front overflow-hidden text-5xl bg-gradient-to-br from-primary/30 to-secondary/20"
              :class="[selected.badge.earned ? 'badge-shine' : 'grayscale blur-[1px]', rarity ? 'ring-2 ' + rarity.ring : '']"
            >
              <img v-if="selected.badge.image" :src="selected.badge.image" :alt="selected.badge.name" class="h-full w-full object-cover" />
              <template v-else>{{ selected.badge.icon || '🏅' }}</template>
            </span>
            <span class="flip-back bg-base-300/80 px-2">
              <span v-if="rarity" class="space-y-0.5">
                <span class="block text-2xl">{{ rarity.emoji }}</span>
                <span class="block text-sm font-semibold" :class="rarity.text">{{ rarityLabel(selected.badge.rarity) }}</span>
                <span class="block text-[0.7rem] text-base-content/60">
                  {{ selected.badge.redeemed_by === 1 ? $t('rarity.collectedOne') : $t('rarity.collectedMany', { n: selected.badge.redeemed_by ?? 0 }) }}
                </span>
              </span>
              <span v-else class="px-2 text-xs text-base-content/70">{{ selected.badge.description || selected.badge.name }}</span>
            </span>
          </div>
        </button>

        <div>
          <h3 class="text-xl font-bold">{{ selected.badge.name }}</h3>
          <p class="text-sm text-base-content/60">{{ selected.event }}</p>
          <div v-if="rarity" class="mt-2 flex items-center justify-center gap-2 text-xs">
            <span class="inline-flex items-center gap-1 rounded-full bg-base-300/60 px-2 py-0.5 font-medium" :class="rarity.text">
              {{ rarity.emoji }} {{ rarityLabel(selected.badge.rarity) }}
            </span>
            <span class="text-base-content/55">
              {{ selected.badge.redeemed_by === 1 ? $t('rarity.collectedOne') : $t('rarity.collectedMany', { n: selected.badge.redeemed_by ?? 0 }) }}
            </span>
          </div>
          <p v-if="selected.badge.description" class="mt-2 text-sm text-base-content/70">{{ selected.badge.description }}</p>
          <p class="mt-1 text-[0.7rem] text-base-content/40">{{ $t('rarity.tapToFlip') }}</p>
        </div>

        <p v-if="!selected.badge.earned" class="rounded-xl bg-base-300/60 px-3 py-2 text-sm text-base-content/60">
          {{ $t('badges.notEarned') }}
        </p>

        <ShareSheet
          :url="shareUrl(selected.badge.id)"
          :text="shareText(selected.badge, selected.event)"
          :title="selected.badge.name"
        />

        <button class="btn btn-ghost btn-sm w-full gap-2 tap-target" :disabled="downloading" @click="downloadCard(selected.badge)">
          <span v-if="downloading" class="loading loading-spinner loading-xs" />
          {{ $t('badges.download') }}
        </button>

        <button class="btn btn-ghost btn-sm w-full tap-target" @click="closeBadge">{{ $t('common.close') }}</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes ring-bell {
  0%,  100% { transform: rotate(0deg); }
  10%       { transform: rotate(-22deg); }
  20%       { transform: rotate(22deg); }
  30%       { transform: rotate(-16deg); }
  40%       { transform: rotate(16deg); }
  50%       { transform: rotate(-10deg); }
  60%       { transform: rotate(10deg); }
  70%       { transform: rotate(-5deg); }
  80%       { transform: rotate(5deg); }
  90%       { transform: rotate(-2deg); }
}

.ann-bell {
  transform-origin: top center;
  animation: ring-bell 0.8s ease-in-out 3;
  animation-fill-mode: forwards;
}
</style>
