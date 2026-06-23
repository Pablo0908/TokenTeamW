<script setup>
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import NavBar from '@/components/ui/NavBar.vue'
import BrandBackground from '@/components/ui/BrandBackground.vue'
import { useSettingsStore } from '@/stores/settings'
import { useRedeemQueueStore } from '@/stores/redeemQueue'

const route = useRoute()
const router = useRouter()
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

const showAdminClose = computed(
  () => route.meta.requiresAdmin || route.meta.requiresStaff,
)

// Global colour adjustment (Settings → saturation/contrast). A fixed, click-through
// backdrop-filter layer re-renders everything behind it — applying `filter` to an
// ancestor instead would make the fixed BrandBackground scroll with the page.
const filterActive = computed(() => settings.saturation !== 1 || settings.contrast !== 1)
const filterCss = computed(() => `saturate(${settings.saturation}) contrast(${settings.contrast})`)
</script>

<template>
  <!-- Full-page routes (event preview) bypass the app shell entirely -->
  <RouterView v-if="route.meta.fullPage" />

  <div v-else class="min-h-dvh w-full">
    <div
      v-if="filterActive"
      class="pointer-events-none fixed inset-0 z-[45]"
      aria-hidden="true"
      :style="{ backdropFilter: filterCss, WebkitBackdropFilter: filterCss }"
    />
    <BrandBackground />
    <div class="relative z-10 mx-auto flex min-h-dvh w-full max-w-md flex-col bg-base-200/30">
      <main class="flex-1" :class="showNav || showAdminClose ? 'pb-24' : ''">
        <RouterView v-slot="{ Component }">
          <transition name="screen" mode="out-in">
            <component :is="Component" />
          </transition>
        </RouterView>
      </main>
      <NavBar v-if="showNav" />
      <div v-if="showAdminClose" class="fixed inset-x-0 bottom-0 z-40 pb-[env(safe-area-inset-bottom)]">
        <div class="mx-auto max-w-md flex justify-center pb-4 anim-rise">
          <div class="relative">
            <!-- Ambient glow orb behind the button -->
            <div class="absolute inset-0 scale-150 rounded-full bg-primary/20 blur-xl" aria-hidden="true" />
            <button
              class="surface relative overflow-hidden flex items-center gap-2.5 rounded-full border-primary/30 px-6 py-3 shadow-2xl shadow-black/50 tap-target anim-pulse-glow transition-all duration-150 active:scale-95"
              @click="router.push('/')"
            >
              <!-- Shimmer sweep using the existing shine keyframe -->
              <span
                class="pointer-events-none absolute inset-0 rounded-full"
                style="background: linear-gradient(115deg, transparent 35%, rgba(255,255,255,0.08) 50%, transparent 65%); animation: shine 3.5s ease-in-out 1s infinite;"
                aria-hidden="true"
              />
              <svg
                class="relative h-4 w-4 text-primary drop-shadow-[0_0_8px_rgba(45,212,191,0.9)]"
                viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
              >
                <path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
              <span class="relative text-sm font-semibold text-primary">Back to app</span>
            </button>
          </div>
        </div>
      </div>
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
