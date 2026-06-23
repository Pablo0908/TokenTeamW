<script setup>
import { reactive, ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useEventsStore } from '@/stores/events'
import { useOrgContextStore } from '@/stores/orgContext'
import QRDisplay from '@/components/domain/QRDisplay.vue'
import ProgressBar from '@/components/domain/ProgressBar.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'
import { printQrSheet } from '@/utils/qrSheet'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const events = useEventsStore()
const orgContext = useOrgContextStore()
const id = route.params.id

// This view is shared by the platform panel (/admin/events/:id) and the org panel
// (/org/events/:id). In org mode it operates against the active org's scoped badge
// endpoints and authorizes on the org role; otherwise it keeps the legacy /admin path.
const isOrgMode = computed(() => route.meta.orgScoped === true)
const orgId = computed(() => (isOrgMode.value ? orgContext.activeOrgId : null))
const canManage = computed(() => (isOrgMode.value ? orgContext.isActiveAdmin : auth.isAdmin))
const backTo = computed(() => (isOrgMode.value ? '/org/events' : '/admin/events'))

const showForm = ref(false)
const creating = ref(false)
const badgeTouched = ref(false)
const lastCreated = ref(null)
const expanded = ref(null)
const copiedToken = ref(null)

// Bulk add (one badge name per line) + QR sheet export.
const showBulk = ref(false)
const bulkText = ref('')
const bulkIcon = ref('🏅')
const bulkColor = ref('primary')
const bulkImage = ref('')
const bulkCreating = ref(false)
const bulkResult = ref('')
const exporting = ref(false)

const bulkNames = computed(() =>
  bulkText.value.split('\n').map((l) => l.trim()).filter(Boolean),
)

async function copyToken(token) {
  try {
    await navigator.clipboard.writeText(token)
    copiedToken.value = token
    setTimeout(() => (copiedToken.value = null), 1500)
  } catch {
    /* clipboard unavailable */
  }
}

const colors = ['primary', 'secondary', 'accent', 'success', 'info', 'warning', 'error']
const form = reactive({ name: '', description: '', icon: '🏅', color: 'primary', image: '' })

const ev = computed(() => events.current)
const list = computed(() => events.adminBadges)
const totalRedemptions = computed(() => list.value.reduce((sum, b) => sum + (b.redeemed_by ?? 0), 0))
const attendees = computed(() => list.value[0]?.total_attendees ?? 0)

let poll = null

async function refresh() {
  await Promise.all([events.fetchEvent(id), events.fetchAdminBadges(id, orgId.value)])
}

const togglingStart = ref(false)
async function toggleStarted() {
  if (!ev.value) return
  togglingStart.value = true
  try {
    await events.setEventStarted(id, !ev.value.started, orgId.value)
    await events.fetchEvent(id)
  } catch {
    /* error surfaced via store */
  } finally {
    togglingStart.value = false
  }
}

async function addBadge() {
  badgeTouched.value = true
  if (!form.name.trim()) return
  creating.value = true
  try {
    const created = await events.addBadge(id, { ...form, name: form.name.trim() }, orgId.value)
    lastCreated.value = created
    expanded.value = created.id
    await refresh()
    form.name = ''
    form.description = ''
    form.icon = '🏅'
    form.color = 'primary'
    form.image = ''
    badgeTouched.value = false
  } catch {
    /* error surfaced via store */
  } finally {
    creating.value = false
  }
}

async function addBulk() {
  const names = bulkNames.value
  if (!names.length) return
  bulkCreating.value = true
  bulkResult.value = ''
  try {
    const list = names.map((name) => ({ name, icon: bulkIcon.value, color: bulkColor.value, image: bulkImage.value.trim() }))
    const res = await events.addBadgesBulk(id, list, orgId.value)
    await refresh()
    bulkResult.value = `✓ Created ${res.count} badge${res.count === 1 ? '' : 's'}`
    bulkText.value = ''
  } catch {
    /* error surfaced via store */
  } finally {
    bulkCreating.value = false
  }
}

async function exportSheet() {
  if (!list.value.length) return
  exporting.value = true
  try {
    const opened = await printQrSheet(ev.value?.name || 'Event', list.value)
    if (!opened) alert('Allow pop-ups to export the QR sheet.')
  } finally {
    exporting.value = false
  }
}

onMounted(async () => {
  await refresh()
  // Near-real-time redemption counts (PRD §4.2 dashboard polling).
  poll = setInterval(() => events.fetchAdminBadges(id, orgId.value), 4000)
})
onBeforeUnmount(() => clearInterval(poll))
</script>

<template>
  <div class="space-y-5 px-4 pb-10 pt-6">
    <button class="tap-target -ml-1 flex items-center gap-1 text-sm text-base-content/70" @click="router.push(backTo)">
      <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M15 19l-7-7 7-7" />
      </svg>
      Events
    </button>

    <AlertMessage type="warning" :message="events.error || ''" />
    <LoadingSpinner v-if="!ev" label="Loading event…" />

    <template v-else>
      <header>
        <h1 class="text-2xl font-bold">{{ ev.name }}</h1>
        <p v-if="ev.description" class="text-sm text-base-content/65">{{ ev.description }}</p>
      </header>

      <!-- Status + manual start/stop (managers only) -->
      <div class="surface flex items-center justify-between gap-3 p-4">
        <div class="min-w-0">
          <p class="flex items-center gap-2">
            <span
              class="badge badge-sm capitalize"
              :class="ev.status === 'active' ? 'badge-success' : ev.status === 'upcoming' ? 'badge-warning' : 'badge-ghost'"
            >{{ ev.status }}</span>
            <span v-if="ev.started" class="text-[0.7rem] font-medium text-success">● started manually</span>
          </p>
          <p class="mt-1 text-[0.7rem] text-base-content/50">
            {{ ev.status === 'active' ? 'Attendees can scan this event now.' : 'Attendees cannot scan this event yet.' }}
          </p>
        </div>
        <button
          v-if="canManage"
          type="button"
          class="btn btn-sm shrink-0 tap-target"
          :class="ev.started ? 'btn-outline btn-warning' : 'btn-success'"
          :disabled="togglingStart"
          @click="toggleStarted"
        >
          <span v-if="togglingStart" class="loading loading-spinner loading-xs" />
          {{ ev.started ? 'Stop event' : 'Start event' }}
        </button>
      </div>

      <!-- Live summary -->
      <section class="grid grid-cols-3 gap-3">
        <div class="surface-soft rounded-2xl p-3 text-center">
          <p class="text-2xl font-bold text-primary">{{ list.length }}</p>
          <p class="text-[0.7rem] uppercase tracking-wide text-base-content/55">Badges</p>
        </div>
        <div class="surface-soft rounded-2xl p-3 text-center">
          <p class="text-2xl font-bold text-success">{{ totalRedemptions }}</p>
          <p class="text-[0.7rem] uppercase tracking-wide text-base-content/55">Redemptions</p>
        </div>
        <div class="surface-soft rounded-2xl p-3 text-center">
          <p class="text-2xl font-bold text-secondary">{{ attendees }}</p>
          <p class="text-[0.7rem] uppercase tracking-wide text-base-content/55">Attendees</p>
        </div>
      </section>

      <p class="flex items-center gap-1.5 text-xs text-base-content/45">
        <span class="inline-block h-2 w-2 animate-pulse rounded-full bg-success" />
        Live — counts refresh automatically
      </p>

      <!-- Add badge (managers only: platform admin, or org owner/admin) -->
      <div v-if="canManage" class="surface p-4">
        <button class="flex w-full items-center justify-between tap-target" :aria-expanded="showForm" @click="showForm = !showForm">
          <span class="font-semibold">Add badge</span>
          <span class="text-xl text-primary">{{ showForm ? '−' : '+' }}</span>
        </button>

        <form v-if="showForm" class="mt-4 space-y-3" novalidate @submit.prevent="addBadge">
          <label class="form-control w-full">
            <span class="label-text mb-1 text-base-content/70">Badge name *</span>
            <input
              v-model="form.name"
              type="text"
              class="input input-bordered w-full bg-base-100/70"
              :class="{ 'input-error': badgeTouched && !form.name.trim() }"
              placeholder="Opening keynote"
            />
          </label>
          <label class="form-control w-full">
            <span class="label-text mb-1 text-base-content/70">Description</span>
            <input v-model="form.description" type="text" class="input input-bordered w-full bg-base-100/70" placeholder="Attended the keynote" />
          </label>
          <div class="flex gap-3">
            <label class="form-control w-24">
              <span class="label-text mb-1 text-base-content/70">Icon</span>
              <input v-model="form.icon" type="text" maxlength="2" class="input input-bordered w-full bg-base-100/70 text-center text-xl" />
            </label>
            <label class="form-control flex-1">
              <span class="label-text mb-1 text-base-content/70">Color</span>
              <select v-model="form.color" class="select select-bordered w-full bg-base-100/70 capitalize">
                <option v-for="c in colors" :key="c" :value="c">{{ c }}</option>
              </select>
            </label>
          </div>
          <label class="form-control w-full">
            <span class="label-text mb-1 text-base-content/70">Image URL (optional — overrides the icon)</span>
            <div class="flex items-center gap-2">
              <input v-model="form.image" type="url" class="input input-bordered w-full bg-base-100/70" placeholder="https://…/badge.png" />
              <img v-if="form.image" :src="form.image" alt="" class="h-10 w-10 shrink-0 rounded-full object-cover ring-1 ring-base-300" />
            </div>
          </label>
          <button type="submit" class="btn btn-primary w-full tap-target" :disabled="creating">
            <span v-if="creating" class="loading loading-spinner loading-sm" />
            {{ creating ? 'Creating…' : 'Create badge + QR' }}
          </button>
        </form>
      </div>

      <!-- Bulk add (managers only: platform admin, or org owner/admin) -->
      <div v-if="canManage" class="surface p-4">
        <button class="flex w-full items-center justify-between tap-target" :aria-expanded="showBulk" @click="showBulk = !showBulk">
          <span class="font-semibold">Bulk add badges</span>
          <span class="text-xl text-primary">{{ showBulk ? '−' : '+' }}</span>
        </button>

        <div v-if="showBulk" class="mt-4 space-y-3">
          <label class="form-control w-full">
            <span class="label-text mb-1 text-base-content/70">One badge name per line</span>
            <textarea
              v-model="bulkText"
              rows="5"
              class="textarea textarea-bordered w-full bg-base-100/70"
              placeholder="Opening keynote&#10;Sponsor booth&#10;Closing party"
            />
          </label>
          <div class="flex gap-3">
            <label class="form-control w-24">
              <span class="label-text mb-1 text-base-content/70">Icon</span>
              <input v-model="bulkIcon" type="text" maxlength="2" class="input input-bordered w-full bg-base-100/70 text-center text-xl" />
            </label>
            <label class="form-control flex-1">
              <span class="label-text mb-1 text-base-content/70">Color</span>
              <select v-model="bulkColor" class="select select-bordered w-full bg-base-100/70 capitalize">
                <option v-for="c in colors" :key="c" :value="c">{{ c }}</option>
              </select>
            </label>
          </div>
          <label class="form-control w-full">
            <span class="label-text mb-1 text-base-content/70">Image URL (optional — applied to all)</span>
            <input v-model="bulkImage" type="url" class="input input-bordered w-full bg-base-100/70" placeholder="https://…/badge.png" />
          </label>
          <p class="text-xs text-base-content/55">{{ bulkNames.length }} badge{{ bulkNames.length === 1 ? '' : 's' }} — each gets its own QR code.</p>
          <button type="button" class="btn btn-primary w-full tap-target" :disabled="bulkCreating || !bulkNames.length" @click="addBulk">
            <span v-if="bulkCreating" class="loading loading-spinner loading-sm" />
            {{ bulkCreating ? 'Creating…' : `Create ${bulkNames.length || ''} badges + QR` }}
          </button>
          <p v-if="bulkResult" class="text-center text-sm font-medium text-success">{{ bulkResult }}</p>
        </div>
      </div>

      <!-- Freshly created QR -->
      <div v-if="lastCreated" class="surface space-y-3 p-4">
        <p class="text-center text-sm font-medium text-success">✓ “{{ lastCreated.name }}” created — print this QR</p>
        <QRDisplay :value="lastCreated.qr_url" :image="lastCreated.qr_image" :label="lastCreated.name" :filename="`${lastCreated.name}-qr.png`" />
      </div>

      <!-- Badge list -->
      <section class="space-y-3">
        <div class="flex items-center justify-between gap-3">
          <h2 class="font-semibold">Badges &amp; QR codes</h2>
          <button
            v-if="list.length"
            type="button"
            class="btn btn-outline btn-xs tap-target gap-1"
            :disabled="exporting"
            @click="exportSheet"
          >
            <span v-if="exporting" class="loading loading-spinner loading-xs" />
            <svg v-else class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M6 9V2h12v7M6 18H4a2 2 0 01-2-2v-5a2 2 0 012-2h16a2 2 0 012 2v5a2 2 0 01-2 2h-2M6 14h12v8H6z" />
            </svg>
            QR sheet
          </button>
        </div>
        <div v-if="list.length" class="space-y-3">
          <div v-for="b in list" :key="b.id" class="surface p-4">
            <div class="flex items-center gap-3">
              <span class="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-base-300/60 text-xl">{{ b.icon || '🏅' }}</span>
              <div class="min-w-0 flex-1">
                <p class="truncate font-medium">{{ b.name }}</p>
                <p class="text-xs text-base-content/55">{{ b.redeemed_by }} / {{ b.total_attendees }} redeemed</p>
              </div>
              <button class="btn btn-outline btn-xs tap-target" @click="expanded = expanded === b.id ? null : b.id">
                {{ expanded === b.id ? 'Hide QR' : 'Show QR' }}
              </button>
            </div>
            <div class="mt-3">
              <ProgressBar :value="b.redeemed_by" :max="b.total_attendees" :show-count="false" />
            </div>
            <div v-if="expanded === b.id" class="mt-4 space-y-3">
              <QRDisplay :value="b.qr_url" :label="b.name" :filename="`${b.name}-qr.png`" />
              <!-- Unique token paired with its QR (for staff verification). -->
              <div class="surface-soft rounded-xl p-3">
                <p class="mb-1 text-[0.7rem] uppercase tracking-wide text-base-content/45">Unique token</p>
                <div class="flex items-center gap-2">
                  <code class="min-w-0 flex-1 truncate font-mono text-xs text-base-content/80">{{ b.token }}</code>
                  <button class="btn btn-ghost btn-xs tap-target" @click="copyToken(b.token)">
                    {{ copiedToken === b.token ? 'Copied!' : 'Copy' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
        <p v-else class="text-sm text-base-content/50">No badges yet — add one above to generate its QR.</p>
      </section>
    </template>
  </div>
</template>
