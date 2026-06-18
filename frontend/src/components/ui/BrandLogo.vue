<script setup>
// Official Lyfter isotipo (extracted from the brand manual) + optional "Lyfter" wordmark
// typeset in the brand display font.
import logo from '@/assets/lyfter-logo.png'

defineProps({
  size: { type: Number, default: 40 },
  showWordmark: { type: Boolean, default: true },
  wordmarkClass: { type: String, default: 'text-xl' },
})
</script>

<template>
  <span class="inline-flex items-center gap-2.5">
    <img
      :src="logo"
      alt="Lyfter"
      :style="{ width: size + 'px', height: size + 'px' }"
      class="shrink-0 select-none"
      draggable="false"
    />
    <span v-if="showWordmark" class="font-display font-bold tracking-tight text-base-content" :class="wordmarkClass">
      Lyfter
    </span>
  </span>
</template>
