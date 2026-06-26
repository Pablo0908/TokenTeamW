<script>
// Module-scoped counter → a unique gradient id per instance, so multiple flames can render
// on the same page (e.g. the streak card and the full-screen celebration) without their
// <linearGradient> ids colliding.
let _flameUid = 0
</script>

<script setup>
const gradId = `streak-flame-${(_flameUid += 1)}`
</script>

<template>
  <!-- Crisp vector flame in the artwork's teal/cyan. Resolution-independent, so it stays
       sharp at any size. Shared by StreakCard and StreakUpOverlay. -->
  <svg viewBox="3 1 18 22" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <defs>
      <linearGradient :id="gradId" x1="12" y1="2" x2="12" y2="23" gradientUnits="userSpaceOnUse">
        <stop offset="0" stop-color="#7ff6ec" />
        <stop offset="0.45" stop-color="#33d6ca" />
        <stop offset="1" stop-color="#0e8279" />
      </linearGradient>
    </defs>
    <path
      d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"
      :fill="`url(#${gradId})`"
    />
  </svg>
</template>

<style scoped>
svg {
  display: block;
  width: 100%;
  height: auto;
}
</style>
