<script setup>
import { onMounted, computed, ref } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUsersStore } from '@/stores/users'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'

const router = useRouter()
const auth = useAuthStore()
const users = useUsersStore()

const updatingId = ref(null)
const confirmModal = ref(null) // { type: 'disable'|'enable'|'delete', user: {...} }

// Most-active attendees first so admins can see badge collection at a glance.
const sorted = computed(() =>
  [...users.users].sort((a, b) => (b.badges_count ?? 0) - (a.badges_count ?? 0)),
)

const isSelf = (u) => u.id === auth.user?.id

// Admin sees "Organizer"; assistant sees "Assistant".
const roleLabel = computed(() => (auth.isAdmin ? 'Organizer' : 'Assistant'))
const roleBadgeClass = (role) =>
  role === 'admin' ? 'badge-secondary' : role === 'assistant' ? 'badge-accent' : 'badge-ghost'

// Admin-only: set any user to attendee / assistant / admin.
async function changeRole(u, role) {
  if (role === u.role) return
  updatingId.value = u.id
  try {
    await users.setRole(u.id, role)
  } catch {
    /* error surfaced via store */
  } finally {
    updatingId.value = null
  }
}

function openConfirm(type, user) {
  confirmModal.value = { type, user }
}

function closeConfirm() {
  confirmModal.value = null
}

async function confirmAction() {
  const { type, user } = confirmModal.value
  closeConfirm()
  updatingId.value = user.id
  try {
    if (type === 'disable') await users.disableUser(user.id, true)
    else if (type === 'enable') await users.disableUser(user.id, false)
    else if (type === 'delete') await users.deleteUser(user.id)
  } catch {
    /* error surfaced via store */
  } finally {
    updatingId.value = null
  }
}

function logout() {
  auth.logout()
  router.push('/login')
}

onMounted(() => users.fetchUsers())
</script>

<template>
  <div class="space-y-5 px-4 pb-10 pt-6">
    <header class="flex items-center justify-between">
      <div>
        <p class="text-xs uppercase tracking-wide text-secondary">{{ roleLabel }}</p>
        <h1 class="text-2xl font-bold">Users</h1>
      </div>
      <button class="btn btn-ghost btn-sm tap-target" @click="logout">Log out</button>
    </header>

    <!-- Admin section nav -->
    <div role="tablist" class="tabs tabs-boxed bg-base-300/40">
      <RouterLink to="/admin/events" role="tab" class="tab">Events</RouterLink>
      <RouterLink to="/admin/users" role="tab" class="tab tab-active">Users</RouterLink>
      <RouterLink v-if="auth.isAdmin" to="/admin/audit" role="tab" class="tab">Audit</RouterLink>
    </div>

    <AlertMessage type="warning" :message="users.error || ''" />
    <LoadingSpinner v-if="users.loading && !users.loaded" label="Loading users…" />

    <template v-else>
      <!-- Summary -->
      <section class="grid grid-cols-3 gap-3">
        <div class="surface-soft rounded-2xl p-3 text-center">
          <p class="text-2xl font-bold text-secondary">{{ users.adminCount }}</p>
          <p class="text-[0.7rem] uppercase tracking-wide text-base-content/55">Admins</p>
        </div>
        <div class="surface-soft rounded-2xl p-3 text-center">
          <p class="text-2xl font-bold text-accent">{{ users.assistantCount }}</p>
          <p class="text-[0.7rem] uppercase tracking-wide text-base-content/55">Assistants</p>
        </div>
        <div class="surface-soft rounded-2xl p-3 text-center">
          <p class="text-2xl font-bold text-success">{{ users.attendeeCount }}</p>
          <p class="text-[0.7rem] uppercase tracking-wide text-base-content/55">Attendees</p>
        </div>
      </section>

      <!-- User list -->
      <section v-if="sorted.length" class="space-y-3">
        <div
          v-for="u in sorted"
          :key="u.id"
          class="surface p-4"
          :class="u.disabled ? 'opacity-60' : ''"
        >
          <div class="flex items-center gap-3">
            <span class="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-base-300/60 text-sm font-semibold uppercase">
              {{ (u.name || u.email || '?').slice(0, 1) }}
            </span>
            <div class="min-w-0 flex-1">
              <p class="flex items-center gap-2 truncate font-medium">
                {{ [u.name, u.lastname].filter(Boolean).join(' ') || u.email }}
                <span class="badge badge-sm" :class="roleBadgeClass(u.role)">{{ u.role }}</span>
                <span v-if="u.disabled" class="badge badge-sm badge-error">disabled</span>
                <span v-if="isSelf(u)" class="badge badge-sm badge-outline">you</span>
              </p>
              <p class="truncate text-xs text-base-content/55">{{ u.email }}</p>
            </div>
            <div class="shrink-0 text-center">
              <p class="text-lg font-bold text-primary leading-none">{{ u.badges_count ?? 0 }}</p>
              <p class="text-[0.65rem] uppercase tracking-wide text-base-content/45">badges</p>
            </div>
          </div>

          <div class="mt-3 flex flex-col gap-2">
            <RouterLink :to="`/admin/users/${u.id}`" class="btn btn-ghost btn-xs tap-target gap-1 text-primary self-start">
              View progress
              <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 5l7 7-7 7" />
              </svg>
            </RouterLink>
            <!-- Admins can set any role; assistants view only (no control). -->
            <div v-if="auth.isAdmin && !isSelf(u)" class="flex items-center gap-2">
              <span v-if="updatingId === u.id" class="loading loading-spinner loading-xs text-primary" />
              <template v-else>
                <select
                  class="select select-bordered select-xs flex-1 min-w-0 bg-base-100/70"
                  :value="u.role"
                  :disabled="updatingId === u.id"
                  aria-label="Change role"
                  @change="(e) => changeRole(u, e.target.value)"
                >
                  <option value="attendee">Attendee</option>
                  <option value="assistant">Assistant</option>
                  <option value="admin">Admin</option>
                </select>
                <button
                  class="btn btn-xs shrink-0"
                  :class="u.disabled ? 'btn-success' : 'btn-warning'"
                  @click="openConfirm(u.disabled ? 'enable' : 'disable', u)"
                >
                  {{ u.disabled ? 'Enable' : 'Disable' }}
                </button>
                <button
                  class="btn btn-xs btn-error shrink-0"
                  @click="openConfirm('delete', u)"
                >
                  Delete
                </button>
              </template>
            </div>
            <span v-else-if="isSelf(u)" class="text-xs text-base-content/40">your account</span>
          </div>
        </div>
      </section>

      <div v-else class="surface p-8 text-center text-sm text-base-content/60">
        No registered users yet.
      </div>
    </template>

    <!-- Confirmation modal — kept inside the single root div to avoid fragment/transition conflicts -->
    <div v-if="confirmModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
      <div class="surface w-full max-w-sm rounded-2xl p-6 shadow-xl space-y-4">
        <h3 class="text-lg font-bold">
          <span v-if="confirmModal.type === 'delete'">Delete account?</span>
          <span v-else-if="confirmModal.type === 'disable'">Disable account?</span>
          <span v-else>Enable account?</span>
        </h3>
        <p class="text-sm text-base-content/70">
          <template v-if="confirmModal.type === 'delete'">
            This will permanently delete <strong>{{ [confirmModal.user.name, confirmModal.user.lastname].filter(Boolean).join(' ') || confirmModal.user.email }}</strong> and all their data. This cannot be undone.
          </template>
          <template v-else-if="confirmModal.type === 'disable'">
            <strong>{{ [confirmModal.user.name, confirmModal.user.lastname].filter(Boolean).join(' ') || confirmModal.user.email }}</strong> will no longer be able to log in.
          </template>
          <template v-else>
            <strong>{{ [confirmModal.user.name, confirmModal.user.lastname].filter(Boolean).join(' ') || confirmModal.user.email }}</strong> will be able to log in again.
          </template>
        </p>
        <div class="flex justify-end gap-3 pt-1">
          <button class="btn btn-ghost btn-sm" @click="closeConfirm">Cancel</button>
          <button
            class="btn btn-sm"
            :class="confirmModal.type === 'delete' ? 'btn-error' : confirmModal.type === 'disable' ? 'btn-warning' : 'btn-success'"
            @click="confirmAction"
          >
            <span v-if="confirmModal.type === 'delete'">Delete</span>
            <span v-else-if="confirmModal.type === 'disable'">Disable</span>
            <span v-else>Enable</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
