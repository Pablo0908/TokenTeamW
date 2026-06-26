<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: { type: String, default: 'error' }, // info | success | warning | error
  message: { type: String, default: '' },
  dismissible: { type: Boolean, default: false },
})
defineEmits(['close'])

const classes = computed(
  () =>
    ({
      info: 'alert-info',
      success: 'alert-success',
      warning: 'alert-warning',
      error: 'alert-error',
    })[props.type] ?? 'alert-error',
)
</script>

<template>
  <div v-if="message" role="alert" class="alert" :class="classes">
    <span class="text-sm">{{ message }}</span>
    <button
      v-if="dismissible"
      type="button"
      class="btn btn-circle btn-ghost btn-xs tap-target"
      aria-label="Dismiss"
      @click="$emit('close')"
    >
      ✕
    </button>
  </div>
</template>
