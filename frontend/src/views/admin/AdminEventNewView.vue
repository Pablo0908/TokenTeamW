<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useEventsStore } from '@/stores/events'
import AlertMessage from '@/components/ui/AlertMessage.vue'

const router = useRouter()
const events = useEventsStore()

const form = reactive({ name: '', description: '', event_type: 'conference', visibility: 'public', date: '', end_date: '', location: '', prize: '' })
const touched = ref(false)
const submitting = ref(false)

const EVENT_TYPES = ['conference', 'workshop', 'meetup', 'hackathon', 'networking', 'other']
const VISIBILITIES = [
  { value: 'public', label: 'Public — listed in attendees’ feeds' },
  { value: 'unlisted', label: 'Unlisted — reachable by link, not listed' },
  { value: 'scan-only', label: 'Scan-only — reachable only via its QR' },
]

const valid = computed(() => form.name.trim().length > 0)

async function submit() {
  touched.value = true
  if (!valid.value) return
  submitting.value = true
  try {
    const created = await events.createEvent({ ...form, name: form.name.trim() })
    events.loaded = false // list should refetch to include the new event
    router.push(`/admin/events/${created.id}`)
  } catch {
    /* error surfaced via store */
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="space-y-5 px-4 pb-10 pt-6">
    <button class="tap-target -ml-1 flex items-center gap-1 text-sm text-base-content/70" @click="router.back()">
      <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M15 19l-7-7 7-7" />
      </svg>
      Back
    </button>

    <header>
      <h1 class="text-2xl font-bold">New event</h1>
      <p class="text-sm text-base-content/60">Set up an event, then add its badges.</p>
    </header>

    <form class="space-y-4" novalidate @submit.prevent="submit">
      <AlertMessage type="error" :message="events.error || ''" />

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">Event name *</span>
        <input
          v-model="form.name"
          type="text"
          class="input input-bordered w-full bg-base-100/70"
          :class="{ 'input-error': touched && !valid }"
          placeholder="Lyfter Hackathon 2026"
        />
        <span v-if="touched && !valid" class="mt-1 text-xs text-error">Event name is required.</span>
      </label>

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">Description</span>
        <textarea
          v-model="form.description"
          rows="3"
          class="textarea textarea-bordered w-full bg-base-100/70"
          placeholder="What is this event about?"
        />
      </label>

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">Type</span>
        <select v-model="form.event_type" class="select select-bordered w-full bg-base-100/70 capitalize">
          <option v-for="t in EVENT_TYPES" :key="t" :value="t" class="capitalize">{{ t }}</option>
        </select>
      </label>

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">Visibility</span>
        <select v-model="form.visibility" class="select select-bordered w-full bg-base-100/70">
          <option v-for="v in VISIBILITIES" :key="v.value" :value="v.value">{{ v.label }}</option>
        </select>
      </label>

      <div class="flex gap-3">
        <label class="form-control flex-1">
          <span class="label-text mb-1 text-base-content/70">Start date</span>
          <input v-model="form.date" type="date" class="input input-bordered w-full bg-base-100/70" />
        </label>
        <label class="form-control flex-1">
          <span class="label-text mb-1 text-base-content/70">End date</span>
          <input v-model="form.end_date" type="date" class="input input-bordered w-full bg-base-100/70" />
        </label>
      </div>

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">Location</span>
        <input v-model="form.location" type="text" class="input input-bordered w-full bg-base-100/70" placeholder="San José, CR" />
      </label>

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">Prize</span>
        <input v-model="form.prize" type="text" class="input input-bordered w-full bg-base-100/70" placeholder="VIP pass to the next event" />
      </label>

      <button type="submit" class="btn btn-primary w-full tap-target" :disabled="submitting">
        <span v-if="submitting" class="loading loading-spinner loading-sm" />
        {{ submitting ? 'Creating…' : 'Create event' }}
      </button>
    </form>
  </div>
</template>
