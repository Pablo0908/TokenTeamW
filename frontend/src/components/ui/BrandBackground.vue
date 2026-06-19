<script setup>
// Ambient Lyfter-brand backdrop (from the prototype): drifting color orbs, a panning
// code grid, falling code glyphs and twinkling stars. Purely decorative — fixed behind
// all content, never intercepts taps, and goes still under prefers-reduced-motion.
const glyphs = [
  { c: '{ }', left: '8%', size: '20px', color: 'rgba(113,206,255,.5)', dur: '15s', delay: '0s' },
  { c: '</>', left: '26%', size: '15px', color: 'rgba(215,152,231,.45)', dur: '19s', delay: '4s' },
  { c: '01', left: '68%', size: '18px', color: 'rgba(255,204,139,.42)', dur: '16s', delay: '7s' },
  { c: '{ }', left: '84%', size: '16px', color: 'rgba(173,209,149,.42)', dur: '21s', delay: '2s' },
  { c: ';', left: '46%', size: '14px', color: 'rgba(232,143,149,.4)', dur: '23s', delay: '9s' },
]
const stars = [
  { left: '16%', top: '24%', dur: '4s', delay: '0s' },
  { left: '78%', top: '18%', dur: '5s', delay: '1s' },
  { left: '60%', top: '70%', dur: '6s', delay: '2s' },
  { left: '30%', top: '82%', dur: '4.5s', delay: '.5s' },
  { left: '88%', top: '56%', dur: '5.5s', delay: '1.5s' },
]
</script>

<template>
  <div class="bg" aria-hidden="true">
    <div class="grid-pan" />
    <div class="orb orb-a" />
    <div class="orb orb-b" />
    <div class="orb orb-c" />
    <div class="orb orb-d" />
    <span
      v-for="(g, i) in glyphs"
      :key="'g' + i"
      class="glyph"
      :style="{ left: g.left, fontSize: g.size, color: g.color, animationDuration: g.dur, animationDelay: g.delay }"
    >{{ g.c }}</span>
    <span
      v-for="(s, i) in stars"
      :key="'s' + i"
      class="star"
      :style="{ left: s.left, top: s.top, animationDuration: s.dur, animationDelay: s.delay }"
    />
  </div>
</template>

<style scoped>
.bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
  /* Decorative base gradient (was on <body>, which only covered one viewport and
     cut off on scroll). A fixed layer covers the viewport at any scroll position. */
  background:
    radial-gradient(1100px 600px at 50% -10%, #1b2536 0%, rgba(27, 37, 54, 0) 60%),
    radial-gradient(900px 520px at 100% 110%, #241a36 0%, rgba(36, 26, 54, 0) 55%),
    linear-gradient(180deg, #0c0f16 0%, #090b11 100%);
}

.grid-pan {
  position: absolute;
  inset: -40px;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px);
  background-size: 56px 56px;
  -webkit-mask-image: radial-gradient(120% 90% at 50% 25%, #000 0%, transparent 75%);
  mask-image: radial-gradient(120% 90% at 50% 25%, #000 0%, transparent 75%);
  animation: gridPan 7s linear infinite;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(72px);
  will-change: transform;
}
.orb-a {
  top: -120px;
  left: -90px;
  width: 420px;
  height: 420px;
  background: radial-gradient(circle at 30% 30%, #71ceff, transparent 68%);
  opacity: 0.42;
  animation: orbDrift1 18s ease-in-out infinite, auroraHue 14s ease-in-out infinite;
}
.orb-b {
  bottom: -140px;
  right: -100px;
  width: 460px;
  height: 460px;
  background: radial-gradient(circle at 60% 40%, #d798e7, transparent 68%);
  opacity: 0.36;
  animation: orbDrift2 22s ease-in-out infinite;
}
.orb-c {
  top: 34%;
  right: 4%;
  width: 300px;
  height: 300px;
  background: radial-gradient(circle at 50% 50%, #ffcc8b, transparent 70%);
  opacity: 0.26;
  animation: orbDrift3 26s ease-in-out infinite;
}
.orb-d {
  bottom: 6%;
  left: 4%;
  width: 280px;
  height: 280px;
  background: radial-gradient(circle at 50% 50%, #add195, transparent 70%);
  opacity: 0.22;
  animation: orbDrift1 24s ease-in-out infinite 3s;
}

.glyph {
  position: absolute;
  top: 0;
  font-family: 'Space Grotesk', monospace;
  font-weight: 700;
  animation-name: glyphFall;
  animation-timing-function: linear;
  animation-iteration-count: infinite;
}

.star {
  position: absolute;
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: #fff;
  animation-name: twinkle;
  animation-timing-function: ease-in-out;
  animation-iteration-count: infinite;
}

@keyframes gridPan {
  from { background-position: 0 0; }
  to { background-position: 56px 56px; }
}
@keyframes orbDrift1 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(60px, -40px) scale(1.15); }
  66% { transform: translate(-30px, 30px) scale(0.92); }
}
@keyframes orbDrift2 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-70px, 50px) scale(1.18); }
}
@keyframes orbDrift3 {
  0%, 100% { transform: translate(0, 0) scale(1); }
  40% { transform: translate(40px, 60px) scale(1.1); }
  75% { transform: translate(-50px, -30px) scale(0.95); }
}
@keyframes auroraHue {
  0%, 100% { filter: blur(72px) hue-rotate(0deg); }
  50% { filter: blur(72px) hue-rotate(26deg); }
}
@keyframes glyphFall {
  0% { transform: translateY(-40px); opacity: 0; }
  12% { opacity: 0.5; }
  88% { opacity: 0.5; }
  100% { transform: translateY(105vh); opacity: 0; }
}
@keyframes twinkle {
  0%, 100% { opacity: 0.15; }
  50% { opacity: 0.7; }
}

@media (prefers-reduced-motion: reduce) {
  .grid-pan,
  .orb,
  .glyph,
  .star {
    animation: none;
  }
  .glyph { opacity: 0.2; }
}
</style>
