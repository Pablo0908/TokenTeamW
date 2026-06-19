<script setup>
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import NavBar from '@/components/ui/NavBar.vue'
import BrandBackground from '@/components/ui/BrandBackground.vue'
import { useSettingsStore } from '@/stores/settings'
import { useRedeemQueueStore } from '@/stores/redeemQueue'

const route = useRoute()
const settings = useSettingsStore()
const redeemQueue = useRedeemQueueStore()

// Auto-dismiss the offline-sync toast a few seconds after it appears.
watch(
  () => redeemQueue.syncMessage,
  (msg) => {
    if (msg) setTimeout(() => redeemQueue.clearMessage(), 4000)
  },
)

// Bottom tab bar shows only on authenticated participant screens (not the staff/admin area).
const showNav = computed(
  () => route.meta.requiresAuth && !route.meta.requiresAdmin && !route.meta.requiresStaff,
)

// Global colour adjustment (Settings → saturation/contrast). A fixed, click-through
// backdrop-filter layer re-renders everything behind it — applying `filter` to an
// ancestor instead would make the fixed BrandBackground scroll with the page.
const filterActive = computed(() => settings.saturation !== 1 || settings.contrast !== 1)
const filterCss = computed(() => `saturate(${settings.saturation}) contrast(${settings.contrast})`)
</script>

<template>
  <div class="min-h-dvh w-full">
    <div
      v-if="filterActive"
      class="pointer-events-none fixed inset-0 z-[45]"
      aria-hidden="true"
      :style="{ backdropFilter: filterCss, WebkitBackdropFilter: filterCss }"
    />
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

    <!-- Offline-sync toast -->
    <transition name="screen">
      <div
        v-if="redeemQueue.syncMessage"
        class="fixed inset-x-0 bottom-24 z-[55] flex justify-center px-4"
        role="status"
      >
        <div class="surface flex items-center gap-2 rounded-full px-4 py-2 text-sm shadow-2xl shadow-black/40">
          <span class="text-base">✅</span>
          {{ redeemQueue.syncMessage }}
        </div>
      </div>
    </transition>
  </div>
</template>
