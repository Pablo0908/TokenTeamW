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

// Most-active attendees first so admins can see badge collection at a glance.
const sorted = computed(() =>
  [...users.users].sort((a, b) => (b.badges_count ?? 0) - (a.badges_count ?? 0)),
)

const isSelf = (u) => u.id === auth.user?.id

async function toggleRole(u) {
  const next = u.role === 'admin' ? 'attendee' : 'admin'
  updatingId.value = u.id
  try {
    await users.setRole(u.id, next)
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
        <p class="text-xs uppercase tracking-wide text-secondary">Organizer</p>
        <h1 class="text-2xl font-bold">Users</h1>
      </div>
      <button class="btn btn-ghost btn-sm tap-target" @click="logout">Log out</button>
    </header>

    <!-- Admin section nav -->
    <div role="tablist" class="tabs tabs-boxed bg-base-300/40">
      <RouterLink to="/admin/events" role="tab" class="tab">Events</RouterLink>
      <RouterLink to="/admin/users" role="tab" class="tab tab-active">Users</RouterLink>
    </div>

    <AlertMessage type="warning" :message="users.error || ''" />
    <LoadingSpinner v-if="users.loading && !users.loaded" label="Loading users…" />

    <template v-else>
      <!-- Summary -->
      <section class="grid grid-cols-3 gap-3">
        <div class="surface-soft rounded-2xl p-3 text-center">
          <p class="text-2xl font-bold text-primary">{{ users.users.length }}</p>
          <p class="text-[0.7rem] uppercase tracking-wide text-base-content/55">Users</p>
        </div>
        <div class="surface-soft rounded-2xl p-3 text-center">
          <p class="text-2xl font-bold text-secondary">{{ users.adminCount }}</p>
          <p class="text-[0.7rem] uppercase tracking-wide text-base-content/55">Admins</p>
        </div>
        <div class="surface-soft rounded-2xl p-3 text-center">
          <p class="text-2xl font-bold text-success">{{ users.attendeeCount }}</p>
          <p class="text-[0.7rem] uppercase tracking-wide text-base-content/55">Attendees</p>
        </div>
      </section>

      <!-- User list -->
      <section v-if="sorted.length" class="space-y-3">
        <div v-for="u in sorted" :key="u.id" class="surface p-4">
          <div class="flex items-center gap-3">
            <span class="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-base-300/60 text-sm font-semibold uppercase">
              {{ (u.name || u.email || '?').slice(0, 1) }}
            </span>
            <div class="min-w-0 flex-1">
              <p class="flex items-center gap-2 truncate font-medium">
                {{ [u.name, u.lastname].filter(Boolean).join(' ') || u.email }}
                <span
                  class="badge badge-sm"
                  :class="u.role === 'admin' ? 'badge-secondary' : 'badge-ghost'"
                >{{ u.role }}</span>
                <span v-if="isSelf(u)" class="badge badge-sm badge-outline">you</span>
              </p>
              <p class="truncate text-xs text-base-content/55">{{ u.email }}</p>
            </div>
            <div class="shrink-0 text-center">
              <p class="text-lg font-bold text-primary leading-none">{{ u.badges_count ?? 0 }}</p>
              <p class="text-[0.65rem] uppercase tracking-wide text-base-content/45">badges</p>
            </div>
          </div>

          <div class="mt-3 flex justify-end">
            <button
              class="btn btn-xs tap-target"
              :class="u.role === 'admin' ? 'btn-outline btn-warning' : 'btn-outline btn-secondary'"
              :disabled="isSelf(u) || updatingId === u.id"
              :title="isSelf(u) ? 'You can’t change your own role.' : ''"
              @click="toggleRole(u)"
            >
              <span v-if="updatingId === u.id" class="loading loading-spinner loading-xs" />
              {{ u.role === 'admin' ? 'Demote to attendee' : 'Promote to admin' }}
            </button>
          </div>
        </div>
      </section>

      <div v-else class="surface p-8 text-center text-sm text-base-content/60">
        No registered users yet.
      </div>
    </template>
  </div>
</template>
