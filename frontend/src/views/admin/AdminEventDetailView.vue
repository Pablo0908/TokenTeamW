<script setup>
import { reactive, ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useEventsStore } from '@/stores/events'
import QRDisplay from '@/components/domain/QRDisplay.vue'
import ProgressBar from '@/components/domain/ProgressBar.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'

const route = useRoute()
const router = useRouter()
const events = useEventsStore()
const id = route.params.id

const showForm = ref(false)
const creating = ref(false)
const badgeTouched = ref(false)
const lastCreated = ref(null)
const expanded = ref(null)

const colors = ['primary', 'secondary', 'accent', 'success', 'info', 'warning', 'error']
const form = reactive({ name: '', description: '', icon: '🏅', color: 'primary' })

const ev = computed(() => events.current)
const list = computed(() => events.adminBadges)
const totalRedemptions = computed(() => list.value.reduce((sum, b) => sum + (b.redeemed_by ?? 0), 0))
const attendees = computed(() => list.value[0]?.total_attendees ?? 0)

let poll = null

async function refresh() {
  await Promise.all([events.fetchEvent(id), events.fetchAdminBadges(id)])
}

async function addBadge() {
  badgeTouched.value = true
  if (!form.name.trim()) return
  creating.value = true
  try {
    const created = await events.addBadge(id, { ...form, name: form.name.trim() })
    lastCreated.value = created
    expanded.value = created.id
    await refresh()
    form.name = ''
    form.description = ''
    form.icon = '🏅'
    form.color = 'primary'
    badgeTouched.value = false
  } catch {
    /* error surfaced via store */
  } finally {
    creating.value = false
  }
}

onMounted(async () => {
  await refresh()
  // Near-real-time redemption counts (PRD §4.2 dashboard polling).
  poll = setInterval(() => events.fetchAdminBadges(id), 4000)
})
onBeforeUnmount(() => clearInterval(poll))
</script>

<template>
  <div class="space-y-5 px-4 pb-10 pt-6">
    <button class="tap-target -ml-1 flex items-center gap-1 text-sm text-base-content/70" @click="router.push('/admin/events')">
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

      <!-- Add badge -->
      <div class="surface p-4">
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
          <button type="submit" class="btn btn-primary w-full tap-target" :disabled="creating">
            <span v-if="creating" class="loading loading-spinner loading-sm" />
            {{ creating ? 'Creating…' : 'Create badge + QR' }}
          </button>
        </form>
      </div>

      <!-- Freshly created QR -->
      <div v-if="lastCreated" class="surface space-y-3 p-4">
        <p class="text-center text-sm font-medium text-success">✓ “{{ lastCreated.name }}” created — print this QR</p>
        <QRDisplay :value="lastCreated.qr_url" :image="lastCreated.qr_image" :label="lastCreated.name" :filename="`${lastCreated.name}-qr.png`" />
      </div>

      <!-- Badge list -->
      <section class="space-y-3">
        <h2 class="font-semibold">Badges &amp; QR codes</h2>
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
            <div v-if="expanded === b.id" class="mt-4">
              <QRDisplay :value="b.qr_url" :label="b.name" :filename="`${b.name}-qr.png`" />
            </div>
          </div>
        </div>
        <p v-else class="text-sm text-base-content/50">No badges yet — add one above to generate its QR.</p>
      </section>
    </template>
  </div>
</template>
