<script setup>
import { ref } from 'vue'

defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '••••••••' },
  autocomplete: { type: String, default: 'current-password' },
  inputClass: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const visible = ref(false)

function show() { visible.value = true }
function hide() { visible.value = false }
</script>

<template>
  <div class="relative">
    <input
      :value="modelValue"
      :type="visible ? 'text' : 'password'"
      :placeholder="placeholder"
      :autocomplete="autocomplete"
      class="input input-bordered w-full bg-base-100/70 pr-11"
      :class="inputClass"
      @input="emit('update:modelValue', $event.target.value)"
    />
    <button
      type="button"
      tabindex="-1"
      class="absolute right-3 top-1/2 -translate-y-1/2 text-base-content/40 hover:text-base-content/70 select-none touch-none"
      @mousedown.prevent="show"
      @mouseup="hide"
      @mouseleave="hide"
      @touchstart.prevent="show"
      @touchend="hide"
      @touchcancel="hide"
    >
      <!-- eye-off (password hidden) -->
      <svg v-if="!visible" class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M17.94 17.94A10.94 10.94 0 0112 20C6 20 1 12 1 12a18.9 18.9 0 015.06-5.94"/>
        <path d="M9.9 4.24A9.12 9.12 0 0112 4c6 0 11 8 11 8a18.9 18.9 0 01-2.13 3.11"/>
        <line x1="1" y1="1" x2="23" y2="23"/>
      </svg>
      <!-- eye (password visible) -->
      <svg v-else class="h-5 w-5 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
        <circle cx="12" cy="12" r="3"/>
      </svg>
    </button>
  </div>
</template>
