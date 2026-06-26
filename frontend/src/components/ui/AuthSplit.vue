<script setup>
import BrandLogo from '@/components/ui/BrandLogo.vue'

// Feature i18n keys shown on the desktop hero panel.
const featureKeys = ['heroF1', 'heroF2', 'heroF3']
</script>

<template>
  <div class="lg:grid lg:min-h-dvh lg:grid-cols-2">
    <!-- Brand hero — desktop only; fills the empty half of the page. -->
    <aside class="relative hidden overflow-hidden lg:flex lg:flex-col lg:justify-center lg:px-16 lg:py-14">
      <div
        class="pointer-events-none absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-secondary/10"
        aria-hidden="true"
      />
      <div class="relative max-w-lg anim-rise">
        <BrandLogo :size="76" wordmark-class="text-4xl" :float="true" />
        <h2 class="mt-10 font-display text-4xl font-bold leading-tight">{{ $t('auth.heroTitle') }}</h2>
        <p class="mt-4 text-lg text-base-content/60">{{ $t('auth.heroSubtitle') }}</p>
        <ul class="mt-9 space-y-4">
          <li
            v-for="k in featureKeys"
            :key="k"
            class="flex items-center gap-3 text-base-content/75"
          >
            <span class="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-primary/15 text-primary">
              <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4.5 12.75l6 6 9-13.5" />
              </svg>
            </span>
            <span class="font-medium">{{ $t('auth.' + k) }}</span>
          </li>
        </ul>
      </div>
    </aside>

    <!-- Form column — identical to the previous single-column auth screen on mobile. -->
    <div class="flex min-h-dvh flex-col justify-center px-6 py-10">
      <div class="mx-auto w-full max-w-md">
        <slot />
      </div>
    </div>
  </div>
</template>
