<script setup>
import { onMounted, ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
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
  } catch (e) { error.value = readApiError(e, 'Could not load organizations.') }
  finally { loading.value = false }
}

async function setStatus(org, status) {
  const verb = status === 'suspended' ? 'Suspend' : 'Reactivate'
  if (!window.confirm(`${verb} "${org.name}"? ${status === 'suspended' ? 'Its scans and event creation will be paused.' : 'It will be active again.'}`)) return
  busy.value = org.id; error.value = ''
  try {
    await api.patch(`/admin/orgs/${org.id}/status`, { status })
    org.status = status
  } catch (e) { error.value = readApiError(e, 'Could not update the organization.') }
  finally { busy.value = '' }
}

function logout() { auth.logout(); router.push('/login') }
onMounted(load)
</script>

<template>
  <div class="space-y-5 px-4 pb-10 pt-6">
    <header class="flex items-center justify-between">
      <div>
        <p class="text-xs uppercase tracking-wide text-secondary">Platform</p>
        <h1 class="text-2xl font-bold">Organizations</h1>
      </div>
      <button class="btn btn-ghost btn-sm tap-target" @click="logout">Log out</button>
    </header>

    <div role="tablist" class="tabs tabs-boxed bg-base-300/40">
      <RouterLink to="/admin/events" role="tab" class="tab">Events</RouterLink>
      <RouterLink to="/admin/users" role="tab" class="tab">Users</RouterLink>
      <RouterLink to="/admin/audit" role="tab" class="tab">Audit</RouterLink>
      <RouterLink to="/admin/orgs" role="tab" class="tab tab-active">Orgs</RouterLink>
      <RouterLink to="/admin/org-invites" role="tab" class="tab">Codes</RouterLink>
      <RouterLink to="/admin/announcements" role="tab" class="tab">News</RouterLink>
    </div>

    <p class="text-xs text-base-content/55">
      Every tenant on the platform. Suspending an org freezes its scans and event creation;
      it never affects member or attendee accounts.
    </p>

    <AlertMessage type="warning" :message="error" />
    <LoadingSpinner v-if="loading && !loaded" label="Loading…" />

    <section v-else-if="orgs.length" class="space-y-2">
      <div v-for="o in orgs" :key="o.id" class="surface flex items-center justify-between gap-2 p-3">
        <div class="min-w-0">
          <p class="truncate text-sm font-medium">
            {{ o.name }}
            <span class="badge badge-sm" :class="o.status === 'suspended' ? 'badge-error' : 'badge-success'">{{ o.status }}</span>
          </p>
          <p class="truncate text-[0.7rem] text-base-content/45">
            {{ o.owner_email || 'no owner' }} · {{ o.members_count }} members · {{ o.events_count }} events
          </p>
        </div>
        <button
          class="btn btn-xs"
          :class="o.status === 'suspended' ? 'btn-success' : 'btn-ghost text-error'"
          :disabled="busy === o.id"
          @click="setStatus(o, o.status === 'suspended' ? 'active' : 'suspended')"
        >
          <span v-if="busy === o.id" class="loading loading-spinner loading-xs" />
          {{ o.status === 'suspended' ? 'Reactivate' : 'Suspend' }}
        </button>
      </div>
    </section>
    <div v-else-if="loaded" class="surface p-8 text-center text-sm text-base-content/60">No organizations yet.</div>
  </div>
</template>
