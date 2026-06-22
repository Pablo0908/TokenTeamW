<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useBadgesStore } from '@/stores/badges'
import { useEventsStore } from '@/stores/events'
import { useOnboardingStore } from '@/stores/onboarding'
import StatTile from '@/components/domain/StatTile.vue'
import BadgeCard from '@/components/domain/BadgeCard.vue'
import EventCard from '@/components/domain/EventCard.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'
import BrandLogo from '@/components/ui/BrandLogo.vue'
import LanguageModal from '@/components/ui/LanguageModal.vue'
import Coachmark from '@/components/ui/Coachmark.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const badges = useBadgesStore()
const events = useEventsStore()
const onboarding = useOnboardingStore()

onMounted(() => {
  if (!badges.loaded) badges.fetchMyBadges()
  if (!events.loaded) events.fetchEvents()
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
          <BadgeCard v-for="b in previewBadges" :key="b.id" :badge="b" />
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
  </div>
</template>
