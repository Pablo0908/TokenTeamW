<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAnnouncementsStore } from '@/stores/announcements'
import { useOrgContextStore } from '@/stores/orgContext'
import BrandLogo from '@/components/ui/BrandLogo.vue'

const route = useRoute()
const anns = useAnnouncementsStore()
const orgContext = useOrgContextStore()

const orgInitials = computed(() => {
  const name = orgContext.activeOrg?.name || ''
  return name.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase() || '?'
})

// Same destinations + glyphs as the mobile bottom bar (NavBar.vue), laid out vertically.
const items = [
  { name: 'home', paths: ['M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25'] },
  { name: 'scan', paths: ['M7 3.75h-1A2.25 2.25 0 003.75 6v1M17 3.75h1A2.25 2.25 0 0120.25 6v1M7 20.25h-1A2.25 2.25 0 013.75 18v-1M17 20.25h1A2.25 2.25 0 0020.25 18v-1', 'M3.75 12h16.5'] },
  { name: 'badges', paths: ['M16.5 18.75h-9m9 0a3 3 0 013 3h-15a3 3 0 013-3m9 0v-3.375c0-.621-.503-1.125-1.125-1.125h-.872M7.5 18.75v-3.375c0-.621.504-1.125 1.125-1.125h.872m5.007 0H9.497m5.007 0a7.454 7.454 0 01-.982-3.172M9.497 14.25a7.454 7.454 0 00.981-3.172M5.25 4.236c-.982.143-1.954.317-2.916.52A6.003 6.003 0 007.73 9.728M5.25 4.236V4.5c0 2.108.966 3.99 2.48 5.228M5.25 4.236V2.72a47.7 47.7 0 0113.5 0v1.516M7.73 9.728a6.726 6.726 0 002.748 1.35m8.272-6.842V4.5c0 2.108-.966 3.99-2.48 5.228m2.48-5.492a46.32 46.32 0 012.916.52 6.003 6.003 0 01-5.395 4.972m0 0a6.726 6.726 0 01-2.749 1.35m0 0a6.772 6.772 0 01-3.044 0'] },
  { name: 'events', paths: ['M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5'] },
  { name: 'profile', paths: ['M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z'] },
]

const isActive = (name) => route.name === name || (name === 'events' && route.name === 'event-detail')
</script>

<template>
  <aside
    class="sticky top-0 z-30 hidden h-dvh w-64 shrink-0 flex-col border-r border-base-300/40 bg-base-100/40 px-3 py-6 backdrop-blur lg:flex"
  >
    <!-- Org branding when active, Lyfter otherwise -->
    <RouterLink :to="{ name: 'home' }" class="mb-7 flex items-center gap-3 px-2 min-w-0">
      <template v-if="orgContext.activeOrg">
        <img
          v-if="orgContext.activeOrg.theme?.logo_url"
          :src="orgContext.activeOrg.theme.logo_url"
          :alt="orgContext.activeOrg.name"
          class="h-9 w-9 shrink-0 rounded-xl object-contain"
        />
        <span
          v-else
          class="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-primary/20 text-sm font-bold text-primary"
        >{{ orgInitials }}</span>
        <span class="truncate text-base font-bold leading-tight">{{ orgContext.activeOrg.name }}</span>
      </template>
      <template v-else>
        <BrandLogo :size="34" wordmark-class="text-xl" />
      </template>
    </RouterLink>

    <nav class="flex flex-1 flex-col gap-1.5">
      <RouterLink
        v-for="item in items"
        :key="item.name"
        :to="{ name: item.name }"
        class="tap-target relative flex items-center justify-start gap-3 rounded-2xl px-3 py-2.5 transition-colors"
        :class="isActive(item.name)
          ? 'bg-primary/10 text-primary'
          : 'text-base-content/60 hover:bg-base-100/60 hover:text-base-content'"
        :aria-current="isActive(item.name) ? 'page' : undefined"
      >
        <span class="relative">
          <svg
            class="h-6 w-6"
            :class="{ 'drop-shadow-[0_0_8px_rgba(45,212,191,0.55)]': isActive(item.name) }"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"
          >
            <path v-for="(d, i) in item.paths" :key="i" :d="d" />
          </svg>
          <span
            v-if="item.name === 'home' && anns.hasUnread"
            class="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full bg-error ring-2 ring-base-100"
            aria-hidden="true"
          />
        </span>
        <span class="text-sm font-medium">{{ $t('nav.' + item.name) }}</span>
      </RouterLink>

      <!-- Admin panel — only for super_admin -->
      <div v-if="orgContext.isSuperAdmin" class="mt-2 border-t border-base-300/30 pt-2">
        <RouterLink
          to="/admin/events"
          class="tap-target relative flex items-center justify-start gap-3 rounded-2xl px-3 py-2.5 transition-colors"
          :class="route.path.startsWith('/admin')
            ? 'bg-primary/10 text-primary'
            : 'text-base-content/60 hover:bg-base-100/60 hover:text-base-content'"
          :aria-current="route.path.startsWith('/admin') ? 'page' : undefined"
        >
          <svg class="h-6 w-6" :class="{ 'drop-shadow-[0_0_8px_rgba(45,212,191,0.55)]': route.path.startsWith('/admin') }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
          </svg>
          <span class="text-sm font-medium">{{ $t('nav.admin') }}</span>
        </RouterLink>
      </div>
    </nav>
  </aside>
</template>
