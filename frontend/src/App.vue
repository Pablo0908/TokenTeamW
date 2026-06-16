<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import NavBar from '@/components/ui/NavBar.vue'

const route = useRoute()
// Bottom tab bar shows only on authenticated participant screens.
const showNav = computed(() => route.meta.requiresAuth && !route.meta.requiresAdmin)
</script>

<template>
  <div class="min-h-dvh w-full">
    <div class="relative mx-auto flex min-h-dvh w-full max-w-md flex-col bg-base-200/40">
      <main class="flex-1" :class="showNav ? 'pb-24' : ''">
        <RouterView v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </RouterView>
      </main>
      <NavBar v-if="showNav" />
    </div>
  </div>
</template>
