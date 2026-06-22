<script setup>
import BrandLogo from '@/components/ui/BrandLogo.vue'

defineEmits(['choose'])
</script>

<template>
  <transition name="welcome-overlay" appear>
    <div class="fixed inset-0 z-[60] flex items-center justify-center p-5">
      <!-- Deep blurred backdrop -->
      <div class="welcome-backdrop absolute inset-0" />

      <!-- Ambient brand orbs bleeding through the blur -->
      <div class="pointer-events-none absolute inset-0 overflow-hidden">
        <div class="welcome-orb welcome-orb-a" />
        <div class="welcome-orb welcome-orb-b" />
      </div>

      <!-- Card — spring-in on enter, staggered children -->
      <div class="welcome-card surface relative w-full max-w-sm overflow-hidden p-7 text-center">
        <!-- One-shot shimmer sweep over the card surface -->
        <div class="welcome-shimmer pointer-events-none absolute inset-0 rounded-3xl" />

        <!-- Logo — spring pop with overshoot -->
        <div class="welcome-logo mx-auto mb-5">
          <BrandLogo :size="52" :show-wordmark="false" class="mx-auto" />
        </div>

        <!-- Headline + subtitle — first content stagger -->
        <div class="welcome-stagger-1 mb-3 space-y-1">
          <h2 class="text-2xl font-bold">Welcome to Lyfter! 👋</h2>
          <p class="text-base font-medium text-base-content/80">¡Bienvenido a Lyfter!</p>
        </div>

        <!-- Body — second stagger -->
        <p class="welcome-stagger-2 mb-5 text-sm text-base-content/60">
          Which language would you like to use?<br />
          ¿En qué idioma quieres usar la app?
        </p>

        <!-- CTA buttons — last stagger -->
        <div class="welcome-stagger-3 flex flex-col gap-2.5">
          <button
            class="btn btn-primary w-full tap-target transition-transform duration-[150ms] ease-out active:scale-[0.97]"
            @click="$emit('choose', 'en')"
          >
            English
          </button>
          <button
            class="btn btn-outline w-full tap-target transition-transform duration-[150ms] ease-out active:scale-[0.97]"
            @click="$emit('choose', 'es')"
          >
            Español
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>
