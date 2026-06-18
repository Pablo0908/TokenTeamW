<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import NavBar from '@/components/ui/NavBar.vue'
import BrandBackground from '@/components/ui/BrandBackground.vue'

const route = useRoute()
// Bottom tab bar shows only on authenticated participant screens (not the staff/admin area).
const showNav = computed(
  () => route.meta.requiresAuth && !route.meta.requiresAdmin && !route.meta.requiresStaff,
)
</script>

<template>
  <div class="min-h-dvh w-full">
    <BrandBackground />
    <div class="relative z-10 mx-auto flex min-h-dvh w-full max-w-md flex-col bg-base-200/30">
      <main class="flex-1" :class="showNav ? 'pb-24' : ''">
        <RouterView v-slot="{ Component }">
          <transition name="screen" mode="out-in">
            <component :is="Component" />
          </transition>
        </RouterView>
      </main>
      <NavBar v-if="showNav" />
    </div>
  </div>
</template>
