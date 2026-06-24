<script setup>
import { onMounted, ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api, readApiError } from '@/services/api'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'

const router = useRouter()
const auth = useAuthStore()

const invites = ref([])
const loading = ref(false)
const loaded = ref(false)
const error = ref('')
const email = ref('')
const creating = ref(false)

const STATUS = { pending: 'badge-warning', accepted: 'badge-success', revoked: 'badge-ghost' }

function fmt(ts) { if (!ts) return ''; const d = new Date(ts); return Number.isNaN(d.getTime()) ? ts : d.toLocaleDateString() }

async function load() {
  loading.value = true; error.value = ''
  try {
    const { data } = await api.get('/admin/org-invites')
    invites.value = data.invites || []
    loaded.value = true
  } catch (e) { error.value = readApiError(e, 'Could not load org-creation invites.') }
  finally { loading.value = false }
}

async function create() {
  const e = email.value.trim()
  if (!e) return
  creating.value = true; error.value = ''
  try { await api.post('/admin/org-invites', { email: e }); email.value = ''; await load() }
  catch (err) { error.value = readApiError(err, 'Could not create the invite.') }
  finally { creating.value = false }
}

async function revoke(id) {
  try { await api.post(`/admin/org-invites/${id}/revoke`); await load() }
  catch (e) { error.value = readApiError(e, 'Could not revoke the invite.') }
}

function logout() { auth.logout(); router.push('/login') }
onMounted(load)
</script>

<template>
  <div class="space-y-5 px-4 pb-10 pt-6">
    <header class="flex items-center justify-between">
      <div>
        <p class="text-xs uppercase tracking-wide text-secondary">Platform</p>
        <h1 class="text-2xl font-bold">Org invites</h1>
      </div>
      <button class="btn btn-ghost btn-sm tap-target" @click="logout">Log out</button>
    </header>

    <div role="tablist" class="tabs tabs-boxed bg-base-300/40">
      <RouterLink to="/admin/events" role="tab" class="tab">Events</RouterLink>
      <RouterLink to="/admin/users" role="tab" class="tab">Users</RouterLink>
      <RouterLink to="/admin/audit" role="tab" class="tab">Audit</RouterLink>
      <RouterLink to="/admin/insights" role="tab" class="tab">Insights</RouterLink>
      <RouterLink to="/admin/orgs" role="tab" class="tab">Orgs</RouterLink>
      <RouterLink to="/admin/org-invites" role="tab" class="tab tab-active">Codes</RouterLink>
      <RouterLink to="/admin/announcements" role="tab" class="tab">News</RouterLink>
    </div>

    <p class="text-xs text-base-content/55">
      Invite someone to create their own organization. They accept it in-app (Profile → Invitations)
      and become its owner.
    </p>

    <div class="surface flex gap-2 p-4">
      <input v-model="email" type="email" placeholder="person@email.com" class="input input-bordered input-sm flex-1 bg-base-100/70" @keyup.enter="create" />
      <button class="btn btn-primary btn-sm" :disabled="creating" @click="create">
        <span v-if="creating" class="loading loading-spinner loading-xs" />
        Invite
      </button>
    </div>

    <AlertMessage type="warning" :message="error" />
    <LoadingSpinner v-if="loading && !loaded" label="Loading…" />

    <section v-else-if="invites.length" class="space-y-2">
      <div v-for="inv in invites" :key="inv.id" class="surface flex items-center justify-between gap-2 p-3">
        <div class="min-w-0">
          <p class="truncate text-sm font-medium">{{ inv.email }}</p>
          <p class="text-[0.7rem] text-base-content/45">expires {{ fmt(inv.expires_at) }}</p>
        </div>
        <div class="flex items-center gap-2">
          <span class="badge badge-sm capitalize" :class="STATUS[inv.status] || 'badge-ghost'">{{ inv.status }}</span>
          <button v-if="inv.status === 'pending'" class="btn btn-ghost btn-xs text-error" @click="revoke(inv.id)">revoke</button>
        </div>
      </div>
    </section>
    <div v-else-if="loaded" class="surface p-8 text-center text-sm text-base-content/60">No org-creation invites yet.</div>
  </div>
</template>
