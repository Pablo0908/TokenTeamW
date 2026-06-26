<script setup>
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import VerifierPanel from '@/components/domain/VerifierPanel.vue'

// Platform-wide prize verifier. The VerifierPanel is org-agnostic — the backend resolves the
// org from the scanned token; a super_admin may award any org's event.
const router = useRouter()
const auth = useAuthStore()

function logout() { auth.logout(); router.push('/login') }
</script>

<template>
  <div class="space-y-5 px-4 lg:px-6 pb-10 pt-6">
    <header class="flex items-center justify-between">
      <div>
        <p class="text-xs uppercase tracking-wide text-secondary">{{ $t('admin.platform') }}</p>
        <h1 class="text-2xl font-bold">{{ $t('verifier.title') }}</h1>
      </div>
      <button class="btn btn-ghost btn-sm tap-target" @click="logout">{{ $t('admin.logout') }}</button>
    </header>

    <div role="tablist" class="tabs tabs-boxed bg-base-300/40 flex-nowrap overflow-x-auto">
      <RouterLink to="/admin/events" role="tab" class="tab">{{ $t('tabs.events') }}</RouterLink>
      <RouterLink to="/admin/users" role="tab" class="tab">{{ $t('tabs.users') }}</RouterLink>
      <RouterLink to="/admin/audit" role="tab" class="tab">{{ $t('tabs.audit') }}</RouterLink>
      <RouterLink to="/admin/insights" role="tab" class="tab">{{ $t('tabs.insights') }}</RouterLink>
      <RouterLink to="/admin/orgs" role="tab" class="tab">{{ $t('tabs.orgs') }}</RouterLink>
      <RouterLink to="/admin/org-invites" role="tab" class="tab">{{ $t('tabs.codes') }}</RouterLink>
      <RouterLink to="/admin/announcements" role="tab" class="tab">{{ $t('tabs.news') }}</RouterLink>
      <RouterLink to="/admin/verifier" role="tab" class="tab tab-active">{{ $t('tabs.verifier') }}</RouterLink>
    </div>

    <div class="surface p-4">
      <VerifierPanel />
    </div>
  </div>
</template>
