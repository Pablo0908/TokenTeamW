<script setup>
// Small onboarding callout anchored to a feature. The parent positions it absolutely.
defineProps({
  title: { type: String, default: '' },
  body: { type: String, default: '' },
})
defineEmits(['dismiss'])
</script>

<template>
  <div class="anim-rise pointer-events-auto relative w-60 rounded-xl border border-primary/45 bg-base-100/95 p-3.5 text-left shadow-2xl shadow-black/50 backdrop-blur">
    <p class="font-display text-sm font-semibold text-primary">{{ title }}</p>
    <p class="mt-1 text-xs leading-relaxed text-base-content/70">{{ body }}</p>
    <button class="btn btn-primary btn-xs mt-2.5 w-full tap-target" @click="$emit('dismiss')">
      {{ $t('coach.gotIt') }}
    </button>
  </div>
</template>
