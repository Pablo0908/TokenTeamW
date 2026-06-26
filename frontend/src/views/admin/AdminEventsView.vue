<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useEventsStore } from '@/stores/events'
import EventCard from '@/components/domain/EventCard.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'

const router = useRouter()
const auth = useAuthStore()
const events = useEventsStore()

onMounted(() => events.fetchEvents())

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="space-y-5 px-4 pb-10 pt-6">
    <header class="flex items-center justify-between">
      <div>
        <p class="text-xs uppercase tracking-wide text-secondary">{{ $t('roles.superAdmin') }}</p>
        <h1 class="text-2xl font-bold">{{ $t('admin.eventsTitle') }}</h1>
      </div>
      <button class="btn btn-ghost btn-sm tap-target" @click="logout">{{ $t('common.logout') }}</button>
    </header>

    <!-- Admin section nav -->
    <div role="tablist" class="tabs tabs-boxed bg-base-300/40">
      <RouterLink to="/admin/events" role="tab" class="tab tab-active">{{ $t('tabs.events') }}</RouterLink>
      <RouterLink to="/admin/users" role="tab" class="tab">{{ $t('tabs.users') }}</RouterLink>
      <RouterLink to="/admin/audit" role="tab" class="tab">{{ $t('tabs.audit') }}</RouterLink>
      <RouterLink to="/admin/insights" role="tab" class="tab">{{ $t('tabs.insights') }}</RouterLink>
      <RouterLink to="/admin/orgs" role="tab" class="tab">{{ $t('tabs.orgs') }}</RouterLink>
      <RouterLink to="/admin/org-invites" role="tab" class="tab">{{ $t('tabs.codes') }}</RouterLink>
      <RouterLink to="/admin/announcements" role="tab" class="tab">{{ $t('tabs.news') }}</RouterLink>
      <RouterLink to="/admin/verifier" role="tab" class="tab">{{ $t('tabs.verifier') }}</RouterLink>
    </div>

    <RouterLink to="/admin/events/new" class="btn btn-primary w-full tap-target">
      <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <path d="M12 5v14M5 12h14" />
      </svg>
      {{ $t('admin.newEvent') }}
    </RouterLink>

    <AlertMessage type="warning" :message="events.error || ''" />
    <LoadingSpinner v-if="events.loading && !events.loaded" :label="$t('admin.loadingEvents')" />

    <div v-else-if="events.events.length" class="space-y-3">
      <EventCard
        v-for="ev in events.events"
        :key="ev.id"
        :event="ev"
        @select="router.push(`/admin/events/${ev.id}`)"
      />
    </div>

    <div v-else class="surface p-8 text-center text-sm text-base-content/60">
      {{ $t('admin.noEventsAdmin') }}
    </div>
  </div>
</template>
