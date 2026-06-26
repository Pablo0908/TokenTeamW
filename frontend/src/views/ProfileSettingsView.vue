<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const initials = computed(() => {
  const n = auth.user?.name ?? ''
  const l = auth.user?.lastname ?? ''
  return ((n[0] ?? '') + (l[0] ?? '')).toUpperCase() || (auth.user?.email?.[0] ?? 'U').toUpperCase()
})

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="space-y-6 px-4 pb-4 pt-6">
    <!-- Header -->
    <header class="flex items-center gap-3">
      <button type="button" class="tap-target -ml-2 grid h-10 w-10 place-items-center rounded-2xl transition-colors hover:bg-base-300/40" @click="router.back()">
        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M15 18l-6-6 6-6"/>
        </svg>
      </button>
      <h1 class="text-xl font-bold">{{ $t('settings.title') }}</h1>
    </header>

    <!-- User card -->
    <div class="surface flex items-center gap-3 p-4">
      <span class="relative h-12 w-12 shrink-0">
        <img
          v-if="auth.user?.avatar_url"
          :src="auth.user.avatar_url"
          class="h-12 w-12 rounded-full object-cover"
          alt=""
        />
        <span
          v-else
          class="grid h-12 w-12 place-items-center rounded-full bg-gradient-to-br from-primary to-secondary text-base font-bold text-primary-content"
        >{{ initials }}</span>
      </span>
      <div class="min-w-0 flex-1">
        <p class="font-semibold">{{ [auth.user?.name, auth.user?.lastname].filter(Boolean).join(' ') || auth.displayName }}</p>
        <p class="truncate text-sm text-base-content/55">{{ auth.user?.email }}</p>
      </div>
    </div>

    <!-- Profile & Security section -->
    <section class="space-y-2">
      <p class="text-[0.65rem] font-semibold uppercase tracking-widest text-base-content/40 px-1">{{ $t('settings.profileSecurity') }}</p>

      <div class="surface overflow-hidden divide-y divide-base-300/40">
        <!-- Edit profile -->
        <RouterLink
          to="/profile/edit-name"
          class="flex w-full items-center gap-3 p-4 transition-colors active:bg-base-300/30"
        >
          <span class="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-primary/15">
            <svg class="h-5 w-5 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>
            </svg>
          </span>
          <div class="min-w-0 flex-1">
            <p class="text-sm font-semibold">{{ $t('settings.editProfileTitle') }}</p>
            <p class="text-xs text-base-content/50">{{ $t('settings.editProfileHint') }}</p>
          </div>
          <svg class="h-4 w-4 shrink-0 text-base-content/40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 18l6-6-6-6"/>
          </svg>
        </RouterLink>

        <!-- Change photo -->
        <RouterLink
          to="/profile/change-photo"
          class="flex w-full items-center gap-3 p-4 transition-colors active:bg-base-300/30"
        >
          <span class="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-secondary/15">
            <svg class="h-5 w-5 text-secondary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/>
              <circle cx="12" cy="13" r="4"/>
            </svg>
          </span>
          <div class="min-w-0 flex-1">
            <p class="text-sm font-semibold">{{ $t('settings.changePhoto') }}</p>
            <p class="text-xs text-base-content/50">{{ $t('settings.changePhotoHint') }}</p>
          </div>
          <svg class="h-4 w-4 shrink-0 text-base-content/40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 18l6-6-6-6"/>
          </svg>
        </RouterLink>

        <!-- Change password -->
        <RouterLink
          to="/profile/change-password"
          class="flex w-full items-center gap-3 p-4 transition-colors active:bg-base-300/30"
        >
          <span class="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-accent/15">
            <svg class="h-5 w-5 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/>
            </svg>
          </span>
          <div class="min-w-0 flex-1">
            <p class="text-sm font-semibold">{{ $t('settings.changePassword') }}</p>
            <p class="text-xs text-base-content/50">{{ $t('settings.changePasswordHint') }}</p>
          </div>
          <svg class="h-4 w-4 shrink-0 text-base-content/40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 18l6-6-6-6"/>
          </svg>
        </RouterLink>
      </div>
    </section>

    <!-- Log out -->
    <button class="surface flex w-full items-center gap-3 p-4 text-error transition-colors active:bg-error/10 tap-target" @click="logout">
      <span class="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-error/15">
        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9"/>
        </svg>
      </span>
      <p class="text-sm font-semibold">{{ $t('common.logout') }}</p>
    </button>
  </div>
</template>
