<script setup>
/**
 * Full-screen streak-up celebration.
 *
 * Mounted once globally (in App.vue) and teleported to <body>, so it plays over ANY screen
 * the user happens to be on. It watches `badges.streakCelebration` (armed by the store when a
 * genuine streak increase is detected) and runs the sequence:
 *   1. the screen goes black and the flame ignites in the centre,
 *   2. the OLD number shows below the flame, then "burns off" (animates out),
 *   3. the NEW number ignites in its place,
 *   4. everything fades away and the celebration state is cleared.
 * Tapping anywhere skips to the end.
 */
import { ref, watch, onUnmounted } from 'vue'
import { useBadgesStore } from '@/stores/badges'
import FlameIcon from '@/components/domain/FlameIcon.vue'

const badges = useBadgesStore()

const visible = ref(false) // drives the enter/leave (fade) transition of the whole overlay
const displayNum = ref(0) // the number currently shown; changing it triggers the out-in swap
const stars = ref(0) // star rating earned for the NEW streak (1–6)
const showStars = ref(false) // gates the staggered star reveal until after the number lands

// Star rating, scaled to the streak: the higher the streak, the more stars. The 6th is a
// rare "bonus" star (streak ≥ 50) with its own special animation.
function starsForStreak(n) {
  if (n >= 50) return 6
  if (n >= 25) return 5
  if (n >= 14) return 4
  if (n >= 7) return 3
  if (n >= 3) return 2
  if (n >= 1) return 1
  return 0
}

// Sequence timing (ms) — grouped here so the whole choreography is easy to read and tune.
const FADE_IN = 450 // matches .streakup enter transition
const HOLD_FROM = 800 // how long the old number lingers before it burns off
const SWAP = 1050 // out-in number transition: old leaves (~450) then new enters (~550)
const STAR_STAGGER = 160 // ms between each star popping in
const STAR_POP = 480 // ms for one star's pop-in animation
const HOLD_AFTER_STARS = 1200 // how long the completed rating is held before fade-out

let runToken = 0
let timers = []
const clearTimers = () => { timers.forEach(clearTimeout); timers = [] }
const wait = (ms) => new Promise((resolve) => { timers.push(setTimeout(resolve, ms)) })

async function play(from, to) {
  const token = ++runToken
  clearTimers()
  stars.value = starsForStreak(to)
  showStars.value = false
  displayNum.value = from
  visible.value = true

  await wait(FADE_IN + HOLD_FROM)
  if (token !== runToken) return
  displayNum.value = to // → out-in swap: old number burns off, new number ignites

  await wait(SWAP)
  if (token !== runToken) return
  showStars.value = true // reveal the rating; stars pop in one by one (staggered in CSS)

  const revealMs = Math.max(0, stars.value - 1) * STAR_STAGGER + STAR_POP
  await wait(revealMs + HOLD_AFTER_STARS)
  if (token !== runToken) return
  visible.value = false // leave transition fades the overlay out; cleanup in onClosed()
}

function skip() {
  if (!visible.value) return
  runToken++ // cancel any pending steps
  clearTimers()
  displayNum.value = badges.streakCelebration?.to ?? displayNum.value
  showStars.value = true
  visible.value = false
}

// Fired after the leave transition completes — only now clear the store flag, so a re-arm
// can't race the fade-out.
function onClosed() {
  clearTimers()
  showStars.value = false
  badges.clearStreakCelebration()
}

watch(
  () => badges.streakCelebration,
  (c) => { if (c) play(c.from, c.to) },
  { immediate: true },
)

onUnmounted(clearTimers)
</script>

<template>
  <Teleport to="body">
    <transition name="streakup" @after-leave="onClosed">
      <div
        v-if="visible"
        class="streakup-overlay"
        role="status"
        aria-live="assertive"
        :aria-label="`${$t('home.streak')}: ${displayNum}`"
        @click="skip"
      >
        <div class="streakup-glow" aria-hidden="true" />
        <div class="streakup-content">
          <div class="streakup-flame">
            <FlameIcon />
          </div>
          <transition name="num" mode="out-in">
            <span :key="displayNum" class="streakup-num">{{ displayNum }}</span>
          </transition>
          <span class="streakup-label">{{ $t('home.streak') }}</span>

          <!-- star rating: 1–6 stars based on the streak; the 6th is a special bonus star -->
          <div v-if="showStars" class="streakup-stars" aria-hidden="true">
            <span
              v-for="i in stars"
              :key="i"
              class="star"
              :class="{ bonus: stars === 6 && i === 6 }"
              :style="{ animationDelay: (i - 1) * 0.16 + 's' }"
            >
              <svg viewBox="0 0 24 24">
                <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
              </svg>
            </span>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<style scoped>
.streakup-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000; /* black background, as requested */
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
  padding: env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);
}

/* faint teal halo so the flame feels like it's lighting up the dark screen */
.streakup-glow {
  position: absolute;
  top: 42%;
  left: 50%;
  width: min(120vw, 720px);
  aspect-ratio: 1;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, rgba(45, 212, 200, 0.22) 0%, rgba(20, 140, 132, 0.08) 38%, transparent 66%);
  pointer-events: none;
  animation: streakup-glow-pulse 2.4s ease-in-out infinite;
}

.streakup-content {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
}

.streakup-flame {
  width: min(58vw, 250px);
  transform-origin: 50% 90%;
  filter: drop-shadow(0 0 14px rgba(48, 214, 204, 0.7)) drop-shadow(0 0 38px rgba(26, 168, 160, 0.5));
  /* rise/ignite once on mount, then settle into a continuous burning flicker */
  animation: streakup-flame-rise 0.6s ease-out both, flame-dance 2.2s ease-in-out 0.6s infinite;
}

.streakup-num {
  display: block;
  font-weight: 900;
  font-size: clamp(4.5rem, 26vw, 9rem);
  line-height: 1;
  color: #fff;
  text-shadow:
    0 0 18px rgba(60, 224, 214, 0.85),
    0 0 44px rgba(26, 168, 160, 0.6),
    0 4px 18px rgba(0, 0, 0, 0.5);
}

.streakup-label {
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: 0.34em;
  text-transform: uppercase;
  color: rgba(170, 230, 224, 0.65);
}

/* ---- star rating ---- */
.streakup-stars {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.8rem;
  min-height: 1px;
}
.star {
  position: relative;
  display: inline-flex;
  width: clamp(26px, 8.5vw, 40px);
  transform-origin: 50% 60%;
  animation: star-pop 0.48s cubic-bezier(0.2, 0.8, 0.3, 1.5) both;
}
.star svg {
  display: block;
  width: 100%;
  height: auto;
  fill: #ffcf4a;
  filter: drop-shadow(0 0 6px rgba(255, 200, 70, 0.85));
}

/* the 6th "bonus" star (streak ≥ 50): bigger, brighter, with a continuous shimmer + halo burst */
.star.bonus {
  width: clamp(34px, 11vw, 54px);
}
.star.bonus svg {
  fill: #c77dff; /* the bonus 6th star is purple, not gold */
  animation: bonus-shimmer 1.5s ease-in-out infinite;
}
.star.bonus::after {
  content: '';
  position: absolute;
  inset: -45%;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(180, 110, 255, 0.6) 0%, transparent 68%);
  z-index: -1;
  animation: bonus-burst 1.6s ease-in-out infinite;
}

/* ---- whole-overlay fade ---- */
.streakup-enter-active,
.streakup-leave-active { transition: opacity 0.45s ease; }
.streakup-enter-from,
.streakup-leave-to { opacity: 0; }

/* ---- the number swap: old "burns off" upward, new "ignites" up from below ---- */
.num-leave-active { animation: num-burn 0.45s ease-in both; }
.num-enter-active { animation: num-ignite 0.55s cubic-bezier(0.2, 0.85, 0.25, 1) both; }

@keyframes num-burn {
  0%   { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
  100% { opacity: 0; transform: translateY(-46px) scale(0.7); filter: blur(7px); }
}
@keyframes num-ignite {
  0%   { opacity: 0; transform: translateY(34px) scale(0.55); filter: blur(5px); }
  55%  { opacity: 1; transform: translateY(-6px) scale(1.14); filter: blur(0); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes streakup-flame-rise {
  0%   { opacity: 0; transform: translateY(26px) scale(0.6); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}

@keyframes streakup-glow-pulse {
  0%, 100% { opacity: 0.6; transform: translate(-50%, -50%) scale(0.95); }
  50%      { opacity: 1;   transform: translate(-50%, -50%) scale(1.07); }
}

/* The flame flicker is shared with StreakCard's intent: sway + stretch from the base while
   the glow breathes, so it reads as actively burning. */
@keyframes flame-dance {
  0%   { transform: scale(1, 1) rotate(0deg);        filter: brightness(1)    drop-shadow(0 0 10px rgba(48, 214, 204, 0.6)); }
  22%  { transform: scale(1.04, 1.08) rotate(-1.6deg); filter: brightness(1.1)  drop-shadow(0 0 16px rgba(72, 236, 226, 0.8)); }
  44%  { transform: scale(0.98, 1.03) rotate(1.1deg);  filter: brightness(1.03) drop-shadow(0 0 12px rgba(48, 214, 204, 0.65)); }
  64%  { transform: scale(1.05, 1.1) rotate(-0.6deg);  filter: brightness(1.14) drop-shadow(0 0 20px rgba(80, 240, 230, 0.9)); }
  84%  { transform: scale(0.99, 1.02) rotate(1.4deg);  filter: brightness(1.04) drop-shadow(0 0 14px rgba(56, 222, 212, 0.7)); }
  100% { transform: scale(1, 1) rotate(0deg);        filter: brightness(1)    drop-shadow(0 0 10px rgba(48, 214, 204, 0.6)); }
}

@keyframes star-pop {
  0%   { opacity: 0; transform: scale(0) rotate(-35deg); }
  60%  { opacity: 1; transform: scale(1.25) rotate(8deg); }
  100% { opacity: 1; transform: scale(1) rotate(0deg); }
}
/* bonus star shimmer: glow + fill brighten/dim, like it's catching the light */
@keyframes bonus-shimmer {
  0%, 100% { fill: #c77dff; filter: drop-shadow(0 0 6px rgba(168, 85, 247, 0.85)) brightness(1); }
  50%      { fill: #f0ddff; filter: drop-shadow(0 0 16px rgba(190, 120, 255, 1)) brightness(1.35); }
}
@keyframes bonus-burst {
  0%, 100% { opacity: 0.4;  transform: scale(0.85); }
  50%      { opacity: 0.85; transform: scale(1.15); }
}

@media (prefers-reduced-motion: reduce) {
  .streakup-flame,
  .streakup-glow,
  .star,
  .star.bonus svg,
  .star.bonus::after { animation: none; }
  .num-leave-active { animation: num-burn-reduced 0.3s ease both; }
  .num-enter-active { animation: num-ignite-reduced 0.3s ease both; }
  @keyframes num-burn-reduced { to { opacity: 0; } }
  @keyframes num-ignite-reduced { from { opacity: 0; } }
}
</style>
