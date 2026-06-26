<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useBadgesStore } from '@/stores/badges'
import { useEventsStore } from '@/stores/events'
import { useAnnouncementsStore } from '@/stores/announcements'
import { useOnboardingStore } from '@/stores/onboarding'
import StatTile from '@/components/domain/StatTile.vue'
import StreakCard from '@/components/domain/StreakCard.vue'
import BadgeCard from '@/components/domain/BadgeCard.vue'
import EventCard from '@/components/domain/EventCard.vue'
import ShareSheet from '@/components/domain/ShareSheet.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'
import LanguageModal from '@/components/ui/LanguageModal.vue'
import Coachmark from '@/components/ui/Coachmark.vue'
import { rarityMeta, rarityLabel } from '@/utils/rarity'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const avatarInitials = computed(() => {
  const n = auth.user?.name ?? ''
  const l = auth.user?.lastname ?? ''
  return ((n[0] ?? '') + (l[0] ?? '')).toUpperCase() || (auth.user?.email?.[0] ?? 'U').toUpperCase()
})
const badges = useBadgesStore()
const events = useEventsStore()
const announcements = useAnnouncementsStore()
const onboarding = useOnboardingStore()

onMounted(async () => {
  if (!badges.loaded) badges.fetchMyBadges()
  badges.fetchStreak()
  if (!events.loaded) events.fetchEvents()
  // Load announcements, then mark them seen shortly after so the unread markers are
  // visible on arrival but clear for the next visit.
  await announcements.fetchAnnouncements()
  if (announcements.hasUnread) setTimeout(() => announcements.markSeen(), 2500)
  // Replay the first-run greeting + tutorial on demand (e.g. for a demo/test).
  if (route.query.welcome === '1') onboarding.forceStart(auth.user?.id)
})

function openAnnouncement(a) {
  if (a.event_id) router.push(`/events/${a.event_id}`)
}

// Let users collapse the announcements section so the home view isn't bloated on phones.
// Choice persists across visits.
const annCollapsed = ref(localStorage.getItem('annCollapsed') === '1')
function toggleAnnouncements() {
  annCollapsed.value = !annCollapsed.value
  try { localStorage.setItem('annCollapsed', annCollapsed.value ? '1' : '0') } catch { /* storage unavailable */ }
}

const WEEK = 7 * 24 * 60 * 60 * 1000
const newThisWeek = computed(
  () =>
    badges.earnedBadges.filter((b) => {
      const t = new Date(b.date).getTime()
      return !Number.isNaN(t) && Date.now() - t <= WEEK
    }).length,
)
// Authoritative streak: consecutive event-days of completed events, computed server-side.
const streak = computed(() => badges.streak)

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
onUnmounted(() => clearInterval(emojiTimer))

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
  <div class="space-y-6 px-4 lg:px-8 pb-4 pt-6">
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
      <!-- Avatar button: main area → profile, camera badge → change photo -->
      <div class="relative">
        <RouterLink to="/profile" class="surface grid h-11 w-11 overflow-hidden place-items-center rounded-2xl active:scale-90 transition-transform">
          <img v-if="auth.user?.avatar_url" :src="auth.user.avatar_url" class="h-full w-full object-cover" alt="" />
          <span v-else class="grid h-full w-full place-items-center bg-gradient-to-br from-primary to-secondary text-sm font-bold text-primary-content">
            {{ avatarInitials }}
          </span>
        </RouterLink>
        <RouterLink
          to="/profile/change-photo"
          class="absolute -bottom-1 -right-1 grid h-5 w-5 place-items-center rounded-full bg-base-200 shadow ring-2 ring-base-100 transition-transform active:scale-90"
          :aria-label="$t('settings.changePhoto')"
        >
          <svg class="h-3 w-3 text-base-content/70" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/>
            <circle cx="12" cy="13" r="4"/>
          </svg>
        </RouterLink>
      </div>
    </header>

    <AlertMessage type="warning" :message="badges.error || ''" />

    <!-- Stats -->
    <section class="space-y-2">
      <div :class="['relative', onboarding.showTip('streak') && 'z-30']">
        <StreakCard :value="streak" :label="$t('home.streak')" />
        <transition name="coachmark">
          <Coachmark
            v-if="onboarding.showTip('streak')"
            class="absolute left-1/2 top-[calc(100%+10px)] z-30 -translate-x-1/2"
            :title="$t('coach.streakTitle')"
            :body="$t('coach.streakBody')"
            :step="1"
            :total="4"
            @dismiss="onboarding.dismissTip('streak')"
          />
        </transition>
      </div>
      <div class="grid grid-cols-2 gap-3 max-w-xs mx-auto w-full">
        <StatTile class="anim-rise" style="animation-delay: 0.05s" :value="badges.totalEarned" :label="$t('home.badges')" tone="primary" />
        <StatTile class="anim-rise" style="animation-delay: 0.12s" :value="badges.eventsCount" :label="$t('home.events')" tone="secondary" />
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
          :step="2"
          :total="4"
          @dismiss="onboarding.dismissTip('scan')"
        />
      </transition>
    </div>

    <!-- Announcements — platform-wide, visible to all; unread items flagged -->
    <section v-if="announcements.items.length" class="space-y-3">
      <button
        type="button"
        class="tap-target flex w-full items-center gap-2"
        :aria-expanded="!annCollapsed"
        :aria-label="annCollapsed ? $t('home.expand') : $t('home.minimize')"
        @click="toggleAnnouncements"
      >
        <h2 class="font-semibold">{{ $t('home.announcements') }}</h2>
        <span
          v-if="announcements.unreadCount"
          class="badge badge-primary badge-sm font-semibold"
          aria-label="Unread announcements"
        >{{ announcements.unreadCount }}</span>
        <svg
          class="ml-auto h-4 w-4 text-base-content/50 transition-transform"
          :class="{ '-rotate-90': annCollapsed }"
          viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>
      <div v-show="!annCollapsed" class="grid grid-cols-1 gap-2 md:grid-cols-2">
        <component
          :is="a.event_id ? 'button' : 'div'"
          v-for="a in announcements.items"
          :key="a.id"
          type="button"
          class="surface relative w-full p-4 text-left"
          :class="[
            a.event_id ? 'transition-transform active:scale-[0.98]' : '',
            a.unread ? 'ring-1 ring-primary/50' : '',
          ]"
          @click="openAnnouncement(a)"
        >
          <!-- Ringing bell — visible while unread, disappears once markSeen() clears it -->
          <span
            v-if="a.unread"
            class="ann-bell absolute right-2 top-2 text-primary drop-shadow-[0_0_6px_rgba(255,210,60,0.9)]"
            aria-hidden="true"
          >
            <svg class="h-7 w-7" viewBox="0 0 24 24" fill="currentColor">
              <path d="M18 16.25v-5.5a6 6 0 00-4.5-5.81V4a1.5 1.5 0 10-3 0v.94A6 6 0 006 10.75v5.5H4v1.5h16v-1.5h-2zm-6 5.75a2 2 0 002-2H10a2 2 0 002 2z"/>
            </svg>
          </span>
          <div class="flex items-center gap-2 pr-8">
            <p class="truncate font-semibold">{{ a.title }}</p>
            <span v-if="a.unread" class="badge badge-primary badge-xs font-bold">{{ $t('home.newTag') }}</span>
          </div>
          <p class="mt-1 line-clamp-2 text-sm text-base-content/70">{{ a.body }}</p>
          <p v-if="a.event && a.event.name" class="mt-2 flex items-center gap-1 text-xs font-medium text-primary">
            <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7" /></svg>
            {{ a.event.name }}
          </p>
        </component>
      </div>
    </section>

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
              :step="3"
              :total="4"
              @dismiss="onboarding.dismissTip('badges')"
            />
          </transition>
        </div>
        <div v-if="previewBadges.length" class="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-2.5">
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
              :step="4"
              :total="4"
              @dismiss="onboarding.dismissTip('events')"
            />
          </transition>
        </div>
        <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
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

    <!-- Badge detail overlay -->
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
.ann-bell {
  display: inline-block;
  transform-origin: 50% 0%;
  animation: ring-bell 0.8s ease-in-out 3;
  animation-fill-mode: forwards;
}

@keyframes ring-bell {
  0%   { transform: rotate(0deg); }
  10%  { transform: rotate(22deg); }
  28%  { transform: rotate(-20deg); }
  46%  { transform: rotate(16deg); }
  62%  { transform: rotate(-12deg); }
  76%  { transform: rotate(7deg); }
  88%  { transform: rotate(-4deg); }
  100% { transform: rotate(0deg); }
}
</style>
