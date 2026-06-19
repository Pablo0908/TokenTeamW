<script setup>
import BrandLogo from '@/components/ui/BrandLogo.vue'

// First-run greeting + language picker. Bilingual on purpose so it reads for both
// audiences before a language is chosen.
defineEmits(['choose'])
</script>

<template>
  <transition name="screen" appear>
    <div class="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 p-5 backdrop-blur-sm">
      <div class="surface anim-pop w-full max-w-sm space-y-5 p-7 text-center">
        <BrandLogo :size="52" :show-wordmark="false" class="mx-auto" />

        <div class="space-y-1">
          <h2 class="text-2xl font-bold">Welcome to Lyfter! 👋</h2>
          <p class="text-base font-medium text-base-content/80">¡Bienvenido a Lyfter!</p>
        </div>

        <p class="text-sm text-base-content/60">
          Which language would you like to use?<br />¿En qué idioma quieres usar la app?
        </p>

        <div class="flex flex-col gap-2.5">
          <button class="btn btn-primary w-full tap-target" @click="$emit('choose', 'en')">English</button>
          <button class="btn btn-outline w-full tap-target" @click="$emit('choose', 'es')">Español</button>
        </div>
      </div>
    </div>
  </transition>
</template>
