<script setup>
import { computed } from 'vue'

// Lightweight, dependency-free bar chart. Two modes, same component:
//  - single series (back-compat): pass `activity` = [{bucket, count}]
//  - multi series: pass `series` = [{label, colorClass, data:[{bucket,count}]}]
// The parent owns the period/date-range controls and refetches when they change.
const props = defineProps({
  activity: { type: Array, default: () => [] },
  series: { type: Array, default: null },
  period: { type: String, default: 'day' }, // label formatting only
  stacked: { type: Boolean, default: false },
})

const DEFAULT_COLORS = ['bg-primary/70', 'bg-secondary/70', 'bg-accent/70']

// Normalize both modes into a list of series with a color.
const seriesList = computed(() => {
  const raw = props.series && props.series.length
    ? props.series
    : [{ label: '', colorClass: DEFAULT_COLORS[0], data: props.activity }]
  return raw.map((s, i) => ({
    label: s.label || '',
    colorClass: s.colorClass || DEFAULT_COLORS[i % DEFAULT_COLORS.length],
    data: s.data || [],
  }))
})
const multi = computed(() => seriesList.value.length > 1)

// Aligned columns across all series (union of buckets, in first-seen order).
const cols = computed(() => {
  const order = []
  const seen = new Set()
  for (const s of seriesList.value) {
    for (const pt of s.data) {
      if (!seen.has(pt.bucket)) { seen.add(pt.bucket); order.push(pt.bucket) }
    }
  }
  return order.map((bucket) => ({
    bucket,
    values: seriesList.value.map((s) => (s.data.find((p) => p.bucket === bucket)?.count ?? 0)),
  }))
})

const maxCount = computed(() => {
  if (props.stacked) return cols.value.reduce((m, c) => Math.max(m, c.values.reduce((a, b) => a + b, 0)), 0)
  return cols.value.reduce((m, c) => Math.max(m, ...c.values), 0)
})
const hasData = computed(() => cols.value.length > 0 && maxCount.value > 0)

function barLabel(bucket) {
  if (!bucket) return ''
  const d = new Date(bucket)
  if (Number.isNaN(d.getTime())) return ''
  if (props.period === 'month') return d.toLocaleDateString(undefined, { month: 'short', year: '2-digit' })
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}
function barHeight(count) {
  return maxCount.value > 0 ? `${Math.max(count > 0 ? 6 : 0, (count / maxCount.value) * 100)}%` : '0%'
}
</script>

<template>
  <div>
    <div v-if="hasData" class="flex h-32 items-end gap-1">
      <div v-for="col in cols" :key="col.bucket" class="flex h-full flex-1 items-end" :class="stacked ? 'flex-col-reverse' : 'gap-0.5'">
        <div
          v-for="(v, i) in col.values"
          :key="i"
          class="rounded-t transition-colors"
          :class="[seriesList[i].colorClass, stacked ? 'w-full' : 'flex-1']"
          :style="{ height: barHeight(v) }"
          :title="`${barLabel(col.bucket)}${seriesList[i].label ? ' · ' + seriesList[i].label : ''}: ${v}`"
        />
      </div>
    </div>
    <p v-else class="py-8 text-center text-sm text-base-content/50">{{ $t('insights.noActivity') }}</p>

    <div v-if="hasData" class="mt-2 flex justify-between text-[0.65rem] text-base-content/45">
      <span>{{ barLabel(cols[0].bucket) }}</span>
      <span>{{ barLabel(cols[cols.length - 1].bucket) }}</span>
    </div>

    <div v-if="multi" class="mt-2 flex flex-wrap gap-3">
      <span v-for="s in seriesList" :key="s.label" class="flex items-center gap-1 text-[0.65rem] text-base-content/55">
        <span class="inline-block h-2.5 w-2.5 rounded-sm" :class="s.colorClass" />{{ s.label }}
      </span>
    </div>
  </div>
</template>
