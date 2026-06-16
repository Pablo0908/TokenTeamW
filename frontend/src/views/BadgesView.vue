<script setup>
import { ref, computed, onMounted } from 'vue'
import { useBadgesStore } from '@/stores/badges'
import BadgeCard from '@/components/domain/BadgeCard.vue'
import ProgressBar from '@/components/domain/ProgressBar.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'

const badges = useBadgesStore()

const selected = ref(null) // { badge, event }
const canShare = typeof navigator !== 'undefined' && !!navigator.share

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

function renderCanvas(badge, eventName) {
  const c = document.createElement('canvas')
  c.width = 600
  c.height = 760
  const ctx = c.getContext('2d')
  const bg = ctx.createLinearGradient(0, 0, 600, 760)
  bg.addColorStop(0, '#12151d')
  bg.addColorStop(1, '#0b0d14')
  ctx.fillStyle = bg
  ctx.fillRect(0, 0, 600, 760)
  ctx.beginPath()
  ctx.arc(300, 300, 180, 0, Math.PI * 2)
  const circle = ctx.createLinearGradient(120, 120, 480, 480)
  circle.addColorStop(0, '#2dd4bf')
  circle.addColorStop(1, '#0e7490')
  ctx.fillStyle = circle
  ctx.fill()
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.font = '150px serif'
  ctx.fillText(badge.icon || '🏅', 300, 300)
  ctx.fillStyle = '#e2e8f0'
  const name = badge.name || 'Badge'
  let nameSize = 44
  ctx.font = `bold ${nameSize}px sans-serif`
  while (nameSize > 22 && ctx.measureText(name).width > 540) {
    nameSize -= 2
    ctx.font = `bold ${nameSize}px sans-serif`
  }
  ctx.fillText(name, 300, 560)
  ctx.fillStyle = '#94a3b8'
  ctx.font = '28px sans-serif'
  ctx.fillText(eventName || '', 300, 612)
  ctx.fillStyle = '#2dd4bf'
  ctx.font = '600 24px sans-serif'
  ctx.fillText('Lyfter Badges', 300, 706)
  return c
}

function toBlob(canvas) {
  return new Promise((resolve) => canvas.toBlob(resolve, 'image/png'))
}

async function download(badge, eventName) {
  const blob = await toBlob(renderCanvas(badge, eventName))
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${badge.name}.png`
  a.click()
  URL.revokeObjectURL(url)
}

async function share(badge, eventName) {
  const blob = await toBlob(renderCanvas(badge, eventName))
  const file = new File([blob], `${badge.name}.png`, { type: 'image/png' })
  if (navigator.canShare?.({ files: [file] })) {
    try {
      await navigator.share({ files: [file], title: badge.name, text: `I earned the ${badge.name} badge at ${eventName}!` })
      return
    } catch {
      /* user cancelled — fall through to download */
    }
  }
  await download(badge, eventName)
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

        <template v-if="selected.badge.earned">
          <div class="flex gap-2">
            <button v-if="canShare" class="btn btn-primary btn-sm flex-1 tap-target" @click="share(selected.badge, selected.event)">
              Share
            </button>
            <button class="btn btn-outline btn-sm flex-1 tap-target" @click="download(selected.badge, selected.event)">
              Download
            </button>
          </div>
        </template>
        <p v-else class="rounded-xl bg-base-300/60 px-3 py-2 text-sm text-base-content/60">
          🔒 Locked — scan this badge to unlock it.
        </p>

        <button class="btn btn-ghost btn-sm w-full tap-target" @click="close">Close</button>
      </div>
    </div>
  </div>
</template>
