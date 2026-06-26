<script setup>
defineProps({
  label: { type: String, default: 'Loading…' },
  size: { type: String, default: 'lg' }, // sm | md | lg
})
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-3 py-12 text-base-content/70">
    <span class="loading loading-spinner text-primary" :class="`loading-${size}`" />
    <span v-if="label" class="text-sm">{{ label }}</span>
  </div>
</template>
