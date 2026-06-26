<script setup>
import { onMounted, computed, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUsersStore } from '@/stores/users'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'

const auth = useAuthStore()
const users = useUsersStore()

const updatingId = ref(null)
const confirmModal = ref(null) // { type: 'disable'|'enable'|'delete', user: {...} }

// Most-active attendees first so super admins can see badge collection at a glance.
const sorted = computed(() =>
  [...users.users].sort((a, b) => (b.badges_count ?? 0) - (a.badges_count ?? 0)),
)

// Free-text search over name + email (case-insensitive).
const search = ref('')
const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return sorted.value
  return sorted.value.filter((u) =>
    [u.name, u.lastname, u.email].filter(Boolean).join(' ').toLowerCase().includes(q),
  )
})

const isSelf = (u) => u.id === auth.user?.id

// Grant or revoke platform super-admin. (No global "admin" tier — org admin is per-org.)
async function toggleSuperAdmin(u) {
  updatingId.value = u.id
  try {
    await users.setSuperAdmin(u.id, !u.super_admin)
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

onMounted(() => users.fetchUsers())
</script>

<template>
  <div class="space-y-5">
    <AlertMessage type="warning" :message="users.error || ''" />
    <LoadingSpinner v-if="users.loading && !users.loaded" :label="$t('admin.users.loading')" />

    <template v-else>
      <!-- Summary -->
      <section class="grid grid-cols-2 gap-3">
        <div class="surface-soft rounded-2xl p-3 text-center">
          <p class="text-2xl font-bold text-secondary">{{ users.superAdminCount }}</p>
          <p class="text-[0.7rem] uppercase tracking-wide text-base-content/55">{{ $t('admin.users.superAdmins') }}</p>
        </div>
        <div class="surface-soft rounded-2xl p-3 text-center">
          <p class="text-2xl font-bold text-success">{{ users.attendeeCount }}</p>
          <p class="text-[0.7rem] uppercase tracking-wide text-base-content/55">{{ $t('admin.users.attendees') }}</p>
        </div>
      </section>

      <!-- Search -->
      <input
        v-model="search"
        type="search"
        :placeholder="$t('admin.searchUsers')"
        class="input input-bordered input-sm w-full max-w-md bg-base-100/70"
      />

      <!-- User list -->
      <section v-if="filtered.length" class="grid grid-cols-1 gap-3 lg:grid-cols-2">
        <div
          v-for="u in filtered"
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
                <span v-if="u.super_admin" class="badge badge-sm badge-secondary">{{ $t('roles.superAdmin') }}</span>
                <span v-if="u.disabled" class="badge badge-sm badge-error">{{ $t('admin.users.disabled') }}</span>
                <span v-if="isSelf(u)" class="badge badge-sm badge-outline">{{ $t('admin.users.you') }}</span>
              </p>
              <p class="truncate text-xs text-base-content/55">{{ u.email }}</p>
            </div>
            <div class="shrink-0 text-center">
              <p class="text-lg font-bold text-primary leading-none">{{ u.badges_count ?? 0 }}</p>
              <p class="text-[0.65rem] uppercase tracking-wide text-base-content/45">{{ $t('admin.users.badges') }}</p>
            </div>
          </div>

          <div class="mt-3 flex flex-col gap-2">
            <RouterLink :to="`/admin/users/${u.id}`" class="btn btn-ghost btn-xs tap-target gap-1 text-primary self-start">
              {{ $t('admin.users.viewProgress') }}
              <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 5l7 7-7 7" />
              </svg>
            </RouterLink>
            <!-- Super admins manage the platform tier (grant/revoke) + account status. -->
            <div v-if="!isSelf(u)" class="flex flex-wrap items-center gap-2">
              <span v-if="updatingId === u.id" class="loading loading-spinner loading-xs text-primary" />
              <template v-else>
                <button
                  class="btn btn-xs shrink-0"
                  :class="u.super_admin ? 'btn-outline' : 'btn-secondary'"
                  @click="toggleSuperAdmin(u)"
                >
                  {{ u.super_admin ? $t('admin.users.revokeSuperAdmin') : $t('admin.users.makeSuperAdmin') }}
                </button>
                <button
                  class="btn btn-xs shrink-0"
                  :class="u.disabled ? 'btn-success' : 'btn-warning'"
                  @click="openConfirm(u.disabled ? 'enable' : 'disable', u)"
                >
                  {{ u.disabled ? $t('admin.users.enable') : $t('admin.users.disable') }}
                </button>
                <button
                  class="btn btn-xs btn-error shrink-0"
                  @click="openConfirm('delete', u)"
                >
                  {{ $t('admin.users.delete') }}
                </button>
              </template>
            </div>
            <span v-else-if="isSelf(u)" class="text-xs text-base-content/40">{{ $t('admin.users.yourAccount') }}</span>
          </div>
        </div>
      </section>

      <div v-else class="surface p-8 text-center text-sm text-base-content/60">
        {{ $t('admin.users.noneYet') }}
      </div>
    </template>

    <!-- Confirmation modal — kept inside the single root div to avoid fragment/transition conflicts -->
    <div v-if="confirmModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
      <div class="surface w-full max-w-sm rounded-2xl p-6 shadow-xl space-y-4">
        <h3 class="text-lg font-bold">
          <span v-if="confirmModal.type === 'delete'">{{ $t('admin.users.deleteTitle') }}</span>
          <span v-else-if="confirmModal.type === 'disable'">{{ $t('admin.users.disableTitle') }}</span>
          <span v-else>{{ $t('admin.users.enableTitle') }}</span>
        </h3>
        <!-- eslint-disable-next-line vue/no-v-html -->
        <p
          class="text-sm text-base-content/70"
          v-html="$t(
            confirmModal.type === 'delete' ? 'admin.users.deleteMsg' : confirmModal.type === 'disable' ? 'admin.users.disableMsg' : 'admin.users.enableMsg',
            { name: `<strong>${[confirmModal.user.name, confirmModal.user.lastname].filter(Boolean).join(' ') || confirmModal.user.email}</strong>` },
          )"
        />
        <div class="flex justify-end gap-3 pt-1">
          <button class="btn btn-ghost btn-sm" @click="closeConfirm">{{ $t('common.cancel') }}</button>
          <button
            class="btn btn-sm"
            :class="confirmModal.type === 'delete' ? 'btn-error' : confirmModal.type === 'disable' ? 'btn-warning' : 'btn-success'"
            @click="confirmAction"
          >
            <span v-if="confirmModal.type === 'delete'">{{ $t('admin.users.delete') }}</span>
            <span v-else-if="confirmModal.type === 'disable'">{{ $t('admin.users.disable') }}</span>
            <span v-else>{{ $t('admin.users.enable') }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
