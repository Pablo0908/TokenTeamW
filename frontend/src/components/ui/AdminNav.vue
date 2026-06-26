<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { t } from '@/i18n'

const route = useRoute()

const TABS = [
  { key: 'events',        to: '/admin/events',        label: () => t('tabs.events') },
  { key: 'users',         to: '/admin/users',         label: () => t('tabs.users') },
  { key: 'audit',         to: '/admin/audit',         label: () => t('tabs.audit') },
  { key: 'insights',      to: '/admin/insights',      label: () => t('tabs.insights') },
  { key: 'orgs',          to: '/admin/orgs',          label: () => t('tabs.orgs') },
  { key: 'org-invites',   to: '/admin/org-invites',   label: () => t('tabs.codes') },
  { key: 'announcements', to: '/admin/announcements', label: () => t('tabs.news') },
  { key: 'verifier',      to: '/admin/verifier',      label: () => t('tabs.verifier') },
]

const active = computed(() => route.path.split('/')[2] || 'events')
</script>

<template>
  <div role="tablist" class="tabs tabs-boxed bg-base-300/40 flex-nowrap overflow-x-auto">
    <RouterLink
      v-for="tab in TABS"
      :key="tab.key"
      :to="tab.to"
      role="tab"
      class="tab transition-all duration-200"
      :class="active === tab.key
        ? 'tab-active !bg-primary !text-primary-content shadow-sm'
        : 'text-base-content/60 hover:text-base-content'"
    >{{ tab.label() }}</RouterLink>
  </div>
</template>
