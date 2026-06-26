<script setup>
import { computed } from 'vue'

const props = defineProps({
  active: { type: Boolean, default: false },
  count: { type: Number, default: 80 },
})

const colors = ['#2dd4bf', '#a78bfa', '#fb7185', '#38bdf8', '#22c55e', '#f59e0b']

// Deterministic-enough randomness; only built while active.
const pieces = computed(() => {
  if (!props.active) return []
  return Array.from({ length: props.count }, (_, i) => ({
    id: i,
    left: Math.random() * 100,
    bg: colors[i % colors.length],
    delay: Math.random() * 0.5,
    duration: 1.8 + Math.random() * 1.6,
    size: 6 + Math.random() * 8,
    drift: `${(Math.random() - 0.5) * 140}px`,
  }))
})
</script>

<template>
  <div
    v-if="active"
    class="pointer-events-none fixed inset-0 z-50 overflow-hidden"
    aria-hidden="true"
  >
    <span
      v-for="p in pieces"
      :key="p.id"
      class="confetti-piece"
      :style="{
        left: p.left + '%',
        width: p.size + 'px',
        height: p.size * 0.5 + 'px',
        background: p.bg,
        animationDelay: p.delay + 's',
        animationDuration: p.duration + 's',
        '--drift': p.drift,
      }"
    />
  </div>
</template>

<style scoped>
.confetti-piece {
  position: absolute;
  top: -5%;
  border-radius: 2px;
  opacity: 0;
  animation-name: confetti-fall;
  animation-timing-function: cubic-bezier(0.3, 0.6, 0.5, 1);
  animation-iteration-count: 1;
  animation-fill-mode: forwards;
}

@keyframes confetti-fall {
  0% {
    transform: translate3d(0, -10vh, 0) rotate(0deg);
    opacity: 1;
  }
  100% {
    transform: translate3d(var(--drift), 110vh, 0) rotate(720deg);
    opacity: 0.9;
  }
}

@media (prefers-reduced-motion: reduce) {
  .confetti-piece {
    display: none;
  }
}
</style>
