<script setup>
import { computed } from 'vue'
import { rarityMeta } from '@/utils/rarity'

const props = defineProps({
  badge: { type: Object, required: true }, // { name, icon, color, earned, date, description, rarity, redeemed_by }
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
// Rarity tier only shown for badges the user has earned (it's a reward, not a spoiler).
const rarity = computed(() => (earned.value ? rarityMeta(props.badge.rarity) : null))

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
    class="badge-tilt surface-soft flex w-full flex-col items-center gap-2 rounded-2xl p-3 text-center"
    :class="[clickable ? 'active:scale-95' : '', earned ? '' : 'opacity-70']"
    @click="clickable && $emit('select', badge)"
  >
    <span class="relative">
      <span
        class="grid h-14 w-14 place-items-center overflow-hidden rounded-full bg-gradient-to-b to-transparent text-2xl ring-1"
        :class="[
          earned ? tint : 'text-base-content/40 ring-base-300 from-base-300/40',
          earned ? '' : 'grayscale blur-[2.5px]',
        ]"
      >
        <img v-if="badge.image" :src="badge.image" :alt="badge.name" class="h-full w-full object-cover" />
        <template v-else>{{ badge.icon || '🏅' }}</template>
      </span>
      <!-- Lock glyph over the silhouette -->
      <span
        v-if="!earned"
        class="absolute inset-0 grid place-items-center text-base-content/55"
        aria-hidden="true"
      >
        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75M6 10.5h12a1.5 1.5 0 011.5 1.5v6A1.5 1.5 0 0118 19.5H6A1.5 1.5 0 014.5 18v-6A1.5 1.5 0 016 10.5z" />
        </svg>
      </span>
      <!-- Rarity dot (earned badges with a tier) -->
      <span
        v-if="rarity"
        class="absolute -right-0.5 -top-0.5 h-3 w-3 rounded-full ring-2 ring-base-100"
        :class="rarity.dot"
        :title="badge.rarity"
      />
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
