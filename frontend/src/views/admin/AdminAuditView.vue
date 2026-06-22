<script setup>
import { onMounted, ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api, readApiError } from '@/services/api'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'

const router = useRouter()
const auth = useAuthStore()

const entries = ref([])
const loading = ref(false)
const loaded = ref(false)
const error = ref('')

// Human-readable label + accent per audit action emitted by the backend.
const ACTIONS = {
  'event.create': { label: 'Event created', cls: 'badge-primary' },
  'badge.create': { label: 'Badge minted', cls: 'badge-secondary' },
  'badge.bulk_create': { label: 'Badges minted', cls: 'badge-secondary' },
  'user.role_change': { label: 'Role changed', cls: 'badge-accent' },
}

const actionMeta = (action) => ACTIONS[action] || { label: action, cls: 'badge-ghost' }

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return Number.isNaN(d.getTime()) ? ts : d.toLocaleString()
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get('/admin/audit')
    entries.value = Array.isArray(data?.entries) ? data.entries : []
    loaded.value = true
  } catch (e) {
    error.value = readApiError(e, 'Could not load the audit log.')
  } finally {
    loading.value = false
  }
}

function logout() {
  auth.logout()
  router.push('/login')
}

onMounted(load)
</script>

<template>
  <div class="space-y-5 px-4 pb-10 pt-6">
    <header class="flex items-center justify-between">
      <div>
        <p class="text-xs uppercase tracking-wide text-secondary">Organizer</p>
        <h1 class="text-2xl font-bold">Audit</h1>
      </div>
      <button class="btn btn-ghost btn-sm tap-target" @click="logout">Log out</button>
    </header>

    <!-- Admin section nav -->
    <div role="tablist" class="tabs tabs-boxed bg-base-300/40">
      <RouterLink to="/admin/events" role="tab" class="tab">Events</RouterLink>
      <RouterLink to="/admin/users" role="tab" class="tab">Users</RouterLink>
      <RouterLink to="/admin/audit" role="tab" class="tab tab-active">Audit</RouterLink>
    </div>

    <AlertMessage type="warning" :message="error" />
    <LoadingSpinner v-if="loading && !loaded" label="Loading audit log…" />

    <template v-else>
      <p class="text-xs text-base-content/55">
        Most recent activity across events, badges and roles (last 150 entries).
      </p>

      <section v-if="entries.length" class="space-y-3">
        <div v-for="(e, i) in entries" :key="i" class="surface p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0 flex-1">
              <span class="badge badge-sm" :class="actionMeta(e.action).cls">
                {{ actionMeta(e.action).label }}
              </span>
              <p v-if="e.detail" class="mt-2 truncate text-sm font-medium">{{ e.detail }}</p>
              <p class="mt-1 truncate text-[0.7rem] text-base-content/45">by {{ e.actor_id }}</p>
            </div>
            <time class="shrink-0 text-[0.7rem] text-base-content/55">{{ formatTime(e.ts) }}</time>
          </div>
        </div>
      </section>

      <div v-else class="surface p-8 text-center text-sm text-base-content/60">
        No activity recorded yet.
      </div>
    </template>
  </div>
</template>
