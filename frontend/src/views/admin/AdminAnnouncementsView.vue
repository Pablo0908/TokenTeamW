<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useEventsStore } from '@/stores/events'
import { useAnnouncementsStore } from '@/stores/announcements'
import AlertMessage from '@/components/ui/AlertMessage.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'

const router = useRouter()
const auth = useAuthStore()
const events = useEventsStore()
const anns = useAnnouncementsStore()

onMounted(() => {
  anns.fetchAnnouncements()
  if (!events.loaded) events.fetchEvents()
})

// Create
const showForm = ref(false)
const creating = ref(false)
const createError = ref('')
const createForm = reactive({ title: '', body: '', event_id: '' })

async function submitCreate() {
  if (!createForm.title.trim()) return
  creating.value = true
  createError.value = ''
  try {
    await anns.createAnnouncement({
      title: createForm.title.trim(),
      body: createForm.body.trim(),
      event_id: createForm.event_id || null,
    })
    createForm.title = ''
    createForm.body = ''
    createForm.event_id = ''
    showForm.value = false
  } catch (err) {
    createError.value = err.response?.data?.error ?? 'Unexpected error'
  } finally {
    creating.value = false
  }
}

// Edit
const editingId = ref(null)
const editForm = reactive({ title: '', body: '', event_id: '' })
const editError = ref('')
const editLoading = ref(false)

function startEdit(ann) {
  editingId.value = ann.id
  editForm.title = ann.title
  editForm.body = ann.body
  editForm.event_id = ann.event_id || ''
  editError.value = ''
}

function cancelEdit() {
  editingId.value = null
  editError.value = ''
}

async function submitEdit(id) {
  if (!editForm.title.trim()) return
  editLoading.value = true
  editError.value = ''
  try {
    await anns.updateAnnouncement(id, {
      title: editForm.title.trim(),
      body: editForm.body.trim(),
      event_id: editForm.event_id || null,
    })
    editingId.value = null
  } catch (err) {
    editError.value = err.response?.data?.error ?? 'Unexpected error'
  } finally {
    editLoading.value = false
  }
}

// Delete
const deletingId = ref(null)
const confirmDeleteId = ref(null)

async function confirmDelete(id) {
  deletingId.value = id
  try {
    await anns.deleteAnnouncement(id)
  } finally {
    deletingId.value = null
    confirmDeleteId.value = null
  }
}

function logout() {
  auth.logout()
  router.push('/login')
}

function fmtDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>

<template>
  <div class="space-y-5 px-4 pb-10 pt-6">
    <header class="flex items-center justify-between">
      <div>
        <p class="text-xs uppercase tracking-wide text-secondary">{{ auth.isAdmin ? 'Organizer' : 'Assistant' }}</p>
        <h1 class="text-2xl font-bold">Announcements</h1>
      </div>
      <button class="btn btn-ghost btn-sm tap-target" @click="logout">Log out</button>
    </header>

    <!-- Admin nav -->
    <div role="tablist" class="tabs tabs-boxed bg-base-300/40">
      <RouterLink to="/admin/events" role="tab" class="tab">Events</RouterLink>
      <RouterLink to="/admin/users" role="tab" class="tab">Users</RouterLink>
      <RouterLink v-if="auth.isAdmin" to="/admin/announcements" role="tab" class="tab tab-active">Announcements</RouterLink>
      <RouterLink v-if="auth.isAdmin" to="/admin/audit" role="tab" class="tab">Audit</RouterLink>
    </div>

    <!-- Make Announcement toggle -->
    <button
      v-if="!showForm"
      type="button"
      class="btn btn-primary w-full tap-target"
      @click="showForm = true"
    >
      <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <path d="M12 5v14M5 12h14"/>
      </svg>
      Make Announcement
    </button>

    <!-- Create form -->
    <div v-if="showForm" class="surface space-y-4 p-4">
      <div class="flex items-center justify-between">
        <p class="font-semibold">New Announcement</p>
        <button type="button" class="btn btn-ghost btn-xs" @click="showForm = false; createError = ''">✕</button>
      </div>
      <AlertMessage type="error" :message="createError" />
      <form class="space-y-3" novalidate @submit.prevent="submitCreate">
        <label class="form-control w-full">
          <span class="label-text mb-1">Title</span>
          <input v-model="createForm.title" type="text" placeholder="e.g. Join us at TechFest 2026!" class="input input-bordered w-full" required />
        </label>
        <label class="form-control w-full">
          <span class="label-text mb-1">Description</span>
          <textarea v-model="createForm.body" rows="4" placeholder="Write the announcement details here…" class="textarea textarea-bordered w-full resize-none" />
        </label>
        <label class="form-control w-full">
          <span class="label-text mb-1">Related event <span class="text-base-content/40">(optional)</span></span>
          <select v-model="createForm.event_id" class="select select-bordered w-full">
            <option value="">— None —</option>
            <option v-for="ev in events.events" :key="ev.id" :value="ev.id">{{ ev.name }}</option>
          </select>
        </label>
        <div class="flex gap-2">
          <button type="submit" class="btn btn-primary flex-1 tap-target" :disabled="creating || !createForm.title.trim()">
            <span v-if="creating" class="loading loading-spinner loading-sm" />
            {{ creating ? 'Publishing…' : 'Publish' }}
          </button>
          <button type="button" class="btn btn-ghost tap-target" @click="showForm = false; createError = ''">Cancel</button>
        </div>
      </form>
    </div>

    <LoadingSpinner v-if="anns.loading && !anns.loaded" label="Loading announcements…" />

    <!-- Announcement list -->
    <div v-else-if="anns.announcements.length" class="space-y-3">
      <div
        v-for="ann in anns.announcements"
        :key="ann.id"
        class="surface overflow-hidden"
      >
        <!-- View mode -->
        <template v-if="editingId !== ann.id">
          <div class="p-4 space-y-2">
            <div class="flex items-start justify-between gap-2">
              <p class="font-semibold leading-snug">{{ ann.title }}</p>
              <span class="shrink-0 text-xs text-base-content/40">{{ fmtDate(ann.updated_at || ann.created_at) }}</span>
            </div>
            <p v-if="ann.body" class="whitespace-pre-line text-sm text-base-content/70">{{ ann.body }}</p>
            <div v-if="ann.event_name" class="inline-flex items-center gap-1.5 rounded-full bg-primary/15 px-3 py-1 text-xs font-medium text-primary">
              <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
              </svg>
              {{ ann.event_name }}
            </div>
          </div>
          <div class="flex border-t border-base-300/40">
            <button
              type="button"
              class="flex-1 py-2.5 text-sm font-medium text-base-content/60 tap-target transition-colors hover:text-primary"
              @click="startEdit(ann)"
            >Edit</button>
            <div class="w-px bg-base-300/40" />
            <template v-if="confirmDeleteId === ann.id">
              <button
                type="button"
                class="flex-1 py-2.5 text-sm font-medium text-error tap-target"
                :disabled="deletingId === ann.id"
                @click="confirmDelete(ann.id)"
              >
                <span v-if="deletingId === ann.id" class="loading loading-spinner loading-xs mr-1" />
                Confirm delete
              </button>
              <div class="w-px bg-base-300/40" />
              <button type="button" class="px-4 py-2.5 text-sm tap-target" @click="confirmDeleteId = null">Cancel</button>
            </template>
            <button
              v-else
              type="button"
              class="flex-1 py-2.5 text-sm font-medium text-base-content/60 tap-target transition-colors hover:text-error"
              @click="confirmDeleteId = ann.id"
            >Delete</button>
          </div>
        </template>

        <!-- Edit mode (inline) -->
        <template v-else>
          <div class="p-4 space-y-3">
            <p class="text-sm font-semibold text-primary">Editing</p>
            <AlertMessage type="error" :message="editError" />
            <form class="space-y-3" novalidate @submit.prevent="submitEdit(ann.id)">
              <label class="form-control w-full">
                <span class="label-text mb-1">Title</span>
                <input v-model="editForm.title" type="text" class="input input-bordered w-full" required />
              </label>
              <label class="form-control w-full">
                <span class="label-text mb-1">Description</span>
                <textarea v-model="editForm.body" rows="4" class="textarea textarea-bordered w-full resize-none" />
              </label>
              <label class="form-control w-full">
                <span class="label-text mb-1">Related event</span>
                <select v-model="editForm.event_id" class="select select-bordered w-full">
                  <option value="">— None —</option>
                  <option v-for="ev in events.events" :key="ev.id" :value="ev.id">{{ ev.name }}</option>
                </select>
              </label>
              <div class="flex gap-2">
                <button type="submit" class="btn btn-primary flex-1 tap-target" :disabled="editLoading || !editForm.title.trim()">
                  <span v-if="editLoading" class="loading loading-spinner loading-sm" />
                  {{ editLoading ? 'Saving…' : 'Save changes' }}
                </button>
                <button type="button" class="btn btn-ghost tap-target" @click="cancelEdit">Cancel</button>
              </div>
            </form>
          </div>
        </template>
      </div>
    </div>

    <div v-else-if="anns.loaded" class="surface p-8 text-center text-sm text-base-content/60">
      No announcements yet. Create one to start engaging attendees.
    </div>
  </div>
</template>
