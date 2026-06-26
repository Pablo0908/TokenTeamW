<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AdminNav from '@/components/ui/AdminNav.vue'

// Shared shell for every super-admin tab. Mounting AdminNav here (once) instead of inside
// each page keeps the same nav element alive across tab navigations — so its active pill
// can transition (the "azulita" slide) exactly like the org panel, whose single
// OrgPanelView component likewise persists its tabs. Per-page title/eyebrow come from route meta.
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const eyebrow = computed(() => route.meta.eyebrow || 'roles.superAdmin')
const title = computed(() => route.meta.title || '')

function logout() {
  auth.logout()
  router.push('/welcome')
}
</script>

<template>
  <div class="space-y-5 px-4 lg:px-6 pb-10 pt-6">
    <header class="flex items-center justify-between">
      <div>
        <p class="text-xs uppercase tracking-wide text-secondary">{{ $t(eyebrow) }}</p>
        <h1 class="text-2xl font-bold">{{ $t(title) }}</h1>
      </div>
      <button class="btn btn-ghost btn-sm tap-target" @click="logout">{{ $t('admin.logout') }}</button>
    </header>

    <AdminNav />

    <router-view />
  </div>
</template>
