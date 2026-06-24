<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/services/api'
import AlertMessage from '@/components/ui/AlertMessage.vue'

const router = useRouter()
const auth = useAuthStore()

// ---------- Name ----------
const form = reactive({
  name: auth.user?.name ?? '',
  lastname: auth.user?.lastname ?? '',
})
const saving = ref(false)
const nameError = ref('')
const nameSuccess = ref(false)

async function saveName() {
  if (!form.name.trim()) { nameError.value = 'First name is required.'; return }
  saving.value = true
  nameError.value = ''
  nameSuccess.value = false
  try {
    const { data } = await api.patch('/me/profile', {
      name: form.name.trim(),
      lastname: form.lastname.trim(),
    })
    auth.updateUser({ name: data.name, lastname: data.lastname })
    nameSuccess.value = true
    setTimeout(() => router.back(), 900)
  } catch (e) {
    nameError.value = e.response?.data?.error ?? 'Could not save changes.'
  } finally {
    saving.value = false
  }
}

// ---------- Avatar ----------
// photoTab: 'upload' | 'url'
const photoTab = ref('upload')
const photoOpen = ref(false)
const avatarPreview = ref(auth.user?.avatar_url ?? null)
const urlInput = ref('')
const photoError = ref('')
const photoSaving = ref(false)
const photoSuccess = ref(false)

const initials = computed(() => {
  const n = form.name || auth.user?.name || ''
  const l = form.lastname || auth.user?.lastname || ''
  return ((n[0] ?? '') + (l[0] ?? '')).toUpperCase() || (auth.user?.email?.[0] ?? 'U').toUpperCase()
})

function openPhoto() {
  photoOpen.value = true
  photoError.value = ''
  urlInput.value = ''
}

function cancelPhoto() {
  photoOpen.value = false
  avatarPreview.value = auth.user?.avatar_url ?? null
  urlInput.value = ''
  photoError.value = ''
}

function onFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (file.size > 1_000_000) {
    photoError.value = 'Image must be under 1 MB.'
    return
  }
  photoError.value = ''
  const reader = new FileReader()
  reader.onload = (ev) => { avatarPreview.value = ev.target.result }
  reader.readAsDataURL(file)
}

function applyUrl() {
  const u = urlInput.value.trim()
  if (u) avatarPreview.value = u
}

async function savePhoto() {
  photoSaving.value = true
  photoError.value = ''
  photoSuccess.value = false
  try {
    const { data } = await api.patch('/me/avatar', { avatar_url: avatarPreview.value ?? '' })
    auth.updateUser({ avatar_url: data.avatar_url })
    photoOpen.value = false
    photoSuccess.value = true
  } catch (e) {
    photoError.value = e.response?.data?.error ?? 'Could not save photo.'
  } finally {
    photoSaving.value = false
  }
}

async function removePhoto() {
  photoSaving.value = true
  photoError.value = ''
  try {
    await api.patch('/me/avatar', { avatar_url: '' })
    auth.updateUser({ avatar_url: null })
    avatarPreview.value = null
    photoOpen.value = false
  } catch (e) {
    photoError.value = e.response?.data?.error ?? 'Could not remove photo.'
  } finally {
    photoSaving.value = false
  }
}
</script>

<template>
  <div class="space-y-6 px-4 pb-4 pt-6">
    <header class="flex items-center gap-3">
      <button type="button" class="tap-target -ml-2 grid h-10 w-10 place-items-center rounded-2xl transition-colors hover:bg-base-300/40" @click="router.back()">
        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M15 18l-6-6 6-6"/>
        </svg>
      </button>
      <h1 class="text-xl font-bold">{{ $t('settings.editProfileTitle') }}</h1>
    </header>

    <!-- Avatar section -->
    <div class="surface space-y-4 p-4">
      <div class="flex flex-col items-center gap-3">
        <!-- Avatar preview -->
        <span class="relative h-20 w-20">
          <img
            v-if="avatarPreview"
            :src="avatarPreview"
            class="h-20 w-20 rounded-full object-cover ring-2 ring-primary/30"
            alt=""
          />
          <span
            v-else
            class="grid h-20 w-20 place-items-center rounded-full bg-gradient-to-br from-primary to-secondary text-2xl font-bold text-primary-content"
          >{{ initials }}</span>
        </span>

        <AlertMessage v-if="photoSuccess" type="success" :message="$t('settings.photoSaved')" />

        <!-- Change / Remove buttons when not editing -->
        <div v-if="!photoOpen" class="flex gap-2">
          <button type="button" class="btn btn-outline btn-sm tap-target" @click="openPhoto">
            {{ $t('settings.changePhoto') }}
          </button>
          <button
            v-if="auth.user?.avatar_url"
            type="button"
            class="btn btn-ghost btn-sm text-error tap-target"
            :disabled="photoSaving"
            @click="removePhoto"
          >
            {{ $t('settings.removePhoto') }}
          </button>
        </div>
      </div>

      <!-- Photo editor panel -->
      <div v-if="photoOpen" class="space-y-3">
        <AlertMessage type="error" :message="photoError" />

        <!-- Tabs: upload vs URL -->
        <div class="surface-soft flex gap-1 rounded-xl p-1">
          <button
            type="button"
            class="flex-1 rounded-lg py-2 text-sm font-medium transition-colors tap-target"
            :class="photoTab === 'upload' ? 'bg-primary text-primary-content' : 'text-base-content/60'"
            @click="photoTab = 'upload'"
          >{{ $t('settings.uploadPhoto') }}</button>
          <button
            type="button"
            class="flex-1 rounded-lg py-2 text-sm font-medium transition-colors tap-target"
            :class="photoTab === 'url' ? 'bg-primary text-primary-content' : 'text-base-content/60'"
            @click="photoTab = 'url'"
          >{{ $t('settings.photoUrl') }}</button>
        </div>

        <!-- File upload -->
        <label v-if="photoTab === 'upload'" class="flex cursor-pointer flex-col items-center gap-2 rounded-2xl border-2 border-dashed border-base-300 p-5 transition-colors hover:border-primary/50">
          <svg class="h-8 w-8 text-base-content/40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
          </svg>
          <span class="text-sm text-base-content/60">Tap to choose a PNG or JPG</span>
          <span class="text-xs text-base-content/40">Max 1 MB</span>
          <input type="file" accept="image/*" class="hidden" @change="onFileChange" />
        </label>

        <!-- URL input -->
        <div v-else class="flex gap-2">
          <input
            v-model="urlInput"
            type="url"
            inputmode="url"
            :placeholder="$t('settings.photoUrlPlaceholder')"
            class="input input-bordered flex-1 bg-base-100/70 text-sm"
          />
          <button type="button" class="btn btn-outline btn-sm tap-target" @click="applyUrl">Preview</button>
        </div>

        <!-- Save / Cancel -->
        <div class="flex gap-2">
          <button
            type="button"
            class="btn btn-primary flex-1 tap-target"
            :disabled="photoSaving || !avatarPreview"
            @click="savePhoto"
          >
            <span v-if="photoSaving" class="loading loading-spinner loading-sm" />
            {{ $t('settings.savePhoto') }}
          </button>
          <button type="button" class="btn btn-ghost tap-target" @click="cancelPhoto">
            {{ $t('common.cancel') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Name form -->
    <form class="surface space-y-4 p-4" novalidate @submit.prevent="saveName">
      <AlertMessage type="error" :message="nameError" />
      <AlertMessage v-if="nameSuccess" type="success" message="Profile updated!" />

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">{{ $t('auth.firstName') }}</span>
        <input
          v-model="form.name"
          type="text"
          autocomplete="given-name"
          class="input input-bordered w-full bg-base-100/70"
        />
      </label>

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">{{ $t('auth.lastName') }}</span>
        <input
          v-model="form.lastname"
          type="text"
          autocomplete="family-name"
          class="input input-bordered w-full bg-base-100/70"
        />
      </label>

      <button type="submit" class="btn btn-primary w-full tap-target" :disabled="saving">
        <span v-if="saving" class="loading loading-spinner loading-sm" />
        {{ saving ? $t('profile.saving') : $t('profile.saveProfile') }}
      </button>
    </form>
  </div>
</template>
