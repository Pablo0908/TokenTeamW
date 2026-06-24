<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/services/api'

// Guided setup checklist for a freshly-created org, shown on the dashboard tab to
// owners/admins. Step completion is DERIVED from existing data (org settings, members,
// invites, event count) — no new backend. Auto-hides when all steps are done; a manual
// dismiss is remembered per-org in localStorage (mirrors the attendee onboarding pattern).
const props = defineProps({
  orgId: { type: String, default: null },
  eventsTotal: { type: Number, default: 0 },
})

const router = useRouter()
const org = ref(null)
const members = ref([])
const invites = ref([])
const dismissed = ref(false)

function dismissKey(id) {
  return `orgOnboardingDismissed:${id}`
}

async function load() {
  if (!props.orgId) return
  dismissed.value = localStorage.getItem(dismissKey(props.orgId)) === '1'
  try {
    const [o, m, i] = await Promise.all([
      api.get(`/orgs/${props.orgId}`),
      api.get(`/orgs/${props.orgId}/members`),
      api.get(`/orgs/${props.orgId}/invites`),
    ])
    org.value = o.data
    members.value = m.data.members || []
    invites.value = i.data.invites || []
  } catch {
    org.value = null
  }
}

const steps = computed(() => {
  const named = !!(org.value && org.value.name && org.value.name !== 'My organization'
    && (org.value.description || '').trim())
  const invited = members.value.length > 1 || invites.value.some((iv) => iv.status === 'pending')
  const hasEvent = props.eventsTotal > 0
  return [
    { key: 'name', label: 'Name your organization', hint: 'Add a name and description', done: named, to: '/org/settings' },
    { key: 'invite', label: 'Invite a teammate', hint: 'Add an admin or staff member', done: invited, to: '/org/members' },
    { key: 'event', label: 'Create your first event', hint: 'Then mint its badges', done: hasEvent, to: '/org/events' },
  ]
})
const doneCount = computed(() => steps.value.filter((s) => s.done).length)
const allDone = computed(() => doneCount.value === steps.value.length)
const visible = computed(() => !!org.value && !dismissed.value && !allDone.value)

function dismiss() {
  dismissed.value = true
  try { localStorage.setItem(dismissKey(props.orgId), '1') } catch { /* storage unavailable */ }
}

watch(() => props.orgId, load, { immediate: true })
</script>

<template>
  <div v-if="visible" class="surface space-y-3 border border-primary/30 p-4">
    <div class="flex items-start justify-between gap-2">
      <div>
        <h2 class="font-semibold">Get your organization set up</h2>
        <p class="text-xs text-base-content/55">{{ doneCount }} of {{ steps.length }} done</p>
      </div>
      <button class="btn btn-ghost btn-xs" title="Dismiss" @click="dismiss">✕</button>
    </div>
    <ul class="space-y-2">
      <li v-for="s in steps" :key="s.key">
        <button
          type="button"
          class="flex w-full items-center gap-3 rounded-lg px-1 py-1.5 text-left hover:bg-base-100/60"
          @click="router.push(s.to)"
        >
          <span
            class="grid h-6 w-6 shrink-0 place-items-center rounded-full text-xs"
            :class="s.done ? 'bg-success/20 text-success' : 'border border-base-content/25 text-base-content/40'"
          >{{ s.done ? '✓' : '' }}</span>
          <span class="min-w-0 flex-1">
            <span class="block truncate text-sm font-medium" :class="{ 'text-base-content/45 line-through': s.done }">{{ s.label }}</span>
            <span v-if="!s.done" class="block truncate text-[0.7rem] text-base-content/45">{{ s.hint }}</span>
          </span>
          <svg v-if="!s.done" class="h-4 w-4 shrink-0 text-base-content/40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5l7 7-7 7" /></svg>
        </button>
      </li>
    </ul>
  </div>
</template>
