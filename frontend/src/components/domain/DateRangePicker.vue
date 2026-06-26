<script setup>
import { ref, onMounted } from 'vue'
import { t } from '@/i18n'

// Period (bucket granularity) + a quick date-range preset. Emits `change` with
// { period, start, end } (ISO date strings; start='' for "all"). Parents pass these
// straight to the analytics endpoints as query params.
const emit = defineEmits(['change'])

const PERIODS = ['day', 'week', 'month']
const PRESETS = [
  { key: '7d', label: '7d', days: 7, period: 'day' },
  { key: '30d', label: '30d', days: 30, period: 'day' },
  { key: '90d', label: '90d', days: 90, period: 'week' },
  { key: 'all', label: 'All', days: null, period: 'month' },
]

const period = ref('day')
const preset = ref('30d')

const PRESET_KEY = { '7d': 'd7', '30d': 'd30', '90d': 'd90', all: 'all' }
const presetLabel = (key) => t(`dateRange.${PRESET_KEY[key] || key}`)
const periodLabel = (p) => t(`dateRange.${p}`)

function isoDate(d) { return d.toISOString().slice(0, 10) }

function payload() {
  const now = new Date()
  const p = PRESETS.find((x) => x.key === preset.value) || PRESETS[1]
  let start = ''
  if (p.days !== null) {
    const s = new Date(now)
    s.setDate(s.getDate() - p.days)
    start = isoDate(s)
  } else {
    start = '2000-01-01' // "all": far enough back to capture full history
  }
  return { period: period.value, start, end: isoDate(now) }
}

function setPreset(key) {
  if (preset.value === key) return
  preset.value = key
  const p = PRESETS.find((x) => x.key === key)
  if (p) period.value = p.period // sensible default granularity for the span
  emit('change', payload())
}
function setPeriod(p) {
  if (period.value === p) return
  period.value = p
  emit('change', payload())
}

onMounted(() => emit('change', payload()))
</script>

<template>
  <div class="flex flex-wrap items-center justify-between gap-2">
    <div role="tablist" class="tabs tabs-boxed tabs-xs bg-base-300/40">
      <button
        v-for="p in PRESETS"
        :key="p.key"
        role="tab"
        class="tab"
        :class="{ 'tab-active': preset === p.key }"
        @click="setPreset(p.key)"
      >{{ presetLabel(p.key) }}</button>
    </div>
    <div role="tablist" class="tabs tabs-boxed tabs-xs bg-base-300/40">
      <button
        v-for="p in PERIODS"
        :key="p"
        role="tab"
        class="tab capitalize"
        :class="{ 'tab-active': period === p }"
        @click="setPeriod(p)"
      >{{ periodLabel(p) }}</button>
    </div>
  </div>
</template>
