<script setup>
import { computed } from 'vue'

// Lightweight, dependency-free bar chart for a per-period activity series
// ([{ bucket: ISO date, count }], oldest→newest). Shared by the per-user analytics
// panel and the org dashboard. Purely presentational — the parent owns the period
// tabs and refetches when the period changes.
const props = defineProps({
  activity: { type: Array, default: () => [] },
  period: { type: String, default: 'day' }, // day | week | month — label formatting only
})

const maxCount = computed(() => props.activity.reduce((m, b) => Math.max(m, b.count), 0))

function barLabel(bucket) {
  if (!bucket) return ''
  const d = new Date(bucket)
  if (Number.isNaN(d.getTime())) return ''
  if (props.period === 'month') return d.toLocaleDateString(undefined, { month: 'short', year: '2-digit' })
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}
function barHeight(count) {
  return maxCount.value > 0 ? `${Math.max(6, (count / maxCount.value) * 100)}%` : '6%'
}
</script>

<template>
  <div v-if="activity.length" class="flex h-32 items-end gap-1">
    <div
      v-for="b in activity"
      :key="b.bucket"
      class="group relative flex-1 rounded-t bg-primary/70 transition-colors hover:bg-primary"
      :style="{ height: barHeight(b.count) }"
      :title="`${barLabel(b.bucket)}: ${b.count}`"
    />
  </div>
  <p v-else class="py-8 text-center text-sm text-base-content/50">No activity in range.</p>
  <div v-if="activity.length" class="mt-2 flex justify-between text-[0.65rem] text-base-content/45">
    <span>{{ barLabel(activity[0].bucket) }}</span>
    <span>{{ barLabel(activity[activity.length - 1].bucket) }}</span>
  </div>
</template>
