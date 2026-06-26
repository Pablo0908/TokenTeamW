<script setup>
import { onMounted, ref } from 'vue'
import { api, readApiError } from '@/services/api'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'
import { t } from '@/i18n'

const invites = ref([])
const loading = ref(false)
const loaded = ref(false)
const error = ref('')
const email = ref('')
const creating = ref(false)

const STATUS = { pending: 'badge-warning', accepted: 'badge-success', revoked: 'badge-ghost' }
const STATUS_KEY = { pending: 'statusPending', accepted: 'statusAccepted', revoked: 'statusRevoked' }
const statusLabel = (s) => (STATUS_KEY[s] ? t(`admin.codes.${STATUS_KEY[s]}`) : s)

function fmt(ts) { if (!ts) return ''; const d = new Date(ts); return Number.isNaN(d.getTime()) ? ts : d.toLocaleDateString() }

async function load() {
  loading.value = true; error.value = ''
  try {
    const { data } = await api.get('/admin/org-invites')
    invites.value = data.invites || []
    loaded.value = true
  } catch (e) { error.value = readApiError(e, t('admin.codes.couldNotLoad')) }
  finally { loading.value = false }
}

async function create() {
  const e = email.value.trim()
  if (!e) return
  creating.value = true; error.value = ''
  try { await api.post('/admin/org-invites', { email: e }); email.value = ''; await load() }
  catch (err) { error.value = readApiError(err, t('admin.codes.couldNotCreate')) }
  finally { creating.value = false }
}

async function revoke(id) {
  try { await api.post(`/admin/org-invites/${id}/revoke`); await load() }
  catch (e) { error.value = readApiError(e, t('admin.codes.couldNotRevoke')) }
}

onMounted(load)
</script>

<template>
  <div class="space-y-5">
    <p class="text-xs text-base-content/55">
      {{ $t('admin.codes.helper') }}
    </p>

    <div class="surface flex gap-2 p-4 mx-auto w-full max-w-2xl">
      <input v-model="email" type="email" :placeholder="$t('admin.codes.emailPlaceholder')" class="input input-bordered input-sm flex-1 bg-base-100/70" @keyup.enter="create" />
      <button class="btn btn-primary btn-sm" :disabled="creating" @click="create">
        <span v-if="creating" class="loading loading-spinner loading-xs" />
        {{ $t('admin.codes.invite') }}
      </button>
    </div>

    <AlertMessage type="warning" :message="error" />
    <LoadingSpinner v-if="loading && !loaded" :label="$t('admin.loading')" />

    <section v-else-if="invites.length" class="grid grid-cols-1 gap-2 lg:grid-cols-2 lg:gap-3 xl:grid-cols-3">
      <div v-for="inv in invites" :key="inv.id" class="surface flex items-center justify-between gap-2 p-3">
        <div class="min-w-0">
          <p class="truncate text-sm font-medium">{{ inv.email }}</p>
          <p class="text-[0.7rem] text-base-content/45">{{ $t('admin.codes.expires', { date: fmt(inv.expires_at) }) }}</p>
        </div>
        <div class="flex items-center gap-2">
          <span class="badge badge-sm capitalize" :class="STATUS[inv.status] || 'badge-ghost'">{{ statusLabel(inv.status) }}</span>
          <button v-if="inv.status === 'pending'" class="btn btn-ghost btn-xs text-error" @click="revoke(inv.id)">{{ $t('admin.codes.revoke') }}</button>
        </div>
      </div>
    </section>
    <div v-else-if="loaded" class="surface p-8 text-center text-sm text-base-content/60">{{ $t('admin.codes.noneYet') }}</div>
  </div>
</template>
