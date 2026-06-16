<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: Number, default: 0 },
  max: { type: Number, default: 0 },
  label: { type: String, default: '' },
  showCount: { type: Boolean, default: true },
  unit: { type: String, default: 'badges' },
})

const pct = computed(() => (props.max > 0 ? Math.min(100, Math.round((props.value / props.max) * 100)) : 0))
const complete = computed(() => props.max > 0 && props.value >= props.max)
</script>

<template>
  <div class="w-full">
    <div v-if="label || showCount" class="mb-1.5 flex items-center justify-between text-xs text-base-content/60">
      <span>{{ label }}</span>
      <span v-if="showCount" class="font-medium text-base-content/80">{{ value }} of {{ max }} {{ unit }}</span>
    </div>
    <div
      class="h-2 w-full overflow-hidden rounded-full bg-base-300/70"
      role="progressbar"
      :aria-valuenow="value"
      :aria-valuemin="0"
      :aria-valuemax="max"
    >
      <div
        class="h-full rounded-full bg-gradient-to-r transition-[width] duration-500 ease-out"
        :class="complete ? 'from-success to-primary' : 'from-primary to-secondary'"
        :style="{ width: pct + '%' }"
      />
    </div>
  </div>
</template>
