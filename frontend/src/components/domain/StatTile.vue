<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: [Number, String], default: 0 },
  label: { type: String, default: '' },
  tone: { type: String, default: 'primary' }, // primary | secondary | accent
  // Optional period-over-period change (percent). null/undefined => no chip shown.
  delta: { type: Number, default: null },
})

const tones = {
  primary: 'text-primary border-primary/30',
  secondary: 'text-secondary border-secondary/30',
  accent: 'text-accent border-accent/30',
}
const cls = computed(() => tones[props.tone] ?? tones.primary)

const hasDelta = computed(() => props.delta !== null && props.delta !== undefined)
const deltaCls = computed(() =>
  props.delta > 0 ? 'text-success' : props.delta < 0 ? 'text-error' : 'text-base-content/45',
)
const deltaText = computed(() => {
  if (!hasDelta.value) return ''
  const arrow = props.delta > 0 ? '▲' : props.delta < 0 ? '▼' : '■'
  return `${arrow} ${Math.abs(props.delta)}%`
})
</script>

<template>
  <div class="surface-soft flex flex-col items-center justify-center rounded-2xl border px-2 py-3" :class="cls">
    <span class="text-2xl font-bold leading-none">{{ value }}</span>
    <span class="mt-1 text-[0.7rem] uppercase tracking-wide text-base-content/55">{{ label }}</span>
    <span v-if="hasDelta" class="mt-1 text-[0.65rem] font-medium" :class="deltaCls">{{ deltaText }}</span>
  </div>
</template>
