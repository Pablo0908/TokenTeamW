<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { locale, setLocale } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import { useBadgesStore } from '@/stores/badges'
import { useSettingsStore, SATURATION_RANGE, CONTRAST_RANGE } from '@/stores/settings'
import { api } from '@/services/api'
import StatTile from '@/components/domain/StatTile.vue'
import ProgressBar from '@/components/domain/ProgressBar.vue'

const router = useRouter()
const auth = useAuthStore()
const badges = useBadgesStore()
const settings = useSettingsStore()

// ── Display ──────────────────────────────────────────────────────────────────

const initials = computed(() => {
  const n = auth.user?.name ?? ''
  const l = auth.user?.lastname ?? ''
  return ((n[0] ?? '') + (l[0] ?? '')).toUpperCase() || (auth.user?.email?.[0] ?? 'U').toUpperCase()
})
const fullName = computed(() =>
  [auth.user?.name, auth.user?.lastname].filter(Boolean).join(' ') || auth.displayName,
)
const pinnedBadgeIds = computed(() => auth.user?.pinned_badges ?? [])
const pinnedBadges = computed(() =>
  pinnedBadgeIds.value.map((id) => badges.earnedBadges.find((b) => b.id === id)).filter(Boolean),
)

// ── Edit mode ─────────────────────────────────────────────────────────────────

const editing = ref(false)
const saving = ref(false)
const editError = ref('')
const form = ref({ name: '', lastname: '', username: '', bio: '', avatar: null })
const previewAvatar = ref(null)
const usernameStatus = ref(null) // null | 'checking' | 'available' | 'taken' | 'invalid'

function startEdit() {
  form.value = {
    name: auth.user?.name ?? '',
    lastname: auth.user?.lastname ?? '',
    username: auth.user?.username ?? '',
    bio: auth.user?.bio ?? '',
    avatar: null,
  }
  if (previewAvatar.value) { URL.revokeObjectURL(previewAvatar.value); previewAvatar.value = null }
  editError.value = ''
  usernameStatus.value = null
  editing.value = true
}

function cancelEdit() {
  if (previewAvatar.value) { URL.revokeObjectURL(previewAvatar.value); previewAvatar.value = null }
  editing.value = false
}

// ── Avatar upload + Canvas resize ─────────────────────────────────────────────

const fileInput = ref(null)

function pickAvatar() { fileInput.value?.click() }

async function onFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) { editError.value = 'Select an image file.'; return }
  editError.value = ''
  if (previewAvatar.value) URL.revokeObjectURL(previewAvatar.value)
  previewAvatar.value = URL.createObjectURL(file)
  form.value.avatar = await resizeImage(file, 200, 200, 0.85)
  e.target.value = ''
}

function resizeImage(file, maxW, maxH, quality) {
  return new Promise((resolve) => {
    const reader = new FileReader()
    reader.onload = (ev) => {
      const img = new Image()
      img.onload = () => {
        const scale = Math.min(maxW / img.width, maxH / img.height, 1)
        const canvas = document.createElement('canvas')
        canvas.width = Math.round(img.width * scale)
        canvas.height = Math.round(img.height * scale)
        canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height)
        resolve(canvas.toDataURL('image/jpeg', quality))
      }
      img.src = ev.target.result
    }
    reader.readAsDataURL(file)
  })
}

// ── Username availability (debounced 500 ms) ──────────────────────────────────

let _unTimer = null

watch(() => form.value.username, (val) => {
  clearTimeout(_unTimer)
  const current = (auth.user?.username ?? '').toLowerCase()
  if (!val || val.toLowerCase() === current) { usernameStatus.value = null; return }
  if (!/^[a-zA-Z0-9_]{3,20}$/.test(val)) { usernameStatus.value = 'invalid'; return }
  usernameStatus.value = 'checking'
  _unTimer = setTimeout(async () => {
    try {
      const { data } = await api.get(`/me/check-username?u=${encodeURIComponent(val)}`)
      usernameStatus.value = data.available ? 'available' : 'taken'
    } catch { usernameStatus.value = null }
  }, 500)
})

const canSave = computed(
  () => usernameStatus.value !== 'taken' && usernameStatus.value !== 'invalid' && usernameStatus.value !== 'checking',
)

// ── Save profile ──────────────────────────────────────────────────────────────

async function saveProfile() {
  if (!canSave.value) return
  saving.value = true
  editError.value = ''
  const payload = {
    name: form.value.name,
    lastname: form.value.lastname,
    username: form.value.username,
    bio: form.value.bio,
  }
  if (form.value.avatar) payload.avatar = form.value.avatar
  const ok = await auth.updateProfile(payload)
  saving.value = false
  if (ok) {
    if (previewAvatar.value) { URL.revokeObjectURL(previewAvatar.value); previewAvatar.value = null }
    editing.value = false
  } else {
    editError.value = auth.error || 'Failed to save.'
  }
}

// ── Pinned badges modal ───────────────────────────────────────────────────────

const selectedPins = ref([])

function openPinModal() {
  selectedPins.value = [...pinnedBadgeIds.value]
  document.getElementById('modal-pins')?.showModal()
}

function togglePin(id) {
  const i = selectedPins.value.indexOf(id)
  if (i >= 0) selectedPins.value.splice(i, 1)
  else if (selectedPins.value.length < 4) selectedPins.value.push(id)
}

async function savePins() {
  document.getElementById('modal-pins')?.close()
  await auth.updatePinnedBadges(selectedPins.value)
}

// ── Init ──────────────────────────────────────────────────────────────────────

onMounted(async () => {
  if (!badges.loaded) badges.fetchMyBadges()
  // Fetch latest profile data (avatar, username, bio, pinned_badges).
  await auth.loadProfile()
})

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div>
  <div class="space-y-6 px-4 pb-4 pt-6">

    <!-- ── Header: view mode ─────────────────────────────────────────────── -->
    <header v-if="!editing" class="flex flex-col items-center gap-3 pt-2 text-center">
      <!-- Avatar -->
      <div class="relative">
        <img
          v-if="auth.user?.avatar"
          :src="auth.user.avatar"
          alt="avatar"
          class="h-20 w-20 rounded-full object-cover ring-2 ring-primary/40"
        />
        <span
          v-else
          class="grid h-20 w-20 place-items-center rounded-full bg-gradient-to-br from-primary to-secondary text-2xl font-bold text-primary-content"
        >
          {{ initials }}
        </span>
      </div>

      <div class="space-y-1">
        <h1 class="text-xl font-bold">{{ fullName }}</h1>
        <p v-if="auth.user?.username" class="text-sm font-medium text-primary">@{{ auth.user.username }}</p>
        <p class="text-xs text-base-content/50">{{ auth.user?.email }}</p>
        <p v-if="auth.user?.bio" class="mx-auto mt-1 max-w-xs text-sm text-base-content/70">{{ auth.user.bio }}</p>
        <span
          class="badge badge-sm mt-2 border-0"
          :class="auth.isAdmin ? 'badge-secondary' : auth.isAssistant ? 'badge-accent' : 'badge-primary'"
        >
          {{ auth.isAdmin ? $t('profile.organizer') : auth.isAssistant ? $t('profile.assistant') : $t('profile.attendee') }}
        </span>
      </div>

      <button class="btn btn-outline btn-sm tap-target" @click="startEdit">
        {{ $t('profile.editProfile') }}
      </button>
    </header>

    <!-- ── Header: edit mode ─────────────────────────────────────────────── -->
    <section v-else class="space-y-4 rounded-2xl border border-base-300/50 bg-base-100/40 p-4">
      <!-- Avatar picker -->
      <div class="flex flex-col items-center gap-2">
        <button type="button" class="relative tap-target" @click="pickAvatar">
          <img
            v-if="previewAvatar || auth.user?.avatar"
            :src="previewAvatar || auth.user?.avatar"
            alt="avatar"
            class="h-20 w-20 rounded-full object-cover ring-2 ring-primary/40"
          />
          <span
            v-else
            class="grid h-20 w-20 place-items-center rounded-full bg-gradient-to-br from-primary to-secondary text-2xl font-bold text-primary-content"
          >{{ initials }}</span>
          <span class="absolute bottom-0 right-0 flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs text-primary-content shadow">
            <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4 12.5-12.5z"/></svg>
          </span>
        </button>
        <span class="text-xs text-base-content/50">{{ $t('profile.changePhoto') }}</span>
        <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onFileChange" />
      </div>

      <!-- Name -->
      <div class="flex gap-3">
        <label class="form-control flex-1">
          <span class="label-text mb-1 text-xs text-base-content/60">{{ $t('auth.firstName') }}</span>
          <input v-model="form.name" type="text" class="input input-bordered input-sm w-full bg-base-100/70" />
        </label>
        <label class="form-control flex-1">
          <span class="label-text mb-1 text-xs text-base-content/60">{{ $t('auth.lastName') }}</span>
          <input v-model="form.lastname" type="text" class="input input-bordered input-sm w-full bg-base-100/70" />
        </label>
      </div>

      <!-- Username -->
      <label class="form-control w-full">
        <span class="label-text mb-1 text-xs text-base-content/60">{{ $t('profile.username') }}</span>
        <div class="relative">
          <span class="pointer-events-none absolute inset-y-0 left-3 flex items-center text-base-content/40">@</span>
          <input
            v-model="form.username"
            type="text"
            maxlength="20"
            :placeholder="$t('profile.usernamePlaceholder')"
            class="input input-bordered input-sm w-full bg-base-100/70 pl-7"
            :class="{
              'input-error': usernameStatus === 'taken' || usernameStatus === 'invalid',
              'input-success': usernameStatus === 'available',
            }"
          />
          <span class="absolute inset-y-0 right-3 flex items-center text-xs">
            <span v-if="usernameStatus === 'checking'" class="loading loading-spinner loading-xs text-base-content/40" />
            <span v-else-if="usernameStatus === 'available'" class="text-success">{{ $t('profile.usernameAvailable') }}</span>
            <span v-else-if="usernameStatus === 'taken'" class="text-error">{{ $t('profile.usernameTaken') }}</span>
            <span v-else-if="usernameStatus === 'invalid'" class="text-error">{{ $t('profile.usernameInvalid') }}</span>
          </span>
        </div>
        <span class="mt-1 text-xs text-base-content/40">{{ $t('profile.usernameHint') }}</span>
      </label>

      <!-- Bio -->
      <label class="form-control w-full">
        <div class="mb-1 flex items-center justify-between">
          <span class="label-text text-xs text-base-content/60">{{ $t('profile.bio') }}</span>
          <span class="text-xs text-base-content/40">{{ $t('profile.bioLimit').replace('{n}', form.bio.length) }}</span>
        </div>
        <textarea
          v-model="form.bio"
          maxlength="160"
          rows="2"
          :placeholder="$t('profile.bioPlaceholder')"
          class="textarea textarea-bordered w-full bg-base-100/70 text-sm"
        />
      </label>

      <p v-if="editError" class="text-xs text-error">{{ editError }}</p>

      <!-- Actions -->
      <div class="flex gap-2">
        <button class="btn btn-ghost btn-sm flex-1 tap-target" @click="cancelEdit">{{ $t('profile.cancelEdit') }}</button>
        <button
          class="btn btn-primary btn-sm flex-1 tap-target"
          :disabled="!canSave || saving"
          @click="saveProfile"
        >
          <span v-if="saving" class="loading loading-spinner loading-xs" />
          {{ saving ? $t('profile.saving') : $t('profile.saveProfile') }}
        </button>
      </div>
    </section>

    <!-- ── Stats ─────────────────────────────────────────────────────────── -->
    <section class="grid grid-cols-3 gap-3">
      <StatTile :value="badges.totalEarned" :label="$t('profile.badges')" tone="primary" />
      <StatTile :value="badges.eventsCount" :label="$t('profile.events')" tone="secondary" />
      <StatTile :value="badges.completedEvents" :label="$t('profile.done')" tone="accent" />
    </section>

    <!-- ── Pinned badges ──────────────────────────────────────────────────── -->
    <section v-if="!editing" class="space-y-2">
      <div class="flex items-center justify-between">
        <h2 class="font-semibold">{{ $t('profile.pinnedBadges') }}</h2>
        <button
          v-if="badges.earnedBadges.length"
          class="btn btn-ghost btn-xs tap-target text-primary"
          @click="openPinModal"
        >
          {{ $t('profile.managePins') }}
        </button>
      </div>

      <div v-if="pinnedBadges.length" class="grid grid-cols-4 gap-2">
        <div
          v-for="b in pinnedBadges"
          :key="b.id"
          class="surface flex flex-col items-center gap-1 p-2 text-center"
        >
          <span class="text-2xl leading-none">{{ b.icon }}</span>
          <span class="line-clamp-2 text-[0.65rem] leading-tight text-base-content/70">{{ b.name }}</span>
        </div>
      </div>

      <div v-else class="surface p-4 text-center text-xs text-base-content/50">
        {{ badges.earnedBadges.length ? $t('profile.noPins') : $t('profile.noEarned') }}
        <p v-if="badges.earnedBadges.length" class="mt-0.5">{{ $t('profile.pinHint') }}</p>
      </div>
    </section>

    <!-- ── Progress by event ──────────────────────────────────────────────── -->
    <section v-if="badges.groups.length" class="space-y-3">
      <h2 class="font-semibold">{{ $t('profile.progressByEvent') }}</h2>
      <div class="surface space-y-4 p-4">
        <div v-for="g in badges.groups" :key="g.event_id" class="space-y-1.5">
          <div class="flex items-center justify-between text-sm">
            <span class="truncate">{{ g.event }}</span>
            <span class="text-base-content/55">{{ g.badges_earned }}/{{ g.badges_total }}</span>
          </div>
          <ProgressBar :value="g.badges_earned" :max="g.badges_total" :show-count="false" />
        </div>
      </div>
    </section>

    <!-- ── Settings ───────────────────────────────────────────────────────── -->
    <section class="space-y-3">
      <h2 class="font-semibold">{{ $t('settings.title') }}</h2>
      <div class="surface space-y-5 p-4">
        <div class="space-y-2">
          <span class="text-sm font-medium">{{ $t('settings.language') }}</span>
          <div class="surface-soft flex gap-2 p-1.5">
            <button
              type="button"
              class="tap-target flex-1 rounded-xl py-2 text-sm font-medium transition-colors"
              :class="locale === 'en' ? 'bg-primary text-primary-content' : 'text-base-content/60'"
              @click="setLocale('en')"
            >English</button>
            <button
              type="button"
              class="tap-target flex-1 rounded-xl py-2 text-sm font-medium transition-colors"
              :class="locale === 'es' ? 'bg-primary text-primary-content' : 'text-base-content/60'"
              @click="setLocale('es')"
            >Español</button>
          </div>
        </div>

        <label class="flex cursor-pointer items-center justify-between gap-3">
          <span>
            <span class="block text-sm font-medium">{{ $t('settings.lightMode') }}</span>
            <span class="block text-xs text-base-content/55">{{ $t('settings.lightModeHint') }}</span>
          </span>
          <input v-model="settings.lightMode" type="checkbox" class="toggle toggle-primary" />
        </label>

        <label class="flex cursor-pointer items-center justify-between gap-3">
          <span>
            <span class="block text-sm font-medium">{{ $t('settings.effects') }}</span>
            <span class="block text-xs text-base-content/55">{{ $t('settings.effectsHint') }}</span>
          </span>
          <input v-model="settings.effects" type="checkbox" class="toggle toggle-primary" />
        </label>

        <div class="space-y-1.5">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium">{{ $t('settings.saturation') }}</span>
            <span class="text-xs tabular-nums text-base-content/55">{{ Math.round(settings.saturation * 100) }}%</span>
          </div>
          <input v-model.number="settings.saturation" type="range" class="range range-primary range-sm"
            :min="SATURATION_RANGE.min" :max="SATURATION_RANGE.max" :step="SATURATION_RANGE.step" />
        </div>

        <div class="space-y-1.5">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium">{{ $t('settings.contrast') }}</span>
            <span class="text-xs tabular-nums text-base-content/55">{{ Math.round(settings.contrast * 100) }}%</span>
          </div>
          <input v-model.number="settings.contrast" type="range" class="range range-primary range-sm"
            :min="CONTRAST_RANGE.min" :max="CONTRAST_RANGE.max" :step="CONTRAST_RANGE.step" />
        </div>

        <div class="border-t border-base-300/60 pt-4">
          <button type="button" class="btn btn-outline btn-primary w-full tap-target" @click="settings.reset()">
            {{ $t('settings.reset') }}
          </button>
        </div>
      </div>
    </section>

    <RouterLink v-if="auth.isStaff" to="/admin/events" class="btn btn-outline w-full tap-target">
      {{ $t('profile.openAdmin') }}
    </RouterLink>

    <button class="btn btn-ghost w-full text-error tap-target" @click="logout">{{ $t('common.logout') }}</button>
  </div>

  <!-- ── Pin badges modal ───────────────────────────────────────────────── -->
  <dialog id="modal-pins" class="modal">
    <div class="modal-box max-h-[80vh]">
      <h3 class="text-lg font-bold">{{ $t('profile.pinnedBadges') }}</h3>
      <p class="mt-1 text-xs text-base-content/55">{{ $t('profile.pinHint') }}</p>

      <div class="mt-4 grid grid-cols-3 gap-2 overflow-y-auto">
        <button
          v-for="b in badges.earnedBadges"
          :key="b.id"
          type="button"
          class="surface flex flex-col items-center gap-1 p-2 text-center transition-all tap-target"
          :class="selectedPins.includes(b.id) ? 'ring-2 ring-primary' : (!selectedPins.includes(b.id) && selectedPins.length >= 4 ? 'opacity-40' : '')"
          @click="togglePin(b.id)"
        >
          <span class="text-2xl leading-none">{{ b.icon }}</span>
          <span class="line-clamp-2 text-[0.65rem] leading-tight">{{ b.name }}</span>
          <span v-if="selectedPins.includes(b.id)" class="text-[0.6rem] font-semibold text-primary">✓</span>
        </button>
      </div>

      <div class="modal-action">
        <form method="dialog">
          <button class="btn btn-ghost btn-sm">{{ $t('common.cancel') }}</button>
        </form>
        <button class="btn btn-primary btn-sm" @click="savePins">{{ $t('profile.saveProfile') }}</button>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop"><button>close</button></form>
  </dialog>
  </div>
</template>
