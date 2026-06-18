<script setup>
import { ref, computed, onMounted } from 'vue'
import { useBadgesStore } from '@/stores/badges'
import BadgeCard from '@/components/domain/BadgeCard.vue'
import ProgressBar from '@/components/domain/ProgressBar.vue'
import ShareSheet from '@/components/domain/ShareSheet.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'

const badges = useBadgesStore()

const selected = ref(null) // { badge, event }
const downloading = ref(false)

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
}
function close() {
  selected.value = null
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
      <h1 class="text-2xl font-bold">My badges</h1>
      <p class="text-sm text-base-content/60">
        {{ badges.totalEarned }} earned · {{ badges.completedEvents }} events completed
      </p>
    </header>

    <AlertMessage type="warning" :message="badges.error || ''" />
    <LoadingSpinner v-if="badges.loading && !badges.loaded" label="Loading your collection…" />

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
      <p class="font-medium">No badges yet</p>
      <p class="text-sm text-base-content/60">Scan a QR at an event station to earn your first badge.</p>
      <RouterLink to="/scan" class="btn btn-primary btn-sm mt-2 tap-target">Start scanning</RouterLink>
    </div>

    <!-- Badge detail modal -->
    <div
      v-if="selected"
      class="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-4 sm:items-center"
      @click.self="close"
    >
      <div class="surface w-full max-w-sm space-y-4 p-6 text-center">
        <div class="mx-auto grid h-24 w-24 place-items-center rounded-full bg-gradient-to-br from-primary/30 to-secondary/20 text-5xl" :class="{ grayscale: !selected.badge.earned }">
          {{ selected.badge.icon || '🏅' }}
        </div>
        <div>
          <h3 class="text-xl font-bold">{{ selected.badge.name }}</h3>
          <p class="text-sm text-base-content/60">{{ selected.event }}</p>
          <p v-if="selected.badge.description" class="mt-2 text-sm text-base-content/70">{{ selected.badge.description }}</p>
        </div>

        <p v-if="!selected.badge.earned" class="rounded-xl bg-base-300/60 px-3 py-2 text-sm text-base-content/60">
          🔒 Not earned yet — scan this badge to unlock it.
        </p>

        <ShareSheet
          :url="shareUrl(selected.badge.id)"
          :text="shareText(selected.badge, selected.event)"
          :title="selected.badge.name"
        />

        <button class="btn btn-ghost btn-sm w-full gap-2 tap-target" :disabled="downloading" @click="downloadCard(selected.badge)">
          <span v-if="downloading" class="loading loading-spinner loading-xs" />
          Download image
        </button>

        <button class="btn btn-ghost btn-sm w-full tap-target" @click="close">Close</button>
      </div>
    </div>
  </div>
</template>
