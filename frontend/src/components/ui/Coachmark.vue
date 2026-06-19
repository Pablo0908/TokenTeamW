<script setup>
// Small onboarding callout anchored to a feature. The parent positions it absolutely;
// `arrow` is which edge the pointer sits on (pointing toward the target).
defineProps({
  title: { type: String, default: '' },
  body: { type: String, default: '' },
  arrow: { type: String, default: 'up' }, // up | down
})
defineEmits(['dismiss'])
</script>

<template>
  <div class="anim-rise pointer-events-auto relative w-60 rounded-2xl border border-primary/45 bg-base-100/95 p-3.5 text-left shadow-2xl shadow-black/50 backdrop-blur">
    <span
      class="absolute left-1/2 h-3 w-3 -translate-x-1/2 rotate-45 border-primary/45 bg-base-100/95"
      :class="arrow === 'up' ? '-top-1.5 border-l border-t' : '-bottom-1.5 border-b border-r'"
    />
    <p class="font-display text-sm font-semibold text-primary">{{ title }}</p>
    <p class="mt-1 text-xs leading-relaxed text-base-content/70">{{ body }}</p>
    <button class="btn btn-primary btn-xs mt-2.5 w-full tap-target" @click="$emit('dismiss')">
      {{ $t('coach.gotIt') }}
    </button>
  </div>
</template>
