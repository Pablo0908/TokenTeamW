<script setup>
// Official Lyfter isotipo (extracted from the brand manual) + optional "Lyfter" wordmark
// typeset in the brand display font.
import logo from '@/assets/lyfter-logo.png'

defineProps({
  size: { type: Number, default: 40 },
  showWordmark: { type: Boolean, default: true },
  wordmarkClass: { type: String, default: 'text-xl' },
  // Gentle idle float on the whole lockup — isotipo + wordmark move together
  // (used on the auth screens). Honors the app's reduced-motion and "extra effects
  // off" settings via the .anim-float opt-outs.
  float: { type: Boolean, default: false },
})
</script>

<template>
  <span class="inline-flex">
    <span class="inline-flex items-center gap-2.5" :class="{ 'anim-float': float }">
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
  </span>
</template>
