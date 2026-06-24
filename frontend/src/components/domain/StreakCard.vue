<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  value: { type: [Number, String], default: 0 },
  label: { type: String, default: '' },
})

const displayed = ref(0)
const shaking = ref(false)
const shakeAmp = ref(0) // px amplitude — grows as the count climbs

function animateCount(target) {
  const end = Number(target)
  const start = displayed.value
  if (start === end) return
  const steps = 20
  const delta = (end - start) / steps
  // only shake when counting UP
  const countingUp = end > start
  shaking.value = countingUp
  let i = 0
  const tick = setInterval(() => {
    i++
    const progress = i / steps
    displayed.value = i < steps ? Math.round(start + delta * i) : end
    // amplitude ramps progressively from 0 → 6px as the number rises
    if (countingUp) shakeAmp.value = progress * 6
    if (i >= steps) {
      clearInterval(tick)
      shaking.value = false
      shakeAmp.value = 0
    }
  }, 28)
}

onMounted(() => animateCount(props.value))
watch(() => props.value, animateCount)
</script>

<template>
  <div class="streak-wrap">
    <!-- glowing halo bloom behind the card edges -->
    <div class="halo" aria-hidden="true" />

    <div class="streak-card" :class="{ shaking }" :style="{ '--amp': shakeAmp + 'px' }">
      <span class="streak-num">{{ displayed }}</span>
      <span class="streak-lbl">{{ label }}</span>

      <!-- scattered glowing embers -->
      <span class="ember e1" aria-hidden="true" />
      <span class="ember e2" aria-hidden="true" />
      <span class="ember e3" aria-hidden="true" />
      <span class="ember e4" aria-hidden="true" />
    </div>
  </div>
</template>

<style scoped>
.streak-wrap {
  position: relative;
  display: flex;
  justify-content: center;
  padding: 14px 10px;
  animation: card-in 0.4s ease-out both;
}

/* the bright amber ring that blooms around the card edges */
.halo {
  position: absolute;
  inset: 14px 22px;
  border-radius: 16px;
  background: #f59e0b;
  filter: blur(16px);
  opacity: 0.55;
  animation: halo-pulse 3.6s ease-in-out infinite;
}

.streak-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 280px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 20px 16px 18px;
  border-radius: 16px;
  border: 1px solid rgba(251, 146, 60, 0.55);
  background: linear-gradient(165deg, #1a1d27 0%, #0d0f15 100%);
  box-shadow:
    0 0 0 1px rgba(251, 146, 60, 0.25),
    inset 0 0 24px rgba(0, 0, 0, 0.55);
}

.streak-num {
  font-size: 2.7rem;
  font-weight: 900;
  line-height: 1;
  letter-spacing: -1px;
  color: #fbbf24;
  text-shadow: 0 0 14px rgba(245, 158, 11, 0.6);
}

/* shake intensity is driven by --amp, which ramps up as the count climbs */
.streak-card.shaking {
  will-change: transform;
  animation: num-shake 0.12s linear infinite;
}

@keyframes num-shake {
  0%   { transform: translate(calc(var(--amp) * -1), 0) rotate(-1deg); }
  25%  { transform: translate(var(--amp), calc(var(--amp) * -0.5)) rotate(1deg); }
  50%  { transform: translate(calc(var(--amp) * -0.6), var(--amp)) rotate(-1deg); }
  75%  { transform: translate(var(--amp), calc(var(--amp) * 0.4)) rotate(1deg); }
  100% { transform: translate(calc(var(--amp) * -1), 0) rotate(-1deg); }
}

.streak-lbl {
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.4);
}

/* ── embers ── */
.ember {
  position: absolute;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #fbbf24;
  box-shadow: 0 0 6px 1px rgba(251, 191, 36, 0.9);
  opacity: 0;
  animation: twinkle 3s ease-in-out infinite;
}
.e1 { top: 34%;  left: 18%; animation-delay: 0.2s; }
.e2 { top: 70%;  left: 30%; animation-delay: 1.1s; }
.e3 { top: 64%;  right: 22%; animation-delay: 0.7s; }
.e4 { top: 44%;  right: 14%; animation-delay: 1.6s; }

/* ── keyframes ── */
@keyframes card-in {
  from { opacity: 0; transform: translateY(6px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes halo-pulse {
  0%, 100% { opacity: 0.45; filter: blur(16px); }
  50%      { opacity: 0.7;  filter: blur(22px); }
}

@keyframes twinkle {
  0%, 100% { opacity: 0;    transform: scale(0.6); }
  50%      { opacity: 0.95; transform: scale(1); }
}

@media (prefers-reduced-motion: reduce) {
  .streak-wrap, .halo, .ember, .streak-card.shaking { animation: none; }
  .halo { opacity: 0.55; }
}
</style>
