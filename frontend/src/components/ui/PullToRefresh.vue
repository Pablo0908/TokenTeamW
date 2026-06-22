<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

// Standalone pull-to-refresh gesture. Drop it at the top of a scrollable view
// (`<PullToRefresh :on-refresh="fn" />`); it watches touch gestures that start at
// the top of the page and calls `onRefresh` once pulled past the threshold.
const props = defineProps({
  onRefresh: { type: Function, required: true },
})

const THRESHOLD = 70 // px of pull needed to trigger
const MAX_PULL = 110 // visual cap
const RESISTANCE = 0.5 // dampen the drag so it feels elastic

const pull = ref(0)
const refreshing = ref(false)

let startY = 0
let engaged = false

function atTop() {
  return (window.scrollY || document.documentElement.scrollTop || 0) <= 0
}

function onTouchStart(e) {
  if (refreshing.value || !atTop()) return
  engaged = true
  startY = e.touches[0].clientY
}

function onTouchMove(e) {
  if (!engaged || refreshing.value) return
  const delta = e.touches[0].clientY - startY
  if (delta <= 0) {
    pull.value = 0
    return
  }
  // Pulling down while at the top — take over from native overscroll.
  if (e.cancelable) e.preventDefault()
  pull.value = Math.min(delta * RESISTANCE, MAX_PULL)
}

async function onTouchEnd() {
  if (!engaged) return
  engaged = false
  if (pull.value >= THRESHOLD && !refreshing.value) {
    refreshing.value = true
    pull.value = THRESHOLD
    try {
      await props.onRefresh()
    } catch {
      /* surfaced by the caller's store */
    } finally {
      refreshing.value = false
      pull.value = 0
    }
  } else {
    pull.value = 0
  }
}

onMounted(() => {
  window.addEventListener('touchstart', onTouchStart, { passive: true })
  window.addEventListener('touchmove', onTouchMove, { passive: false })
  window.addEventListener('touchend', onTouchEnd, { passive: true })
})
onBeforeUnmount(() => {
  window.removeEventListener('touchstart', onTouchStart)
  window.removeEventListener('touchmove', onTouchMove)
  window.removeEventListener('touchend', onTouchEnd)
})
</script>

<template>
  <div
    v-show="pull > 0 || refreshing"
    class="pointer-events-none fixed inset-x-0 top-0 z-40 flex justify-center"
    :style="{ transform: `translateY(${pull}px)`, transition: refreshing ? 'transform 0.2s' : 'none' }"
  >
    <span
      class="mt-2 grid h-9 w-9 place-items-center rounded-full bg-base-100/90 shadow-lg"
      :style="{ opacity: Math.min(pull / THRESHOLD, 1) }"
    >
      <span v-if="refreshing" class="loading loading-spinner loading-sm text-primary" />
      <svg
        v-else
        class="h-5 w-5 text-primary transition-transform"
        :style="{ transform: `rotate(${Math.min(pull / THRESHOLD, 1) * 180}deg)` }"
        viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"
      >
        <path d="M12 5v14M5 12l7 7 7-7" />
      </svg>
    </span>
  </div>
</template>
