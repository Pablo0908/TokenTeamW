<script setup>
defineProps({
  title: { type: String, default: '' },
  body:  { type: String, default: '' },
  step:  { type: Number, default: 1 },
  total: { type: Number, default: 3 },
})
defineEmits(['dismiss'])
</script>

<template>
  <div class="pointer-events-auto relative w-64 overflow-hidden rounded-2xl border border-primary/40 bg-base-100/95 p-4 text-left shadow-2xl shadow-black/60 backdrop-blur-md">
    <!-- Progress dots + step counter -->
    <div class="mb-3 flex items-center justify-between">
      <div class="flex gap-1.5">
        <span
          v-for="i in total"
          :key="i"
          :class="[
            'h-1.5 rounded-full transition-all duration-300 ease-out',
            i === step  ? 'w-5 bg-primary' :
            i < step    ? 'w-1.5 bg-primary/45' :
                          'w-1.5 bg-base-content/20',
          ]"
        />
      </div>
      <span class="text-[10px] font-semibold tracking-wide text-base-content/35">
        {{ step }}/{{ total }}
      </span>
    </div>

    <p class="font-display text-sm font-semibold text-primary">{{ title }}</p>
    <p class="mt-1 text-xs leading-relaxed text-base-content/70">{{ body }}</p>

    <button
      class="btn btn-primary btn-xs mt-3 w-full tap-target transition-transform duration-100 ease-out active:scale-[0.97]"
      @click="$emit('dismiss')"
    >
      {{ $t('coach.gotIt') }}
    </button>
  </div>
</template>
