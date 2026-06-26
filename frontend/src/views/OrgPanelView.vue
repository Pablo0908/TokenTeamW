<script setup>
import { computed, ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, readApiError } from '@/services/api'
import { useOrgContextStore } from '@/stores/orgContext'
import { applyOrgTheme, clearOrgTheme } from '@/utils/orgTheme'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'
import StatTile from '@/components/domain/StatTile.vue'
import ActivityChart from '@/components/domain/ActivityChart.vue'
import DateRangePicker from '@/components/domain/DateRangePicker.vue'
import OrgOnboarding from '@/components/domain/OrgOnboarding.vue'
import VerifierPanel from '@/components/domain/VerifierPanel.vue'
import { t } from '@/i18n'
import { roleLabel, eventTypeLabel, inviteStatusLabel } from '@/utils/labels'

const route = useRoute()
const router = useRouter()
const orgContext = useOrgContextStore()

const orgId = computed(() => orgContext.activeOrgId)
const activeOrg = computed(() => orgContext.activeOrg)
const isOwner = computed(() => orgContext.isActiveOwner)
const isAdmin = computed(() => orgContext.isActiveAdmin) // owner or admin
const isStaff = computed(() => orgContext.isActiveStaff) // owner, admin or staff

const TABS = computed(() => [
  { key: 'dashboard', label: t('tabs.dashboard'), show: true },
  { key: 'events', label: t('tabs.events'), show: true },
  { key: 'verifier', label: t('tabs.verifier'), show: isStaff.value },
  { key: 'members', label: t('tabs.members'), show: isAdmin.value },
  { key: 'participants', label: t('tabs.people'), show: true },
  { key: 'audit', label: t('tabs.audit'), show: isAdmin.value },
  { key: 'settings', label: t('tabs.settings'), show: isAdmin.value },
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
const insights = ref(null)
const newReturningSeries = computed(() => [
  { label: t('org.newAttendees'), colorClass: 'bg-primary/70', data: insights.value?.new_vs_returning?.series ?? [] },
])
async function loadInsights(r) {
  if (!orgId.value) return
  try { insights.value = (await api.get(`/orgs/${orgId.value}/insights`, { params: r })).data }
  catch (e) { error.value = readApiError(e, t('org.couldNotLoadInsights')) }
}
const events = ref([])
const members = ref([])
const invites = ref([])
const participants = ref([])
const participantSearch = ref('')
const filteredParticipants = computed(() => {
  const q = participantSearch.value.trim().toLowerCase()
  if (!q) return participants.value
  return participants.value.filter((p) =>
    [p.name, p.lastname, p.email].filter(Boolean).join(' ').toLowerCase().includes(q),
  )
})
const audit = ref({ entries: [], page: 1, has_more: false, total: 0 })
const auditSearch = ref('')
let auditDebounce = null
watch(auditSearch, () => {
  clearTimeout(auditDebounce)
  auditDebounce = setTimeout(() => {
    if (tab.value === 'audit') { audit.value.page = 1; loadTab() }
  }, 350)
})
const settings = ref({ name: '', description: '', theme: { primary: '', secondary: '', accent: '', logo_url: '' } })
const settingsSaved = ref(false)

function pickLogo(e) {
  const file = e.target.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => { settings.value.theme.logo_url = ev.target.result }
  reader.readAsDataURL(file)
}

const NEW_EVENT = () => ({ name: '', description: '', event_type: 'conference', visibility: 'public', date: '', end_date: '', location: '', prize: '' })
const newEvent = ref(NEW_EVENT())
const showNewEvent = ref(false)
const inviteEmail = ref('')
// In-flight guard so double-clicking create/invite/save doesn't POST twice
// (would otherwise create duplicate events / invites).
const submitting = ref(false)
const EVENT_TYPES = ['conference', 'workshop', 'meetup', 'hackathon', 'networking', 'other']
const VISIBILITIES = computed(() => [
  { value: 'public', label: t('org.visPublic') },
  { value: 'unlisted', label: t('org.visUnlisted') },
  { value: 'scan-only', label: t('org.visScanOnly') },
])

function fmtTime(ts) { const d = new Date(ts); return Number.isNaN(d.getTime()) ? ts : d.toLocaleString() }

// Reuse the shared audit-action labels (keys use underscores instead of dots).
function auditActionLabel(action) {
  if (!action) return ''
  const label = t(`admin.audit.actions.${action.replace(/\./g, '_')}`)
  return label.startsWith('admin.audit.actions.') ? action : label
}

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
    else if (tab.value === 'audit') audit.value = (await api.get(`${base}/audit`, { params: { page: audit.value.page, q: auditSearch.value.trim() || undefined } })).data
    else if (tab.value === 'settings') {
      const o = (await api.get(base)).data
      settings.value = {
        name: o.name || '',
        description: o.description || '',
        theme: { primary: '', secondary: '', accent: '', logo_url: '', ...(o.theme || {}) },
      }
    }
  } catch (e) { error.value = readApiError(e, t('org.couldNotLoadSection')) }
  finally { loading.value = false }
}

async function createEvent() {
  if (!newEvent.value.name.trim() || submitting.value) return
  submitting.value = true
  try {
    await api.post(`/orgs/${orgId.value}/event`, { ...newEvent.value, name: newEvent.value.name.trim() })
    showNewEvent.value = false; newEvent.value = NEW_EVENT()
    await loadTab()
  } catch (e) { error.value = readApiError(e, t('org.couldNotCreateEvent')) }
  finally { submitting.value = false }
}
async function sendInvite() {
  const email = inviteEmail.value.trim()
  if (!email || submitting.value) return
  submitting.value = true
  try { await api.post(`/orgs/${orgId.value}/invites`, { email }); inviteEmail.value = ''; await loadTab() }
  catch (e) { error.value = readApiError(e, t('org.couldNotSendInvite')) }
  finally { submitting.value = false }
}
async function revokeInvite(id) {
  try { await api.post(`/orgs/${orgId.value}/invites/${id}/revoke`); await loadTab() }
  catch (e) { error.value = readApiError(e, t('org.couldNotRevokeInvite')) }
}
async function setRole(uid, role) {
  try { await api.patch(`/orgs/${orgId.value}/members/${uid}`, { role }); await loadTab() }
  catch (e) { error.value = readApiError(e, t('org.couldNotChangeRole')) }
}
async function removeMember(uid) {
  try { await api.delete(`/orgs/${orgId.value}/members/${uid}`); await loadTab() }
  catch (e) { error.value = readApiError(e, t('org.couldNotRemoveMember')) }
}
async function banParticipant(uid, banned) {
  try {
    if (banned) await api.delete(`/orgs/${orgId.value}/participants/${uid}/ban`)
    else await api.post(`/orgs/${orgId.value}/participants/${uid}/ban`)
    await loadTab()
  } catch (e) { error.value = readApiError(e, t('org.couldNotUpdateBan')) }
}
async function saveSettings() {
  if (submitting.value) return
  submitting.value = true
  try {
    await api.patch(`/orgs/${orgId.value}`, {
      name: settings.value.name.trim(),
      description: settings.value.description.trim(),
      theme: settings.value.theme,
    })
    await orgContext.load()
    applyOrgTheme(orgContext.activeOrg?.theme)
    settingsSaved.value = true
    setTimeout(() => { settingsSaved.value = false }, 2500)
  } catch (e) { error.value = readApiError(e, t('org.couldNotSaveSettings')) }
  finally { submitting.value = false }
}
function resetTheme() {
  settings.value.theme = { primary: '', secondary: '', accent: '', logo_url: '' }
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

// Sliding active-tab indicator: measure the active tab and animate a single pill to it.
const tablistEl = ref(null)
const indicator = ref({ left: 0, top: 0, width: 0, height: 0, ready: false })
function updateIndicator() {
  const root = tablistEl.value
  const el = root?.querySelector('[data-active="true"]')
  if (!el) { indicator.value = { ...indicator.value, ready: false }; return }
  indicator.value = {
    left: el.offsetLeft, top: el.offsetTop,
    width: el.offsetWidth, height: el.offsetHeight, ready: true,
  }
}
watch([tab, TABS], () => nextTick(updateIndicator), { flush: 'post' })
onMounted(() => { nextTick(updateIndicator); window.addEventListener('resize', updateIndicator) })
onUnmounted(() => window.removeEventListener('resize', updateIndicator))

// Apply the active org's brand colors while the panel is open; restore on leave.
watch(() => activeOrg.value?.theme, (th) => applyOrgTheme(th || {}), { immediate: true, deep: true })
onUnmounted(clearOrgTheme)
</script>

<template>
  <div class="space-y-5 px-4 lg:px-6 pb-10 pt-6">
    <header>
      <p class="text-xs uppercase tracking-wide text-secondary">{{ $t('org.eyebrow') }}</p>
      <div class="flex items-center gap-2">
        <img
          v-if="activeOrg?.theme?.logo_url"
          :src="activeOrg.theme.logo_url"
          alt=""
          class="h-8 w-8 shrink-0 rounded-lg object-cover ring-1 ring-base-300"
        />
        <h1 class="truncate text-2xl font-bold">{{ activeOrg?.name || $t('org.defaultName') }}</h1>
        <span v-if="activeOrg" class="badge badge-sm badge-ghost">{{ roleLabel(activeOrg.role) }}</span>
        <span v-if="orgContext.isSuperAdmin" class="badge badge-sm badge-secondary">{{ $t('roles.superAdmin') }}</span>
      </div>
      <!-- Active-org switcher (only when in more than one org) -->
      <select
        v-if="orgContext.orgs.length > 1"
        class="select select-bordered select-sm mt-2 bg-base-100/70"
        :value="orgId"
        @change="orgContext.setActiveOrg($event.target.value); loadTab()"
      >
        <option v-for="o in orgContext.orgs" :key="o.id" :value="o.id">{{ o.name }} ({{ roleLabel(o.role) }})</option>
      </select>
    </header>

    <div ref="tablistEl" role="tablist" class="tabs tabs-boxed relative bg-base-300/40 flex-nowrap overflow-x-auto">
      <span
        class="pointer-events-none absolute z-0 rounded-full bg-primary shadow-sm transition-all duration-300 ease-out"
        :style="{
          left: indicator.left + 'px',
          top: indicator.top + 'px',
          width: indicator.width + 'px',
          height: indicator.height + 'px',
          opacity: indicator.ready ? 1 : 0,
        }"
        aria-hidden="true"
      />
      <template v-for="t in TABS" :key="t.key">
        <RouterLink
          v-if="t.show"
          :to="`/org/${t.key}`"
          role="tab"
          :data-active="tab === t.key"
          class="tab relative z-10 transition-colors duration-200"
          :class="tab === t.key
            ? '!text-primary-content'
            : 'text-base-content/60 hover:text-base-content'"
        >{{ t.label }}</RouterLink>
      </template>
    </div>

    <AlertMessage type="warning" :message="error" />
    <LoadingSpinner v-if="loading" :label="$t('admin.loading')" />

    <template v-else>
      <!-- DASHBOARD -->
      <section v-if="tab === 'dashboard'" class="space-y-4">
        <div v-if="dashboard?.org?.status === 'suspended'" class="alert alert-warning text-sm">
          {{ $t('org.suspendedNotice') }}
        </div>
        <OrgOnboarding
          v-if="isAdmin && dashboard"
          :org-id="orgId"
          :events-total="dashboard?.events?.total ?? 0"
        />
        <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatTile :value="dashboard?.total_scans ?? 0" :label="$t('org.kpiScans')" tone="primary" />
          <StatTile :value="dashboard?.unique_participants ?? 0" :label="$t('org.kpiPeople')" tone="secondary" />
          <StatTile :value="dashboard?.events?.total ?? 0" :label="$t('org.kpiEvents')" tone="accent" />
          <StatTile :value="dashboard?.badges_minted ?? 0" :label="$t('org.kpiBadges')" tone="primary" />
        </div>

        <div class="surface space-y-2 p-4">
          <div class="flex items-center justify-between">
            <h2 class="font-semibold">{{ $t('org.scansOverTime') }}</h2>
            <div role="tablist" class="tabs tabs-boxed tabs-xs bg-base-300/40">
              <button
                v-for="p in DASH_PERIODS"
                :key="p"
                role="tab"
                class="tab capitalize"
                :class="{ 'tab-active': dashPeriod === p }"
                @click="setDashPeriod(p)"
              >{{ $t('dateRange.' + p) }}</button>
            </div>
          </div>
          <ActivityChart :activity="dashboard?.activity ?? []" :period="dashPeriod" />
        </div>

        <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatTile :value="dashboard?.events?.active ?? 0" :label="$t('org.kpiActive')" tone="primary" />
          <StatTile :value="dashboard?.events?.upcoming ?? 0" :label="$t('org.kpiUpcoming')" tone="secondary" />
          <StatTile :value="dashboard?.events?.locked ?? 0" :label="$t('org.kpiLocked')" tone="accent" />
          <StatTile :value="dashboard?.events?.past ?? 0" :label="$t('org.kpiPast')" tone="secondary" />
        </div>

        <div class="surface p-4">
          <h2 class="mb-2 font-semibold">{{ $t('org.topEvents') }}</h2>
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
          <p v-else class="py-4 text-center text-sm text-base-content/50">{{ $t('org.noScansYet') }}</p>
        </div>

        <!-- Attendee insights -->
        <div class="surface space-y-3 p-4">
          <h2 class="font-semibold">{{ $t('org.attendeeInsights') }}</h2>
          <DateRangePicker @change="loadInsights" />
          <template v-if="insights">
            <div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <StatTile :value="insights.kpi_deltas.scans.value" :label="$t('org.kpiScans')" tone="primary" :delta="insights.kpi_deltas.scans.delta_pct" />
              <StatTile :value="insights.kpi_deltas.participants.value" :label="$t('org.kpiPeople')" tone="secondary" :delta="insights.kpi_deltas.participants.delta_pct" />
              <StatTile :value="insights.new_vs_returning.new" :label="$t('org.kpiNew')" tone="accent" />
              <StatTile :value="insights.new_vs_returning.returning" :label="$t('org.kpiReturning')" tone="secondary" />
            </div>
            <div>
              <p class="mb-1 text-xs uppercase tracking-wide text-base-content/45">{{ $t('org.newAttendeesOverTime') }}</p>
              <ActivityChart :series="newReturningSeries" :period="insights.period" />
            </div>
            <div class="rounded-xl bg-base-100/40 p-3">
              <div class="flex items-center justify-between">
                <span class="text-sm font-medium">{{ $t('org.returnRate') }}</span>
                <span class="text-sm font-semibold text-primary">{{ insights.retention.return_rate }}%</span>
              </div>
              <p class="text-[0.7rem] text-base-content/45">
                {{ $t('org.retentionNote', { repeat: insights.retention.repeat, attendees: insights.retention.attendees }) }}
              </p>
            </div>
          </template>
        </div>
      </section>

      <!-- EVENTS -->
      <section v-else-if="tab === 'events'" class="space-y-3">
        <button v-if="isAdmin" class="btn btn-primary btn-sm tap-target" @click="showNewEvent = !showNewEvent">
          {{ showNewEvent ? $t('common.cancel') : $t('org.newEvent') }}
        </button>
        <div v-if="showNewEvent" class="surface space-y-2 p-4 mx-auto w-full max-w-2xl">
          <input v-model="newEvent.name" :placeholder="$t('org.eventName')" class="input input-bordered input-sm w-full bg-base-100/70" />
          <textarea v-model="newEvent.description" rows="2" :placeholder="$t('admin.eventNew.descriptionLabel')" class="textarea textarea-bordered textarea-sm w-full bg-base-100/70" />
          <select v-model="newEvent.event_type" class="select select-bordered select-sm w-full bg-base-100/70">
            <option v-for="ty in EVENT_TYPES" :key="ty" :value="ty">{{ eventTypeLabel(ty) }}</option>
          </select>
          <select v-model="newEvent.visibility" class="select select-bordered select-sm w-full bg-base-100/70">
            <option v-for="v in VISIBILITIES" :key="v.value" :value="v.value">{{ v.label }}</option>
          </select>
          <div class="flex gap-2">
            <label class="form-control flex-1">
              <span class="label-text mb-1 text-xs text-base-content/60">{{ $t('org.hostingDay') }}</span>
              <input v-model="newEvent.date" type="date" class="input input-bordered input-sm w-full bg-base-100/70" />
            </label>
            <label class="form-control flex-1">
              <span class="label-text mb-1 text-xs text-base-content/60">{{ $t('org.endDay') }}</span>
              <input v-model="newEvent.end_date" type="date" class="input input-bordered input-sm w-full bg-base-100/70" />
            </label>
          </div>
          <input v-model="newEvent.location" :placeholder="$t('admin.eventNew.locationLabel')" class="input input-bordered input-sm w-full bg-base-100/70" />
          <input v-model="newEvent.prize" :placeholder="$t('admin.eventNew.prizeLabel')" class="input input-bordered input-sm w-full bg-base-100/70" />
          <p class="text-[0.7rem] text-base-content/55">{{ $t('org.startsClosed') }}</p>
          <button class="btn btn-primary btn-sm w-full" :disabled="submitting" @click="createEvent">{{ $t('org.createEvent') }}</button>
        </div>
        <div class="grid grid-cols-1 gap-3 lg:grid-cols-2 xl:grid-cols-3">
        <button
          v-for="ev in events"
          :key="ev.id"
          type="button"
          class="surface flex w-full items-center justify-between p-4 text-left transition-transform active:scale-[0.98]"
          @click="router.push(`/org/events/${ev.id}`)"
        >
          <div class="min-w-0"><p class="truncate font-medium">{{ ev.name }}</p>
            <p class="text-[0.7rem] text-base-content/45">{{ eventTypeLabel(ev.event_type) }} · {{ ev.badges_total }} {{ $t('org.unitBadges') }}</p></div>
          <div class="flex shrink-0 items-center gap-2">
            <span class="badge badge-sm" :class="ev.status === 'active' ? 'badge-primary' : 'badge-ghost'">{{ $t('events.status.' + ev.status) }}</span>
            <svg class="h-4 w-4 text-base-content/40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7" /></svg>
          </div>
        </button>
        </div>
        <p v-if="!events.length" class="surface p-6 text-center text-sm text-base-content/50">{{ $t('org.noEventsYet') }}</p>
      </section>

      <!-- VERIFIER (staff+) — scan an attendee's prize-claim QR and hand over the prize. -->
      <section v-else-if="tab === 'verifier'" class="surface p-4 mx-auto w-full max-w-2xl">
        <VerifierPanel />
      </section>

      <!-- MEMBERS -->
      <section v-else-if="tab === 'members'" class="space-y-4">
        <div class="surface flex gap-2 p-4 mx-auto w-full max-w-2xl">
          <input v-model="inviteEmail" type="email" :placeholder="$t('org.invitePlaceholder')" class="input input-bordered input-sm flex-1 bg-base-100/70" />
          <button class="btn btn-primary btn-sm" :disabled="submitting" @click="sendInvite">{{ $t('org.invite') }}</button>
        </div>
        <div class="grid grid-cols-1 gap-2 lg:grid-cols-2 lg:gap-3">
          <div v-for="m in members" :key="m.user_id" class="surface flex items-center justify-between gap-2 p-3">
            <div class="min-w-0"><p class="truncate text-sm font-medium">{{ m.name }} {{ m.lastname }}</p>
              <p class="truncate text-[0.7rem] text-base-content/45">{{ m.email }}</p></div>
            <div class="flex items-center gap-2">
              <select v-if="isOwner && m.role !== 'owner'" class="select select-bordered select-xs bg-base-100/70" :value="m.role" @change="setRole(m.user_id, $event.target.value)">
                <option value="admin">{{ roleLabel('admin') }}</option><option value="staff">{{ roleLabel('staff') }}</option>
              </select>
              <span v-else class="badge badge-sm">{{ roleLabel(m.role) }}</span>
              <button v-if="isOwner && m.role !== 'owner'" class="btn btn-ghost btn-xs text-error" @click="removeMember(m.user_id)">{{ $t('org.remove') }}</button>
            </div>
          </div>
        </div>
        <div v-if="invites.length" class="space-y-2">
          <p class="text-xs uppercase tracking-wide text-base-content/45">{{ $t('org.pendingInvites') }}</p>
          <div v-for="inv in invites" :key="inv.id" class="surface flex items-center justify-between gap-2 p-3">
            <p class="truncate text-sm">{{ inv.email }} <span class="badge badge-xs" :class="inv.status === 'pending' ? 'badge-warning' : 'badge-ghost'">{{ inviteStatusLabel(inv.status) }}</span></p>
            <button v-if="inv.status === 'pending'" class="btn btn-ghost btn-xs text-error" @click="revokeInvite(inv.id)">{{ $t('org.revoke') }}</button>
          </div>
        </div>
      </section>

      <!-- PARTICIPANTS -->
      <section v-else-if="tab === 'participants'" class="space-y-2">
        <input
          v-model="participantSearch"
          type="search"
          :placeholder="$t('org.searchPeople')"
          class="input input-bordered input-sm w-full bg-base-100/70 lg:max-w-md"
        />
        <div class="grid grid-cols-1 gap-2 lg:grid-cols-2 xl:grid-cols-3 lg:gap-3">
        <div v-for="p in filteredParticipants" :key="p.id" class="surface flex items-center justify-between gap-2 p-3">
          <div class="min-w-0">
            <p class="truncate text-sm font-medium">
              {{ p.name }} {{ p.lastname }}
              <span v-if="p.banned" class="badge badge-xs badge-error">{{ $t('org.banned') }}</span>
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
            >{{ p.banned ? $t('org.unban') : $t('org.ban') }}</button>
          </div>
        </div>
        </div>
        <p v-if="!participants.length" class="surface p-6 text-center text-sm text-base-content/50">{{ $t('org.noParticipantsYet') }}</p>
      </section>

      <!-- AUDIT -->
      <section v-else-if="tab === 'audit'" class="space-y-3">
        <input
          v-model="auditSearch"
          type="search"
          :placeholder="$t('org.searchAudit')"
          class="input input-bordered input-sm w-full bg-base-100/70 lg:max-w-md"
        />
        <div class="grid grid-cols-1 gap-3 lg:grid-cols-2">
        <div v-for="(e, i) in audit.entries" :key="i" class="surface p-3">
          <p class="text-sm font-medium">{{ auditActionLabel(e.action) }}</p>
          <p v-if="e.detail" class="truncate text-xs text-base-content/60">{{ e.detail }}</p>
          <p class="text-[0.7rem] text-base-content/45">{{ e.actor_email || e.actor_id }} · {{ fmtTime(e.ts) }}</p>
        </div>
        </div>
        <p v-if="!audit.entries.length" class="surface p-6 text-center text-sm text-base-content/50">{{ $t('org.noActivityYet') }}</p>
        <div v-if="audit.entries.length || audit.page > 1" class="flex items-center justify-center gap-5">
          <button class="btn btn-circle btn-sm btn-ghost" :disabled="audit.page <= 1" @click="auditPage(-1)">‹</button>
          <span class="text-xs text-base-content/55">{{ $t('org.page') }} {{ audit.page }}</span>
          <button class="btn btn-circle btn-sm btn-ghost" :disabled="!audit.has_more" @click="auditPage(1)">›</button>
        </div>
      </section>

      <!-- SETTINGS -->
      <section v-else-if="tab === 'settings'" class="mx-auto w-full max-w-2xl space-y-4">

        <!-- Logo / identidad -->
        <div class="surface p-5 space-y-4">
          <h2 class="font-semibold text-base">{{ $t('org.identity') }}</h2>

          <!-- Logo upload -->
          <div class="flex flex-col sm:flex-row items-center gap-4">
            <div class="relative shrink-0">
              <div class="h-20 w-20 rounded-2xl overflow-hidden ring-2 ring-base-300 bg-base-200 flex items-center justify-center">
                <img v-if="settings.theme.logo_url" :src="settings.theme.logo_url" alt="" class="h-full w-full object-cover" />
                <svg v-else class="h-8 w-8 text-base-content/30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/>
                </svg>
              </div>
              <label class="absolute -bottom-1 -right-1 grid h-7 w-7 cursor-pointer place-items-center rounded-full bg-primary shadow ring-2 ring-base-100 transition-transform active:scale-90">
                <svg class="h-3.5 w-3.5 text-primary-content" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/>
                </svg>
                <input type="file" accept="image/*" class="sr-only" @change="pickLogo" />
              </label>
            </div>
            <div class="flex-1 w-full space-y-2">
              <label class="form-control w-full">
                <span class="label-text text-xs text-base-content/60 mb-1">{{ $t('org.orgName') }}</span>
                <input v-model="settings.name" class="input input-bordered w-full bg-base-100/70" :placeholder="$t('org.orgName')" />
              </label>
              <p class="text-[0.7rem] text-base-content/45">{{ $t('org.logoHint') }}</p>
            </div>
          </div>

          <!-- Description -->
          <label class="form-control w-full">
            <span class="label-text text-xs text-base-content/60 mb-1">{{ $t('org.description') }}</span>
            <textarea v-model="settings.description" rows="3" class="textarea textarea-bordered w-full bg-base-100/70" :placeholder="$t('org.descriptionPlaceholder')" />
          </label>
        </div>

        <!-- Colores / branding -->
        <div class="surface p-5 space-y-3">
          <div class="flex items-center justify-between">
            <h2 class="font-semibold text-base">{{ $t('org.theme') }}</h2>
            <button class="btn btn-ghost btn-xs" @click="resetTheme">{{ $t('org.resetTheme') }}</button>
          </div>
          <p class="text-[0.7rem] text-base-content/55">{{ $t('org.themeHint') }}</p>
          <div class="grid grid-cols-3 gap-3">
            <label class="form-control">
              <span class="label-text mb-1 text-xs text-base-content/60">{{ $t('org.primary') }}</span>
              <input v-model="settings.theme.primary" type="color" class="h-10 w-full cursor-pointer rounded-lg bg-base-100/70 p-1" />
            </label>
            <label class="form-control">
              <span class="label-text mb-1 text-xs text-base-content/60">{{ $t('org.secondary') }}</span>
              <input v-model="settings.theme.secondary" type="color" class="h-10 w-full cursor-pointer rounded-lg bg-base-100/70 p-1" />
            </label>
            <label class="form-control">
              <span class="label-text mb-1 text-xs text-base-content/60">{{ $t('org.accent') }}</span>
              <input v-model="settings.theme.accent" type="color" class="h-10 w-full cursor-pointer rounded-lg bg-base-100/70 p-1" />
            </label>
          </div>
        </div>

        <!-- Guardar -->
        <button
          class="btn btn-primary w-full tap-target"
          :class="{ 'btn-success': settingsSaved }"
          :disabled="submitting"
          @click="saveSettings"
        >
          <svg v-if="settingsSaved" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l4 4L19 7"/></svg>
          {{ settingsSaved ? $t('org.saved') : $t('org.save') }}
        </button>
      </section>
    </template>
  </div>
</template>
