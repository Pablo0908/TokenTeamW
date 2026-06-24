<script setup>
import { onMounted, ref, watch, onBeforeUnmount } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { t } from '@/i18n'
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

// Accent per audit action emitted by the backend. Labels are translated via i18n.
const ACTION_CLS = {
  'event.create': 'badge-primary',
  'event.start': 'badge-success',
  'event.stop': 'badge-ghost',
  'event.pause': 'badge-warning',
  'event.unpause': 'badge-ghost',
  'event.end': 'badge-error',
  'event.reopen': 'badge-info',
  'badge.create': 'badge-secondary',
  'badge.bulk_create': 'badge-secondary',
  'badge.redeem': 'badge-success',
  'auth.login': 'badge-ghost',
  'auth.signup': 'badge-info',
  'user.role_change': 'badge-accent',
  'user.disable': 'badge-warning',
  'user.enable': 'badge-ghost',
  'user.delete': 'badge-error',
  'announcement.create': 'badge-info',
  'announcement.update': 'badge-ghost',
  'announcement.delete': 'badge-error',
}

const actionMeta = (action) => {
  const cls = ACTION_CLS[action] || 'badge-ghost'
  // Action keys contain dots; i18n keys use underscores to avoid path-splitting.
  const label = ACTION_CLS[action] ? t(`admin.audit.actions.${action.replace(/\./g, '_')}`) : action
  return { label, cls }
}

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
    error.value = readApiError(e, t('admin.audit.couldNotLoad'))
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
        <p class="text-xs uppercase tracking-wide text-secondary">{{ $t('admin.organizer') }}</p>
        <h1 class="text-2xl font-bold">{{ $t('admin.audit.title') }}</h1>
      </div>
      <button class="btn btn-ghost btn-sm tap-target" @click="logout">{{ $t('admin.logout') }}</button>
    </header>

    <!-- Admin section nav -->
    <div role="tablist" class="tabs tabs-boxed bg-base-300/40">
      <RouterLink to="/admin/events" role="tab" class="tab">{{ $t('tabs.events') }}</RouterLink>
      <RouterLink to="/admin/users" role="tab" class="tab">{{ $t('tabs.users') }}</RouterLink>
      <RouterLink to="/admin/audit" role="tab" class="tab tab-active">{{ $t('tabs.audit') }}</RouterLink>
      <RouterLink to="/admin/insights" role="tab" class="tab">{{ $t('tabs.insights') }}</RouterLink>
      <RouterLink to="/admin/orgs" role="tab" class="tab">{{ $t('tabs.orgs') }}</RouterLink>
      <RouterLink to="/admin/org-invites" role="tab" class="tab">{{ $t('tabs.codes') }}</RouterLink>
      <RouterLink to="/admin/announcements" role="tab" class="tab">{{ $t('tabs.news') }}</RouterLink>
    </div>

    <!-- Search by user (email/name) or event (name) -->
    <label class="form-control w-full">
      <input
        v-model="search"
        type="search"
        inputmode="search"
        :placeholder="$t('admin.audit.searchPlaceholder')"
        class="input input-bordered input-sm w-full bg-base-100/70"
      />
    </label>

    <AlertMessage type="warning" :message="error" />
    <LoadingSpinner v-if="loading && !loaded" :label="$t('admin.audit.loading')" />

    <template v-else>
      <p class="text-xs text-base-content/55">
        {{ $t('admin.audit.summary', { n: pageSize }) }}
      </p>

      <section v-if="entries.length" class="space-y-3">
        <div v-for="(e, i) in entries" :key="i" class="surface p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0 flex-1">
              <span class="badge badge-sm" :class="actionMeta(e.action).cls">
                {{ actionMeta(e.action).label }}
              </span>
              <p v-if="e.detail" class="mt-2 truncate text-sm font-medium">{{ e.detail }}</p>
              <p class="mt-1 truncate text-[0.7rem] text-base-content/45">{{ $t('admin.audit.by', { actor: e.actor_email || e.actor_id }) }}</p>
            </div>
            <time class="shrink-0 text-[0.7rem] text-base-content/55">{{ formatTime(e.ts) }}</time>
          </div>
        </div>
      </section>

      <div v-else class="surface p-8 text-center text-sm text-base-content/60">
        {{ search.trim() ? $t('admin.audit.noMatch') : $t('admin.audit.noneYet') }}
      </div>

      <!-- Pager: arrows disabled at the ends -->
      <div v-if="entries.length || page > 1" class="flex items-center justify-center gap-5 pt-1">
        <button
          class="btn btn-circle btn-sm btn-ghost tap-target"
          :disabled="page <= 1 || loading"
          :aria-label="$t('admin.audit.prevPage')"
          @click="prevPage"
        >
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 19l-7-7 7-7" /></svg>
        </button>
        <span class="text-xs text-base-content/55">{{ $t('admin.audit.page') }} {{ page }}<span v-if="total"> · {{ $t('admin.audit.total', { n: total }) }}</span></span>
        <button
          class="btn btn-circle btn-sm btn-ghost tap-target"
          :disabled="!hasMore || loading"
          :aria-label="$t('admin.audit.nextPage')"
          @click="nextPage"
        >
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7" /></svg>
        </button>
      </div>
    </template>
  </div>
</template>
