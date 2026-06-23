<script setup>
import { onMounted, ref, reactive, computed } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAnnouncementsStore } from '@/stores/announcements'
import { useEventsStore } from '@/stores/events'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'

const router = useRouter()
const auth = useAuthStore()
const announcements = useAnnouncementsStore()
const events = useEventsStore()

// editingId === null + form empty => creating; otherwise editing that announcement.
const editingId = ref(null)
const form = reactive({ title: '', body: '', event_id: '', enable_event: false })
const touched = ref(false)
const submitting = ref(false)
const deletingId = ref(null)

const valid = computed(() => form.title.trim() && form.body.trim())
const eventName = (id) => events.events.find((e) => e.id === id)?.name || ''

function fmt(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return Number.isNaN(d.getTime()) ? ts : d.toLocaleString()
}

function resetForm() {
  editingId.value = null
  form.title = ''
  form.body = ''
  form.event_id = ''
  form.enable_event = false
  touched.value = false
}

function startEdit(a) {
  editingId.value = a.id
  form.title = a.title
  form.body = a.body
  form.event_id = a.event_id || ''
  form.enable_event = false
  touched.value = false
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function submit() {
  touched.value = true
  if (!valid.value) return
  submitting.value = true
  try {
    const payload = {
      title: form.title.trim(),
      body: form.body.trim(),
      event_id: form.event_id || null,
      enable_event: !!(form.event_id && form.enable_event),
    }
    if (editingId.value) await announcements.update(editingId.value, payload)
    else await announcements.create(payload)
    resetForm()
    await announcements.fetchAnnouncements()
  } catch {
    /* error surfaced via store */
  } finally {
    submitting.value = false
  }
}

async function remove(a) {
  if (!window.confirm(`Delete announcement "${a.title}"? This cannot be undone.`)) return
  deletingId.value = a.id
  try {
    await announcements.remove(a.id)
    if (editingId.value === a.id) resetForm()
    await announcements.fetchAnnouncements()
  } catch {
    /* error surfaced via store */
  } finally {
    deletingId.value = null
  }
}

function logout() {
  auth.logout()
  router.push('/login')
}

onMounted(() => {
  announcements.fetchAnnouncements()
  if (!events.loaded) events.fetchEvents()
})
</script>

<template>
  <div class="space-y-5 px-4 pb-10 pt-6">
    <header class="flex items-center justify-between">
      <div>
        <p class="text-xs uppercase tracking-wide text-secondary">Platform</p>
        <h1 class="text-2xl font-bold">Announcements</h1>
      </div>
      <button class="btn btn-ghost btn-sm tap-target" @click="logout">Log out</button>
    </header>

    <div role="tablist" class="tabs tabs-boxed bg-base-300/40">
      <RouterLink to="/admin/events" role="tab" class="tab">Events</RouterLink>
      <RouterLink to="/admin/users" role="tab" class="tab">Users</RouterLink>
      <RouterLink to="/admin/audit" role="tab" class="tab">Audit</RouterLink>
      <RouterLink to="/admin/org-invites" role="tab" class="tab">Orgs</RouterLink>
      <RouterLink to="/admin/announcements" role="tab" class="tab tab-active">News</RouterLink>
    </div>

    <p class="text-xs text-base-content/55">
      Announcements appear on everyone's home page. Link one to any event so users know where and when it happens.
    </p>

    <!-- Composer / editor -->
    <form class="surface space-y-3 p-4" novalidate @submit.prevent="submit">
      <div class="flex items-center justify-between">
        <h2 class="font-semibold">{{ editingId ? 'Edit announcement' : 'New announcement' }}</h2>
        <button v-if="editingId" type="button" class="btn btn-ghost btn-xs" @click="resetForm">Cancel edit</button>
      </div>

      <AlertMessage type="error" :message="announcements.error || ''" />

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">Title *</span>
        <input
          v-model="form.title"
          type="text"
          class="input input-bordered input-sm w-full bg-base-100/70"
          :class="{ 'input-error': touched && !form.title.trim() }"
          placeholder="Doors open at 6pm!"
        />
      </label>

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">Description *</span>
        <textarea
          v-model="form.body"
          rows="3"
          class="textarea textarea-bordered w-full bg-base-100/70"
          :class="{ 'textarea-error': touched && !form.body.trim() }"
          placeholder="Tell users what's happening and how to join."
        />
      </label>

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">Linked event (optional)</span>
        <select v-model="form.event_id" class="select select-bordered select-sm w-full bg-base-100/70">
          <option value="">No linked event</option>
          <option v-for="ev in events.events" :key="ev.id" :value="ev.id">{{ ev.name }}</option>
        </select>
      </label>

      <!-- Auto-enable the linked event so an announced event is scannable right away -->
      <label v-if="form.event_id" class="flex cursor-pointer items-start gap-2 rounded-xl bg-base-100/50 p-3">
        <input v-model="form.enable_event" type="checkbox" class="checkbox checkbox-sm checkbox-primary mt-0.5" />
        <span class="text-sm">
          Start the linked event now
          <span class="block text-[0.7rem] text-base-content/55">Forces it active so attendees can scan immediately — no need to set it live separately.</span>
        </span>
      </label>

      <button type="submit" class="btn btn-primary btn-sm w-full tap-target" :disabled="submitting">
        <span v-if="submitting" class="loading loading-spinner loading-xs" />
        {{ editingId ? 'Save changes' : 'Post announcement' }}
      </button>
    </form>

    <LoadingSpinner v-if="announcements.loading && !announcements.loaded" label="Loading announcements…" />

    <section v-else-if="announcements.items.length" class="space-y-3">
      <div v-for="a in announcements.items" :key="a.id" class="surface p-4">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0 flex-1">
            <p class="truncate font-semibold">{{ a.title }}</p>
            <p class="mt-1 whitespace-pre-line text-sm text-base-content/70">{{ a.body }}</p>
            <p v-if="a.event_id" class="mt-2 text-[0.7rem] text-primary">
              🔗 {{ eventName(a.event_id) || 'Linked event' }}
            </p>
            <p class="mt-1 text-[0.7rem] text-base-content/45">{{ fmt(a.created_at) }}</p>
          </div>
          <div class="flex shrink-0 flex-col gap-1">
            <button class="btn btn-ghost btn-xs text-primary" @click="startEdit(a)">Edit</button>
            <button class="btn btn-ghost btn-xs text-error" :disabled="deletingId === a.id" @click="remove(a)">
              <span v-if="deletingId === a.id" class="loading loading-spinner loading-xs" />
              <span v-else>Delete</span>
            </button>
          </div>
        </div>
      </div>
    </section>

    <div v-else-if="announcements.loaded" class="surface p-8 text-center text-sm text-base-content/60">
      No announcements yet. Post the first one above.
    </div>
  </div>
</template>
