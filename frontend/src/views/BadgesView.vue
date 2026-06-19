<script setup>
import { ref, computed, onMounted } from 'vue'
import { useBadgesStore } from '@/stores/badges'
import BadgeCard from '@/components/domain/BadgeCard.vue'
import ProgressBar from '@/components/domain/ProgressBar.vue'
import ShareSheet from '@/components/domain/ShareSheet.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'
import { rarityMeta, rarityLabel } from '@/utils/rarity'

const badges = useBadgesStore()

const selected = ref(null) // { badge, event }
const flipped = ref(false)
const downloading = ref(false)

// Rarity tier of the open badge (only meaningful once earned).
const rarity = computed(() => (selected.value?.badge?.earned ? rarityMeta(selected.value.badge.rarity) : null))

// Public share link — the backend serves an Open Graph preview card for it.
const apiBase = import.meta.env.VITE_API_URL || ''
const shareUrl = (id) => `${apiBase}/share/badge/${id}`
const shareText = (badge, event) => `${badge.name}${event ? ' — ' + event : ''}. Join us at Lyfter!`

onMounted(() => {
  if (!badges.loaded) badges.fetchMyBadges()
})

const nonEmpty = computed(() => badges.groups.some((g) => g.badges.length))

function open(badge, event) {
  selected.value = { badge, event }
  flipped.value = false
}
function close() {
  selected.value = null
  flipped.value = false
}

// Download the backend-rendered share card (branded PNG).
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
    <header>
      <h1 class="text-2xl font-bold">{{ $t('badges.title') }}</h1>
      <p class="text-sm text-base-content/60">
        {{ $t('badges.summary', { earned: badges.totalEarned, completed: badges.completedEvents }) }}
      </p>
    </header>

    <AlertMessage type="warning" :message="badges.error || ''" />
    <LoadingSpinner v-if="badges.loading && !badges.loaded" :label="$t('badges.loading')" />

    <template v-else-if="nonEmpty">
      <section v-for="group in badges.groups" :key="group.event_id" class="space-y-3">
        <div class="flex items-end justify-between gap-3">
          <h2 class="font-semibold">{{ group.event }}</h2>
          <span class="text-xs text-base-content/55">{{ group.badges_earned }}/{{ group.badges_total }}</span>
        </div>
        <ProgressBar :value="group.badges_earned" :max="group.badges_total" :show-count="false" />
        <div class="grid grid-cols-4 gap-2.5">
          <BadgeCard
            v-for="b in group.badges"
            :key="b.id"
            :badge="b"
            clickable
            @select="open(b, group.event)"
          />
        </div>
      </section>
    </template>

    <div v-else class="surface flex flex-col items-center gap-2 p-8 text-center">
      <span class="text-4xl">🎯</span>
      <p class="font-medium">{{ $t('badges.emptyTitle') }}</p>
      <p class="text-sm text-base-content/60">{{ $t('badges.emptySub') }}</p>
      <RouterLink to="/scan" class="btn btn-primary btn-sm mt-2 tap-target">{{ $t('badges.emptyCta') }}</RouterLink>
    </div>

    <!-- Badge detail modal -->
    <div
      v-if="selected"
      class="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-4 sm:items-center"
      @click.self="close"
    >
      <div class="surface w-full max-w-sm space-y-4 p-6 text-center">
        <!-- Flip medallion: front = icon (with shine when earned), back = rarity + count -->
        <button
          type="button"
          class="flip-card mx-auto block h-24 w-24"
          :class="{ flipped: flipped }"
          :aria-label="$t('rarity.tapToFlip')"
          @click="flipped = !flipped"
        >
          <div class="flip-inner">
            <span
              class="flip-front text-5xl bg-gradient-to-br from-primary/30 to-secondary/20"
              :class="[selected.badge.earned ? 'badge-shine' : 'grayscale blur-[1px]', rarity ? 'ring-2 ' + rarity.ring : '']"
            >
              {{ selected.badge.icon || '🏅' }}
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
          <!-- Rarity + collected summary -->
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

        <button class="btn btn-ghost btn-sm w-full tap-target" @click="close">{{ $t('common.close') }}</button>
      </div>
    </div>
  </div>
</template>
