<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, readApiError } from '@/services/api'
import { useOrgContextStore } from '@/stores/orgContext'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'
import { t } from '@/i18n'

const route = useRoute()
const router = useRouter()
const orgContext = useOrgContextStore()

const invites = ref([])
const loading = ref(false)
const loaded = ref(false)
const error = ref('')
const accepting = ref(null)

const TYPE = {
  create_org: { key: 'invites.typeCreateOrg', cls: 'badge-primary' },
  org_join: { key: 'invites.typeOrgJoin', cls: 'badge-secondary' },
  event: { key: 'invites.typeEvent', cls: 'badge-accent' },
}
const typeMeta = (ty) => {
  const m = TYPE[ty]
  return m ? { label: t(m.key), cls: m.cls } : { label: ty, cls: 'badge-ghost' }
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get('/me/invites')
    invites.value = Array.isArray(data?.invites) ? data.invites : []
    loaded.value = true
  } catch (e) {
    error.value = readApiError(e, t('invites.couldNotLoad'))
  } finally {
    loading.value = false
  }
}

async function acceptToken(token, id = 'link') {
  accepting.value = id
  error.value = ''
  try {
    const { data } = await api.post('/invites/accept', { token })
    await orgContext.load()
    if (data.org?.id) orgContext.setActiveOrg(data.org.id)
    if (data.type === 'create_org') router.push('/org/settings')
    else if (data.type === 'org_join') router.push('/org/events')
    else await load()
  } catch (e) {
    error.value = readApiError(e, t('invites.couldNotAccept'))
  } finally {
    accepting.value = null
  }
}
const accept = (inv) => acceptToken(inv.token, inv.id)

onMounted(async () => {
  await load()
  // Deep link from an invite email: /invites?token=… → accept it automatically.
  // (Unauthenticated visitors are bounced through login first, then land back here.)
  const token = route.query.token
  if (token) {
    router.replace({ path: '/invites' }) // drop the token from the URL
    await acceptToken(String(token))
  }
})
</script>

<template>
  <div class="space-y-5 px-4 pb-10 pt-6">
    <header class="flex items-center gap-3">
      <button class="tap-target -ml-1 flex items-center gap-1 text-sm text-base-content/70" @click="router.push('/profile')">
        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 19l-7-7 7-7" /></svg>
      </button>
      <h1 class="text-2xl font-bold">{{ $t('invites.title') }}</h1>
    </header>

    <AlertMessage type="warning" :message="error" />
    <LoadingSpinner v-if="loading && !loaded" :label="$t('invites.loading')" />

    <template v-else>
      <section v-if="invites.length" class="space-y-3">
        <div v-for="inv in invites" :key="inv.id" class="surface flex items-center justify-between gap-3 p-4">
          <div class="min-w-0">
            <span class="badge badge-sm" :class="typeMeta(inv.type).cls">{{ typeMeta(inv.type).label }}</span>
            <p v-if="inv.org_name" class="mt-1 truncate text-sm font-medium">{{ inv.org_name }}</p>
            <p class="mt-0.5 truncate text-[0.7rem] text-base-content/45">{{ $t('invites.forEmail', { email: inv.email }) }}</p>
          </div>
          <button class="btn btn-primary btn-sm tap-target" :disabled="accepting === inv.id" @click="accept(inv)">
            <span v-if="accepting === inv.id" class="loading loading-spinner loading-xs" />
            {{ $t('invites.accept') }}
          </button>
        </div>
      </section>

      <div v-else class="surface p-8 text-center text-sm text-base-content/60">
        {{ $t('invites.empty') }}
      </div>
    </template>
  </div>
</template>
