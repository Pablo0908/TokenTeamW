<script setup>
import { onMounted, ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { t } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import { api, readApiError } from '@/services/api'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'

const router = useRouter()
const auth = useAuthStore()

const orgs = ref([])
const loading = ref(false)
const loaded = ref(false)
const error = ref('')
const busy = ref('') // org id currently being toggled

function fmt(ts) { if (!ts) return ''; const d = new Date(ts); return Number.isNaN(d.getTime()) ? ts : d.toLocaleDateString() }

async function load() {
  loading.value = true; error.value = ''
  try {
    const { data } = await api.get('/admin/orgs')
    orgs.value = data.orgs || []
    loaded.value = true
  } catch (e) { error.value = readApiError(e, t('admin.orgs.couldNotLoad')) }
  finally { loading.value = false }
}

async function setStatus(org, status) {
  const verb = status === 'suspended' ? t('admin.orgs.suspend') : t('admin.orgs.reactivate')
  const detail = status === 'suspended' ? t('admin.orgs.suspendDetail') : t('admin.orgs.reactivateDetail')
  if (!window.confirm(t('admin.orgs.confirm', { verb, name: org.name, detail }))) return
  busy.value = org.id; error.value = ''
  try {
    await api.patch(`/admin/orgs/${org.id}/status`, { status })
    org.status = status
  } catch (e) { error.value = readApiError(e, t('admin.orgs.couldNotUpdate')) }
  finally { busy.value = '' }
}

function logout() { auth.logout(); router.push('/login') }
onMounted(load)
</script>

<template>
  <div class="space-y-5 px-4 pb-10 pt-6">
    <header class="flex items-center justify-between">
      <div>
        <p class="text-xs uppercase tracking-wide text-secondary">{{ $t('admin.platform') }}</p>
        <h1 class="text-2xl font-bold">{{ $t('admin.orgs.title') }}</h1>
      </div>
      <button class="btn btn-ghost btn-sm tap-target" @click="logout">{{ $t('admin.logout') }}</button>
    </header>

    <div role="tablist" class="tabs tabs-boxed bg-base-300/40">
      <RouterLink to="/admin/events" role="tab" class="tab">{{ $t('tabs.events') }}</RouterLink>
      <RouterLink to="/admin/users" role="tab" class="tab">{{ $t('tabs.users') }}</RouterLink>
      <RouterLink to="/admin/audit" role="tab" class="tab">{{ $t('tabs.audit') }}</RouterLink>
      <RouterLink to="/admin/insights" role="tab" class="tab">{{ $t('tabs.insights') }}</RouterLink>
      <RouterLink to="/admin/orgs" role="tab" class="tab tab-active">{{ $t('tabs.orgs') }}</RouterLink>
      <RouterLink to="/admin/org-invites" role="tab" class="tab">{{ $t('tabs.codes') }}</RouterLink>
      <RouterLink to="/admin/announcements" role="tab" class="tab">{{ $t('tabs.news') }}</RouterLink>
    </div>

    <p class="text-xs text-base-content/55">
      {{ $t('admin.orgs.helper') }}
    </p>

    <AlertMessage type="warning" :message="error" />
    <LoadingSpinner v-if="loading && !loaded" :label="$t('admin.loading')" />

    <section v-else-if="orgs.length" class="space-y-2">
      <div v-for="o in orgs" :key="o.id" class="surface flex items-center justify-between gap-2 p-3">
        <div class="min-w-0">
          <p class="truncate text-sm font-medium">
            {{ o.name }}
            <span class="badge badge-sm" :class="o.status === 'suspended' ? 'badge-error' : 'badge-success'">{{ o.status === 'suspended' ? $t('admin.orgs.statusSuspended') : $t('admin.orgs.statusActive') }}</span>
          </p>
          <p class="truncate text-[0.7rem] text-base-content/45">
            {{ o.owner_email || $t('admin.orgs.noOwner') }} · {{ $t('admin.orgs.membersEvents', { members: o.members_count, events: o.events_count }) }}
          </p>
        </div>
        <button
          class="btn btn-xs"
          :class="o.status === 'suspended' ? 'btn-success' : 'btn-ghost text-error'"
          :disabled="busy === o.id"
          @click="setStatus(o, o.status === 'suspended' ? 'active' : 'suspended')"
        >
          <span v-if="busy === o.id" class="loading loading-spinner loading-xs" />
          {{ o.status === 'suspended' ? $t('admin.orgs.reactivate') : $t('admin.orgs.suspend') }}
        </button>
      </div>
    </section>
    <div v-else-if="loaded" class="surface p-8 text-center text-sm text-base-content/60">{{ $t('admin.orgs.noneYet') }}</div>
  </div>
</template>
