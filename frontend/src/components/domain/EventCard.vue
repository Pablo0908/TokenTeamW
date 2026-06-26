<script setup>
import { computed } from 'vue'
import { t, locale } from '@/i18n'
import ProgressBar from './ProgressBar.vue'

const props = defineProps({
  event: { type: Object, required: true },
  clickable: { type: Boolean, default: true },
})
defineEmits(['select'])

const earned = computed(() => props.event.badges_earned ?? 0)
const total = computed(() => props.event.badges_total ?? 0)
const completed = computed(() => props.event.completed || (total.value > 0 && earned.value >= total.value))

const status = computed(() => {
  // A locked (paused) event is flagged distinctly even if the user has completed it.
  if (props.event.status === 'locked') return { label: t('events.status.locked'), cls: 'badge-warning' }
  if (completed.value) return { label: t('events.status.completed'), cls: 'badge-primary' }
  switch (props.event.status) {
    case 'active':
      return { label: t('events.status.active'), cls: 'badge-success' }
    case 'upcoming':
      return { label: t('events.status.upcoming'), cls: 'badge-secondary' }
    case 'past':
      return { label: t('events.status.past'), cls: 'badge-ghost text-base-content/60' }
    default:
      return { label: t('events.status.event'), cls: 'badge-ghost' }
  }
})

const statusRing = computed(() => {
  if (props.event.status === 'locked') return 'ring-1 ring-warning/40 shadow-warning/10 shadow-lg'
  if (completed.value) return 'ring-1 ring-primary/40 shadow-primary/10 shadow-lg'
  switch (props.event.status) {
    case 'active': return 'ring-1 shadow-lg'
    case 'upcoming': return 'ring-1 shadow-md'
    default: return 'opacity-75'
  }
})

// Org-colored ring — uses org's accent/primary when available, falls back to status colors
const ringStyle = computed(() => {
  const color = accent.value
  if (!color) return {}
  if (props.event.status === 'active') {
    return { '--tw-ring-color': color + '80', boxShadow: `0 0 0 1px ${color}80, 0 10px 15px -3px ${color}26` }
  }
  if (props.event.status === 'upcoming') {
    return { '--tw-ring-color': color + '59', boxShadow: `0 0 0 1px ${color}59, 0 4px 6px -1px ${color}1a` }
  }
  return {}
})

const visibilityLabel = computed(() =>
  props.event.visibility ? t(`visibility.${props.event.visibility}`) : '',
)

// Per-org branding on the card: a left accent strip + the org's logo/name.
const accent = computed(() => props.event.org?.theme?.accent || props.event.org?.theme?.primary || '')
const orgLogo = computed(() => props.event.org?.theme?.logo_url || '')
const orgName = computed(() => props.event.org?.name || '')
const orgInitials = computed(() => orgName.value.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase() || '')

const dateLabel = computed(() => {
  const fmt = (iso) => {
    const d = new Date(iso)
    return Number.isNaN(d.getTime())
      ? ''
      : d.toLocaleDateString(locale.value === 'es' ? 'es' : 'en-US', { month: 'short', day: 'numeric' })
  }
  const start = fmt(props.event.date)
  const end = props.event.endDate ? fmt(props.event.endDate) : ''
  if (start && end && end !== start) return `${start} – ${end}`
  return start || t('events.dateTba')
})
</script>

<template>
  <component
    :is="clickable ? 'button' : 'div'"
    type="button"
    class="surface w-full space-y-3 p-4 text-left transition-transform"
    :class="[clickable ? 'active:scale-[0.98]' : '', statusRing]"
    :style="{ ...(accent ? { borderLeft: `3px solid ${accent}` } : {}), ...ringStyle }"
    @click="clickable && $emit('select', event)"
  >
    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0">
        <h3 class="truncate font-semibold text-base-content">{{ event.name }}</h3>
        <p class="mt-0.5 flex items-center gap-1.5 text-xs text-base-content/55">
          <!-- Org attribution: logo or initials + name -->
          <template v-if="orgName">
            <img v-if="orgLogo" :src="orgLogo" alt="" class="h-3.5 w-3.5 shrink-0 rounded object-cover" />
            <span v-else class="inline-grid h-3.5 w-3.5 shrink-0 place-items-center rounded bg-primary/20 text-[8px] font-bold text-primary">{{ orgInitials }}</span>
            <span class="font-medium text-base-content/70">{{ orgName }}</span>
            <span class="text-base-content/30">·</span>
          </template>
          <svg class="h-3.5 w-3.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M6.75 3v2.25M17.25 3v2.25M3 7.5h18M5.25 5.25h13.5A2.25 2.25 0 0121 7.5v11.25A2.25 2.25 0 0118.75 21H5.25A2.25 2.25 0 013 18.75V7.5a2.25 2.25 0 012.25-2.25z" />
          </svg>
          {{ dateLabel }}
        </p>
      </div>
      <div class="flex shrink-0 flex-col items-end gap-1">
        <span class="badge badge-md border-0 font-semibold" :class="status.cls">
          <span v-if="event.status === 'active' && !completed" class="inline-block h-1.5 w-1.5 rounded-full bg-success animate-pulse mr-1" />
          {{ status.label }}
        </span>
        <span
          v-if="event.visibility && event.visibility !== 'public'"
          class="badge badge-xs badge-ghost capitalize"
        >{{ visibilityLabel }}</span>
      </div>
    </div>

    <ProgressBar
      :value="earned"
      :max="total"
      :show-count="true"
      :unit="$t('events.unitBadges')"
      :label="completed ? $t('events.status.completed') : $t('events.progress')"
    />
  </component>
</template>
