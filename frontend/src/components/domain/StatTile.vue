<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: [Number, String], default: 0 },
  label: { type: String, default: '' },
  tone: { type: String, default: 'primary' }, // primary | secondary | accent
})

const tones = {
  primary: 'text-primary border-primary/30',
  secondary: 'text-secondary border-secondary/30',
  accent: 'text-accent border-accent/30',
}
const cls = computed(() => tones[props.tone] ?? tones.primary)
</script>

<template>
  <div class="surface-soft flex flex-col items-center justify-center rounded-2xl border px-2 py-3" :class="cls">
    <span class="text-2xl font-bold leading-none">{{ value }}</span>
    <span class="mt-1 text-[0.7rem] uppercase tracking-wide text-base-content/55">{{ label }}</span>
  </div>
</template>
