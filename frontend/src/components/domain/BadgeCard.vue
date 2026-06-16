<script setup>
import { computed } from 'vue'

const props = defineProps({
  badge: { type: Object, required: true }, // { name, icon, color, earned, date, description }
  clickable: { type: Boolean, default: false },
})
defineEmits(['select'])

// Static class strings so Tailwind keeps them during purge.
const palette = {
  primary: 'text-primary ring-primary/40 from-primary/25',
  secondary: 'text-secondary ring-secondary/40 from-secondary/25',
  accent: 'text-accent ring-accent/40 from-accent/25',
  success: 'text-success ring-success/40 from-success/25',
  info: 'text-info ring-info/40 from-info/25',
  warning: 'text-warning ring-warning/40 from-warning/25',
  error: 'text-error ring-error/40 from-error/25',
}

const tint = computed(() => palette[props.badge.color] ?? palette.primary)
const earned = computed(() => !!props.badge.earned)

const earnedDate = computed(() => {
  if (!props.badge.date) return ''
  const d = new Date(props.badge.date)
  return Number.isNaN(d.getTime())
    ? ''
    : d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
})
</script>

<template>
  <component
    :is="clickable ? 'button' : 'div'"
    type="button"
    class="surface-soft flex w-full flex-col items-center gap-2 rounded-2xl p-3 text-center transition-transform"
    :class="[clickable ? 'active:scale-95' : '', earned ? '' : 'opacity-60']"
    @click="clickable && $emit('select', badge)"
  >
    <span
      class="grid h-14 w-14 place-items-center rounded-full bg-gradient-to-b to-transparent text-2xl ring-1"
      :class="earned ? tint : 'text-base-content/40 ring-base-300 grayscale from-base-300/40'"
    >
      {{ badge.icon || '🏅' }}
    </span>
    <span class="line-clamp-1 text-sm font-medium text-base-content">{{ badge.name }}</span>
    <span
      v-if="earned"
      class="text-[0.7rem] text-base-content/50"
    >{{ earnedDate || 'Earned' }}</span>
    <span
      v-else
      class="inline-flex items-center gap-1 rounded-full bg-base-300/70 px-2 py-0.5 text-[0.65rem] text-base-content/50"
    >
      <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <path d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75M6 10.5h12a1.5 1.5 0 011.5 1.5v6A1.5 1.5 0 0118 19.5H6A1.5 1.5 0 014.5 18v-6A1.5 1.5 0 016 10.5z" />
      </svg>
      Locked
    </span>
  </component>
</template>
