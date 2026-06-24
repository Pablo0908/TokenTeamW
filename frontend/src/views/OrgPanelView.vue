<script setup>
import { computed, ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, readApiError } from '@/services/api'
import { useOrgContextStore } from '@/stores/orgContext'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'
import StatTile from '@/components/domain/StatTile.vue'
import ActivityChart from '@/components/domain/ActivityChart.vue'
import OrgOnboarding from '@/components/domain/OrgOnboarding.vue'

const route = useRoute()
const router = useRouter()
const orgContext = useOrgContextStore()

const orgId = computed(() => orgContext.activeOrgId)
const activeOrg = computed(() => orgContext.activeOrg)
const isOwner = computed(() => orgContext.isActiveOwner)
const isAdmin = computed(() => orgContext.isActiveAdmin) // owner or admin

const TABS = computed(() => [
  { key: 'dashboard', label: 'Dashboard', show: true },
  { key: 'events', label: 'Events', show: true },
  { key: 'members', label: 'Members', show: isAdmin.value },
  { key: 'participants', label: 'People', show: true },
  { key: 'audit', label: 'Audit', show: isAdmin.value },
  { key: 'settings', label: 'Settings', show: isOwner.value },
])
const tab = computed(() => {
  const t = route.params.tab || 'dashboard'
  return TABS.value.some((x) => x.key === t && x.show) ? t : 'dashboard'
})
function go(t) { router.push(`/org/${t}`) }

const loading = ref(false)
const error = ref('')

// section data
const dashboard = ref(null)
const dashPeriod = ref('day')
const DASH_PERIODS = ['day', 'week', 'month']
const events = ref([])
const members = ref([])
const invites = ref([])
const participants = ref([])
const audit = ref({ entries: [], page: 1, has_more: false, total: 0 })
const settings = ref({ name: '', description: '' })

const newEvent = ref({ name: '', event_type: 'conference' })
const showNewEvent = ref(false)
const inviteEmail = ref('')
const EVENT_TYPES = ['conference', 'workshop', 'meetup', 'hackathon', 'networking', 'other']

function fmtTime(ts) { const d = new Date(ts); return Number.isNaN(d.getTime()) ? ts : d.toLocaleString() }

async function loadTab() {
  if (!orgId.value) return
  loading.value = true; error.value = ''
  try {
    const base = `/orgs/${orgId.value}`
    if (tab.value === 'dashboard') dashboard.value = (await api.get(`${base}/dashboard`, { params: { period: dashPeriod.value } })).data
    else if (tab.value === 'events') events.value = (await api.get(`${base}/events`)).data || []
    else if (tab.value === 'members') {
      members.value = (await api.get(`${base}/members`)).data.members || []
      invites.value = (await api.get(`${base}/invites`)).data.invites || []
    } else if (tab.value === 'participants') participants.value = (await api.get(`${base}/participants`)).data.participants || []
    else if (tab.value === 'audit') audit.value = (await api.get(`${base}/audit`, { params: { page: audit.value.page } })).data
    else if (tab.value === 'settings') {
      const o = (await api.get(base)).data
      settings.value = { name: o.name || '', description: o.description || '' }
    }
  } catch (e) { error.value = readApiError(e, 'Could not load this section.') }
  finally { loading.value = false }
}

async function createEvent() {
  if (!newEvent.value.name.trim()) return
  try {
    await api.post(`/orgs/${orgId.value}/event`, { ...newEvent.value, name: newEvent.value.name.trim() })
    showNewEvent.value = false; newEvent.value = { name: '', event_type: 'conference' }
    await loadTab()
  } catch (e) { error.value = readApiError(e, 'Could not create the event.') }
}
async function sendInvite() {
  const email = inviteEmail.value.trim()
  if (!email) return
  try { await api.post(`/orgs/${orgId.value}/invites`, { email }); inviteEmail.value = ''; await loadTab() }
  catch (e) { error.value = readApiError(e, 'Could not send the invite.') }
}
async function revokeInvite(id) {
  try { await api.post(`/orgs/${orgId.value}/invites/${id}/revoke`); await loadTab() }
  catch (e) { error.value = readApiError(e, 'Could not revoke the invite.') }
}
async function setRole(uid, role) {
  try { await api.patch(`/orgs/${orgId.value}/members/${uid}`, { role }); await loadTab() }
  catch (e) { error.value = readApiError(e, 'Could not change the role.') }
}
async function removeMember(uid) {
  try { await api.delete(`/orgs/${orgId.value}/members/${uid}`); await loadTab() }
  catch (e) { error.value = readApiError(e, 'Could not remove the member.') }
}
async function banParticipant(uid, banned) {
  try {
    if (banned) await api.delete(`/orgs/${orgId.value}/participants/${uid}/ban`)
    else await api.post(`/orgs/${orgId.value}/participants/${uid}/ban`)
    await loadTab()
  } catch (e) { error.value = readApiError(e, 'Could not update the ban.') }
}
async function saveSettings() {
  try {
    await api.patch(`/orgs/${orgId.value}`, { name: settings.value.name.trim(), description: settings.value.description })
    await orgContext.load()
  } catch (e) { error.value = readApiError(e, 'Could not save settings.') }
}
function setDashPeriod(p) {
  if (p === dashPeriod.value) return
  dashPeriod.value = p
  loadTab()
}
function auditPage(delta) {
  const next = audit.value.page + delta
  if (next < 1 || (delta > 0 && !audit.value.has_more)) return
  audit.value.page = next; loadTab()
}

watch([orgId, tab], loadTab)
onMounted(loadTab)
</script>

<template>
  <div class="space-y-5 px-4 pb-10 pt-6">
    <header>
      <p class="text-xs uppercase tracking-wide text-secondary">Organization</p>
      <div class="flex items-center gap-2">
        <h1 class="truncate text-2xl font-bold">{{ activeOrg?.name || 'My organization' }}</h1>
        <span v-if="activeOrg" class="badge badge-sm badge-ghost capitalize">{{ activeOrg.role }}</span>
      </div>
      <!-- Active-org switcher (only when in more than one org) -->
      <select
        v-if="orgContext.orgs.length > 1"
        class="select select-bordered select-sm mt-2 bg-base-100/70"
        :value="orgId"
        @change="orgContext.setActiveOrg($event.target.value); loadTab()"
      >
        <option v-for="o in orgContext.orgs" :key="o.id" :value="o.id">{{ o.name }} ({{ o.role }})</option>
      </select>
    </header>

    <div role="tablist" class="tabs tabs-boxed bg-base-300/40">
      <template v-for="t in TABS" :key="t.key">
        <button v-if="t.show" role="tab" class="tab" :class="{ 'tab-active': tab === t.key }" @click="go(t.key)">{{ t.label }}</button>
      </template>
    </div>

    <AlertMessage type="warning" :message="error" />
    <LoadingSpinner v-if="loading" label="Loading…" />

    <template v-else>
      <!-- DASHBOARD -->
      <section v-if="tab === 'dashboard'" class="space-y-4">
        <div v-if="dashboard?.org?.status === 'suspended'" class="alert alert-warning text-sm">
          This organization is suspended. Scanning and event creation are paused.
        </div>
        <OrgOnboarding
          v-if="isAdmin && dashboard"
          :org-id="orgId"
          :events-total="dashboard?.events?.total ?? 0"
        />
        <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatTile :value="dashboard?.total_scans ?? 0" label="Scans" tone="primary" />
          <StatTile :value="dashboard?.unique_participants ?? 0" label="People" tone="secondary" />
          <StatTile :value="dashboard?.events?.total ?? 0" label="Events" tone="accent" />
          <StatTile :value="dashboard?.badges_minted ?? 0" label="Badges" tone="primary" />
        </div>

        <div class="surface space-y-2 p-4">
          <div class="flex items-center justify-between">
            <h2 class="font-semibold">Scans over time</h2>
            <div role="tablist" class="tabs tabs-boxed tabs-xs bg-base-300/40">
              <button
                v-for="p in DASH_PERIODS"
                :key="p"
                role="tab"
                class="tab capitalize"
                :class="{ 'tab-active': dashPeriod === p }"
                @click="setDashPeriod(p)"
              >{{ p }}</button>
            </div>
          </div>
          <ActivityChart :activity="dashboard?.activity ?? []" :period="dashPeriod" />
        </div>

        <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatTile :value="dashboard?.events?.active ?? 0" label="Active" tone="primary" />
          <StatTile :value="dashboard?.events?.upcoming ?? 0" label="Upcoming" tone="secondary" />
          <StatTile :value="dashboard?.events?.locked ?? 0" label="Locked" tone="accent" />
          <StatTile :value="dashboard?.events?.past ?? 0" label="Past" tone="secondary" />
        </div>

        <div class="surface p-4">
          <h2 class="mb-2 font-semibold">Top events</h2>
          <div v-if="dashboard?.top_events?.length" class="space-y-2">
            <button
              v-for="ev in dashboard.top_events"
              :key="ev.id"
              type="button"
              class="flex w-full items-center justify-between rounded-lg px-1 py-1.5 text-left hover:bg-base-100/60"
              @click="router.push(`/org/events/${ev.id}`)"
            >
              <span class="truncate text-sm">{{ ev.name }}</span>
              <span class="shrink-0 text-sm font-semibold text-primary">{{ ev.scans }} 🏅</span>
            </button>
          </div>
          <p v-else class="py-4 text-center text-sm text-base-content/50">No scans yet.</p>
        </div>
      </section>

      <!-- EVENTS -->
      <section v-else-if="tab === 'events'" class="space-y-3">
        <button v-if="isAdmin" class="btn btn-primary btn-sm tap-target" @click="showNewEvent = !showNewEvent">
          {{ showNewEvent ? 'Cancel' : '+ New event' }}
        </button>
        <div v-if="showNewEvent" class="surface space-y-2 p-4">
          <input v-model="newEvent.name" placeholder="Event name" class="input input-bordered input-sm w-full bg-base-100/70" />
          <select v-model="newEvent.event_type" class="select select-bordered select-sm w-full bg-base-100/70 capitalize">
            <option v-for="ty in EVENT_TYPES" :key="ty" :value="ty">{{ ty }}</option>
          </select>
          <button class="btn btn-primary btn-sm w-full" @click="createEvent">Create event</button>
        </div>
        <button
          v-for="ev in events"
          :key="ev.id"
          type="button"
          class="surface flex w-full items-center justify-between p-4 text-left transition-transform active:scale-[0.98]"
          @click="router.push(`/org/events/${ev.id}`)"
        >
          <div class="min-w-0"><p class="truncate font-medium">{{ ev.name }}</p>
            <p class="text-[0.7rem] text-base-content/45 capitalize">{{ ev.event_type }} · {{ ev.badges_total }} badges</p></div>
          <div class="flex shrink-0 items-center gap-2">
            <span class="badge badge-sm" :class="ev.status === 'active' ? 'badge-primary' : 'badge-ghost'">{{ ev.status }}</span>
            <svg class="h-4 w-4 text-base-content/40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7" /></svg>
          </div>
        </button>
        <p v-if="!events.length" class="surface p-6 text-center text-sm text-base-content/50">No events yet.</p>
      </section>

      <!-- MEMBERS -->
      <section v-else-if="tab === 'members'" class="space-y-4">
        <div class="surface flex gap-2 p-4">
          <input v-model="inviteEmail" type="email" placeholder="invite teammate by email" class="input input-bordered input-sm flex-1 bg-base-100/70" />
          <button class="btn btn-primary btn-sm" @click="sendInvite">Invite</button>
        </div>
        <div class="space-y-2">
          <div v-for="m in members" :key="m.user_id" class="surface flex items-center justify-between gap-2 p-3">
            <div class="min-w-0"><p class="truncate text-sm font-medium">{{ m.name }} {{ m.lastname }}</p>
              <p class="truncate text-[0.7rem] text-base-content/45">{{ m.email }}</p></div>
            <div class="flex items-center gap-2">
              <select v-if="isOwner && m.role !== 'owner'" class="select select-bordered select-xs bg-base-100/70" :value="m.role" @change="setRole(m.user_id, $event.target.value)">
                <option value="admin">admin</option><option value="staff">staff</option>
              </select>
              <span v-else class="badge badge-sm capitalize">{{ m.role }}</span>
              <button v-if="isOwner && m.role !== 'owner'" class="btn btn-ghost btn-xs text-error" @click="removeMember(m.user_id)">remove</button>
            </div>
          </div>
        </div>
        <div v-if="invites.length" class="space-y-2">
          <p class="text-xs uppercase tracking-wide text-base-content/45">Pending invites</p>
          <div v-for="inv in invites" :key="inv.id" class="surface flex items-center justify-between gap-2 p-3">
            <p class="truncate text-sm">{{ inv.email }} <span class="badge badge-xs" :class="inv.status === 'pending' ? 'badge-warning' : 'badge-ghost'">{{ inv.status }}</span></p>
            <button v-if="inv.status === 'pending'" class="btn btn-ghost btn-xs text-error" @click="revokeInvite(inv.id)">revoke</button>
          </div>
        </div>
      </section>

      <!-- PARTICIPANTS -->
      <section v-else-if="tab === 'participants'" class="space-y-2">
        <div v-for="p in participants" :key="p.id" class="surface flex items-center justify-between gap-2 p-3">
          <div class="min-w-0">
            <p class="truncate text-sm font-medium">
              {{ p.name }} {{ p.lastname }}
              <span v-if="p.banned" class="badge badge-xs badge-error">banned</span>
            </p>
            <p class="truncate text-[0.7rem] text-base-content/45">{{ p.email }}</p>
          </div>
          <div class="flex shrink-0 items-center gap-2">
            <span class="text-sm font-semibold text-primary">{{ p.badges_count }} 🏅</span>
            <button
              v-if="isAdmin"
              class="btn btn-ghost btn-xs"
              :class="p.banned ? 'text-success' : 'text-error'"
              @click="banParticipant(p.id, p.banned)"
            >{{ p.banned ? 'unban' : 'ban' }}</button>
          </div>
        </div>
        <p v-if="!participants.length" class="surface p-6 text-center text-sm text-base-content/50">No participants yet.</p>
      </section>

      <!-- AUDIT -->
      <section v-else-if="tab === 'audit'" class="space-y-3">
        <div v-for="(e, i) in audit.entries" :key="i" class="surface p-3">
          <p class="text-sm font-medium">{{ e.action }}</p>
          <p v-if="e.detail" class="truncate text-xs text-base-content/60">{{ e.detail }}</p>
          <p class="text-[0.7rem] text-base-content/45">{{ e.actor_email || e.actor_id }} · {{ fmtTime(e.ts) }}</p>
        </div>
        <p v-if="!audit.entries.length" class="surface p-6 text-center text-sm text-base-content/50">No activity yet.</p>
        <div v-if="audit.entries.length || audit.page > 1" class="flex items-center justify-center gap-5">
          <button class="btn btn-circle btn-sm btn-ghost" :disabled="audit.page <= 1" @click="auditPage(-1)">‹</button>
          <span class="text-xs text-base-content/55">Page {{ audit.page }}</span>
          <button class="btn btn-circle btn-sm btn-ghost" :disabled="!audit.has_more" @click="auditPage(1)">›</button>
        </div>
      </section>

      <!-- SETTINGS -->
      <section v-else-if="tab === 'settings'" class="space-y-3">
        <label class="form-control w-full">
          <span class="label-text mb-1 text-base-content/70">Organization name</span>
          <input v-model="settings.name" class="input input-bordered w-full bg-base-100/70" />
        </label>
        <label class="form-control w-full">
          <span class="label-text mb-1 text-base-content/70">Description</span>
          <textarea v-model="settings.description" rows="3" class="textarea textarea-bordered w-full bg-base-100/70" />
        </label>
        <button class="btn btn-primary w-full tap-target" @click="saveSettings">Save</button>
      </section>
    </template>
  </div>
</template>
