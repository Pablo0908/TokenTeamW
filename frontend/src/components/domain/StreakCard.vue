<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import medallionAnim from '@/assets/medallion-streak.webp'
import medallionStill from '@/assets/medallion-streak.png'
import FlameIcon from '@/components/domain/FlameIcon.vue'

const props = defineProps({
  value: { type: [Number, String], default: 0 },
  label: { type: String, default: '' },
  tagline: { type: String, default: '' },
})

const displayed = ref(0)
const shaking = ref(false) // true ONLY while the number is counting up; off once it settles

function animateCount(target) {
  const end = Number(target)
  const start = displayed.value
  if (start === end) return
  const steps = 20
  const delta = (end - start) / steps
  // shake only while counting UP — it stops the moment the number is complete
  shaking.value = end > start
  let i = 0
  const tick = setInterval(() => {
    i++
    displayed.value = i < steps ? Math.round(start + delta * i) : end
    if (i >= steps) {
      clearInterval(tick)
      shaking.value = false // number complete → no more shake
    }
  }, 28)
}

// While counting up the shake intensifies as the number climbs: both amplitude and
// speed scale with the current displayed value, so a higher streak shakes harder and
// faster on the way up. (Irrelevant once `shaking` is false — the animation is off.)
const shakeAmp = computed(() => Math.min(2 + displayed.value * 0.8, 12)) // px, capped at 12
const shakeDur = computed(() => Math.max(0.18 - displayed.value * 0.008, 0.07)) // s, faster as it climbs

onMounted(() => animateCount(props.value))
watch(() => props.value, animateCount)
</script>

<template>
  <div class="streak-wrap">
    <div class="medallion">
      <!-- animated medallion; swaps to a still frame when the user prefers reduced motion -->
      <picture>
        <source :srcset="medallionStill" media="(prefers-reduced-motion: reduce)" />
        <img class="medallion-img" :src="medallionAnim" alt="" aria-hidden="true" draggable="false" />
      </picture>

      <!-- crisp vector flame, layered over the baked one so it can be sized independently of
           the ring. Sits where the original flame is; the webp still supplies the orbiting arc. -->
      <div class="flame" aria-hidden="true">
        <div class="flame-inner">
          <FlameIcon />
        </div>
      </div>

      <!-- live count + label, overlaid exactly where the design's number/label sit -->
      <div class="num-slot">
        <span
          class="streak-num"
          :class="{ shaking }"
          :style="{ '--amp': shakeAmp + 'px', '--shake-dur': shakeDur + 's' }"
        >{{ displayed }}</span>
      </div>
      <div class="lbl-slot">
        <span class="streak-lbl">{{ label }}</span>
      </div>
    </div>

    <p v-if="tagline" class="streak-tagline">{{ tagline }}</p>
  </div>
</template>

<style scoped>
.streak-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  /* extra top/side padding gives the bigger glow halo room so it isn't clipped */
  padding: 20px 14px 14px;
  animation: card-in 0.4s ease-out both;
}

/* medallion holds the animated image and is the positioning + sizing context for the
   overlaid number/label (container-query units keep them aligned at any width) */
.medallion {
  position: relative;
  width: 100%;
  max-width: 176px; /* dialed back down again per feedback (152 → 184 → 224 → 196 → 176) */
  aspect-ratio: 310 / 345;
  container-type: inline-size;
}

.medallion-img {
  display: block;
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  -webkit-user-select: none;
  user-select: none;
  /* The glow is a drop-shadow computed from the webp's own alpha EVERY frame, so it hugs the
     brightest pixels — the cyan arc orbiting the ring and the flame — and travels with the
     moving line automatically. Color matches the artwork's teal/cyan, not orange. */
  filter: drop-shadow(0 0 6px rgba(48, 214, 204, 0.75)) drop-shadow(0 0 16px rgba(26, 168, 160, 0.5));
  animation: flame-burn 2.4s ease-in-out infinite;
}

/* The crisp vector flame, layered over the baked one. Size + vertical position are CSS vars so
   they're trivial to tune. transform-origin sits near the base so the flicker dances like fire. */
.flame {
  --flame-size: 27cqw; /* a little smaller per feedback (was 32cqw) */
  --flame-y: 32%;      /* vertical center within the medallion (baked flame ≈ 34%) */
  position: absolute;
  left: 50%;
  top: var(--flame-y);
  width: var(--flame-size);
  transform: translate(-50%, -50%);
  z-index: 1; /* above the webp (later in DOM), below the number (z-index 2) */
  pointer-events: none;
}

.flame-inner {
  transform-origin: 50% 88%;
  filter: drop-shadow(0 0 5px rgba(48, 214, 204, 0.7)) drop-shadow(0 0 14px rgba(26, 168, 160, 0.5));
  animation: flame-dance 2.2s ease-in-out infinite;
}

.flame-inner svg {
  display: block;
  width: 100%;
  height: auto;
}

/* the design's number sits at 49.9% height, the label at 62% — match those anchors */
.num-slot,
.lbl-slot {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2; /* keep the count/label above the flame bloom */
}
.num-slot { top: 49.9%; transform: translate(-50%, -50%); }
.lbl-slot { top: 62%;  transform: translate(-50%, -50%); }

.streak-num {
  display: inline-block;
  font-size: 22cqw;
  font-weight: 900;
  line-height: 1;
  letter-spacing: -0.01em;
  color: #fff;
  /* dark shadow keeps it legible over the flame; cyan glow ties it to the flame's light */
  text-shadow:
    0 2px 10px rgba(0, 0, 0, 0.55),
    0 0 14px rgba(60, 224, 214, 0.7),
    0 0 28px rgba(26, 168, 160, 0.45);
  -webkit-user-select: text;
  user-select: text;
}

/* the number shakes only while counting up; both amplitude (--amp) and speed
   (--shake-dur) scale with the count, so a higher streak shakes harder/faster */
.streak-num.shaking {
  will-change: transform;
  animation: num-shake var(--shake-dur, 0.12s) linear infinite;
}

@keyframes num-shake {
  0%   { transform: translate(calc(var(--amp) * -1), 0) rotate(-1deg); }
  25%  { transform: translate(var(--amp), calc(var(--amp) * -0.5)) rotate(1deg); }
  50%  { transform: translate(calc(var(--amp) * -0.6), var(--amp)) rotate(-1deg); }
  75%  { transform: translate(var(--amp), calc(var(--amp) * 0.4)) rotate(1deg); }
  100% { transform: translate(calc(var(--amp) * -1), 0) rotate(-1deg); }
}

.streak-lbl {
  font-size: 5cqw;
  font-weight: 700;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  white-space: nowrap;
  color: rgba(220, 235, 240, 0.5);
  -webkit-user-select: text;
  user-select: text;
}

.streak-tagline {
  margin-top: -6px;
  font-size: 0.78rem;
  font-weight: 500;
  text-align: center;
  color: rgba(255, 255, 255, 0.55);
}

@keyframes card-in {
  from { opacity: 0; transform: translateY(6px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

/* The fire burns: the cyan glow flickers irregularly and the medallion brightens in uneven
   pulses, like firelight. Because the drop-shadow tracks the webp's alpha per-frame, this
   flicker rides the moving arc + flame. Combined with the webp's own flame motion it reads
   as a live, burning flame. The irregular keyframe spacing avoids a mechanical pulse. */
@keyframes flame-burn {
  0%   { filter: brightness(1)    drop-shadow(0 0 5px rgba(48, 214, 204, 0.70)) drop-shadow(0 0 13px rgba(26, 168, 160, 0.50)); }
  18%  { filter: brightness(1.08) drop-shadow(0 0 9px rgba(64, 228, 218, 0.88)) drop-shadow(0 0 22px rgba(34, 190, 180, 0.62)); }
  34%  { filter: brightness(1.02) drop-shadow(0 0 6px rgba(48, 214, 204, 0.72)) drop-shadow(0 0 15px rgba(26, 168, 160, 0.52)); }
  52%  { filter: brightness(1.12) drop-shadow(0 0 12px rgba(74, 238, 228, 0.92)) drop-shadow(0 0 27px rgba(40, 200, 190, 0.66)); }
  70%  { filter: brightness(1.01) drop-shadow(0 0 6px rgba(48, 214, 204, 0.74)) drop-shadow(0 0 14px rgba(26, 168, 160, 0.50)); }
  86%  { filter: brightness(1.06) drop-shadow(0 0 8px rgba(56, 222, 212, 0.82)) drop-shadow(0 0 19px rgba(33, 182, 173, 0.58)); }
  100% { filter: brightness(1)    drop-shadow(0 0 5px rgba(48, 214, 204, 0.70)) drop-shadow(0 0 13px rgba(26, 168, 160, 0.50)); }
}

/* The vector flame dances: it sways and stretches from its base (transform-origin near the
   bottom) while its glow brightens and dims, so it looks like it's actively burning. */
@keyframes flame-dance {
  0%   { transform: scale(1, 1)        rotate(0deg);    filter: brightness(1)    drop-shadow(0 0 4px rgba(48, 214, 204, 0.6))  drop-shadow(0 0 12px rgba(26, 168, 160, 0.45)); }
  22%  { transform: scale(1.04, 1.08)  rotate(-1.6deg); filter: brightness(1.1)  drop-shadow(0 0 8px rgba(72, 236, 226, 0.85)) drop-shadow(0 0 18px rgba(34, 190, 180, 0.6)); }
  44%  { transform: scale(0.98, 1.03)  rotate(1.1deg);  filter: brightness(1.03) drop-shadow(0 0 5px rgba(48, 214, 204, 0.65)) drop-shadow(0 0 13px rgba(26, 168, 160, 0.48)); }
  64%  { transform: scale(1.05, 1.1)   rotate(-0.6deg); filter: brightness(1.14) drop-shadow(0 0 11px rgba(80, 240, 230, 0.9)) drop-shadow(0 0 22px rgba(40, 200, 190, 0.64)); }
  84%  { transform: scale(0.99, 1.02)  rotate(1.4deg);  filter: brightness(1.04) drop-shadow(0 0 6px rgba(56, 222, 212, 0.7))  drop-shadow(0 0 15px rgba(33, 182, 173, 0.5)); }
  100% { transform: scale(1, 1)        rotate(0deg);    filter: brightness(1)    drop-shadow(0 0 4px rgba(48, 214, 204, 0.6))  drop-shadow(0 0 12px rgba(26, 168, 160, 0.45)); }
}

@media (prefers-reduced-motion: reduce) {
  .streak-wrap,
  .streak-num.shaking,
  .flame-inner,
  .medallion-img { animation: none; }
}
</style>
