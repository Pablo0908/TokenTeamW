<script setup>
import { onMounted, ref, watch, onBeforeUnmount } from 'vue'
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

const search = ref('')
const page = ref(1)
const pageSize = ref(50)
const total = ref(0)
const hasMore = ref(false)

// Human-readable label + accent per audit action emitted by the backend.
const ACTIONS = {
  'event.create': { label: 'Event created', cls: 'badge-primary' },
  'event.start': { label: 'Event started', cls: 'badge-success' },
  'event.stop': { label: 'Event stopped', cls: 'badge-ghost' },
  'event.pause': { label: 'Event locked', cls: 'badge-warning' },
  'event.unpause': { label: 'Event unlocked', cls: 'badge-ghost' },
  'event.end': { label: 'Event ended', cls: 'badge-error' },
  'event.reopen': { label: 'Event reopened', cls: 'badge-info' },
  'badge.create': { label: 'Badge minted', cls: 'badge-secondary' },
  'badge.bulk_create': { label: 'Badges minted', cls: 'badge-secondary' },
  'badge.redeem': { label: 'Badge scanned', cls: 'badge-success' },
  'auth.login': { label: 'Signed in', cls: 'badge-ghost' },
  'auth.signup': { label: 'Signed up', cls: 'badge-info' },
  'user.role_change': { label: 'Role changed', cls: 'badge-accent' },
  'user.disable': { label: 'User disabled', cls: 'badge-warning' },
  'user.enable': { label: 'User enabled', cls: 'badge-ghost' },
  'user.delete': { label: 'User deleted', cls: 'badge-error' },
  'announcement.create': { label: 'Announcement posted', cls: 'badge-info' },
  'announcement.update': { label: 'Announcement edited', cls: 'badge-ghost' },
  'announcement.delete': { label: 'Announcement deleted', cls: 'badge-error' },
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
    const { data } = await api.get('/admin/audit', {
      params: { page: page.value, q: search.value.trim() || undefined },
    })
    entries.value = Array.isArray(data?.entries) ? data.entries : []
    total.value = data?.total ?? entries.value.length
    pageSize.value = data?.page_size ?? 50
    hasMore.value = !!data?.has_more
    loaded.value = true
  } catch (e) {
    error.value = readApiError(e, 'Could not load the audit log.')
  } finally {
    loading.value = false
  }
}

// Debounced search: a new term always resets to page 1.
let debounce
watch(search, () => {
  clearTimeout(debounce)
  debounce = setTimeout(() => {
    page.value = 1
    load()
  }, 300)
})
onBeforeUnmount(() => clearTimeout(debounce))

function prevPage() {
  if (page.value > 1 && !loading.value) {
    page.value -= 1
    load()
  }
}
function nextPage() {
  if (hasMore.value && !loading.value) {
    page.value += 1
    load()
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
      <RouterLink to="/admin/insights" role="tab" class="tab">Insights</RouterLink>
      <RouterLink to="/admin/orgs" role="tab" class="tab">Orgs</RouterLink>
      <RouterLink to="/admin/org-invites" role="tab" class="tab">Codes</RouterLink>
      <RouterLink to="/admin/announcements" role="tab" class="tab">News</RouterLink>
    </div>

    <!-- Search by user (email/name) or event (name) -->
    <label class="form-control w-full">
      <input
        v-model="search"
        type="search"
        inputmode="search"
        placeholder="Search by user or event…"
        class="input input-bordered input-sm w-full bg-base-100/70"
      />
    </label>

    <AlertMessage type="warning" :message="error" />
    <LoadingSpinner v-if="loading && !loaded" label="Loading audit log…" />

    <template v-else>
      <p class="text-xs text-base-content/55">
        Activity across events, badges, scans, logins and roles · {{ pageSize }} per page.
      </p>

      <section v-if="entries.length" class="space-y-3">
        <div v-for="(e, i) in entries" :key="i" class="surface p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0 flex-1">
              <span class="badge badge-sm" :class="actionMeta(e.action).cls">
                {{ actionMeta(e.action).label }}
              </span>
              <p v-if="e.detail" class="mt-2 truncate text-sm font-medium">{{ e.detail }}</p>
              <p class="mt-1 truncate text-[0.7rem] text-base-content/45">by {{ e.actor_email || e.actor_id }}</p>
            </div>
            <time class="shrink-0 text-[0.7rem] text-base-content/55">{{ formatTime(e.ts) }}</time>
          </div>
        </div>
      </section>

      <div v-else class="surface p-8 text-center text-sm text-base-content/60">
        {{ search.trim() ? 'No activity matches your search.' : 'No activity recorded yet.' }}
      </div>

      <!-- Pager: arrows disabled at the ends -->
      <div v-if="entries.length || page > 1" class="flex items-center justify-center gap-5 pt-1">
        <button
          class="btn btn-circle btn-sm btn-ghost tap-target"
          :disabled="page <= 1 || loading"
          aria-label="Previous page"
          @click="prevPage"
        >
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 19l-7-7 7-7" /></svg>
        </button>
        <span class="text-xs text-base-content/55">Page {{ page }}<span v-if="total"> · {{ total }} total</span></span>
        <button
          class="btn btn-circle btn-sm btn-ghost tap-target"
          :disabled="!hasMore || loading"
          aria-label="Next page"
          @click="nextPage"
        >
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7" /></svg>
        </button>
      </div>
    </template>
  </div>
</template>
