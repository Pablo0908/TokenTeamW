<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/services/api'
import AlertMessage from '@/components/ui/AlertMessage.vue'

const router = useRouter()
const auth = useAuthStore()

const photoTab = ref('upload')
const preview = ref(auth.user?.avatar_url ?? null)
const urlInput = ref('')
const error = ref('')
const saving = ref(false)
const success = ref(false)

function onFileChange(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (file.size > 1_000_000) { error.value = 'Image must be under 1 MB.'; return }
  error.value = ''
  const reader = new FileReader()
  reader.onload = (ev) => { preview.value = ev.target.result }
  reader.readAsDataURL(file)
}

function applyUrl() {
  const u = urlInput.value.trim()
  if (u) { preview.value = u; error.value = '' }
}

async function save() {
  saving.value = true
  error.value = ''
  success.value = false
  try {
    const { data } = await api.patch('/me/avatar', { avatar_url: preview.value ?? '' })
    auth.updateUser({ avatar_url: data.avatar_url })
    success.value = true
    setTimeout(() => router.back(), 800)
  } catch (e) {
    error.value = e.response?.data?.error ?? 'Could not save photo.'
  } finally {
    saving.value = false
  }
}

async function remove() {
  saving.value = true
  error.value = ''
  try {
    await api.patch('/me/avatar', { avatar_url: '' })
    auth.updateUser({ avatar_url: null })
    preview.value = null
    success.value = true
    setTimeout(() => router.back(), 800)
  } catch (e) {
    error.value = e.response?.data?.error ?? 'Could not remove photo.'
  } finally {
    saving.value = false
  }
}

const initials = (() => {
  const n = auth.user?.name ?? ''
  const l = auth.user?.lastname ?? ''
  return ((n[0] ?? '') + (l[0] ?? '')).toUpperCase() || (auth.user?.email?.[0] ?? 'U').toUpperCase()
})()
</script>

<template>
  <div class="space-y-6 px-4 pb-4 pt-6">
    <header class="flex items-center gap-3">
      <button type="button" class="tap-target -ml-2 grid h-10 w-10 place-items-center rounded-2xl transition-colors hover:bg-base-300/40" @click="router.back()">
        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M15 18l-6-6 6-6"/>
        </svg>
      </button>
      <h1 class="text-xl font-bold">{{ $t('settings.changePhoto') }}</h1>
    </header>

    <div class="surface space-y-5 p-4">
      <!-- Current / preview avatar -->
      <div class="flex flex-col items-center gap-2">
        <span class="relative h-24 w-24">
          <img v-if="preview" :src="preview" class="h-24 w-24 rounded-full object-cover ring-2 ring-primary/30" alt="" />
          <span v-else class="grid h-24 w-24 place-items-center rounded-full bg-gradient-to-br from-primary to-secondary text-3xl font-bold text-primary-content">
            {{ initials }}
          </span>
        </span>
        <AlertMessage v-if="success" type="success" :message="$t('settings.photoSaved')" />
      </div>

      <AlertMessage type="error" :message="error" />

      <!-- Tabs -->
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
      <label v-if="photoTab === 'upload'" class="flex cursor-pointer flex-col items-center gap-2 rounded-2xl border-2 border-dashed border-base-300 p-6 transition-colors hover:border-primary/50">
        <svg class="h-9 w-9 text-base-content/35" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
        </svg>
        <span class="text-sm font-medium">{{ $t('settings.photoTapChoose') }}</span>
        <span class="text-xs text-base-content/40">{{ $t('settings.photoFormatHint') }}</span>
        <input type="file" accept="image/*" class="hidden" @change="onFileChange" />
      </label>

      <!-- URL input -->
      <div v-else class="space-y-2">
        <div class="flex gap-2">
          <input
            v-model="urlInput"
            type="url"
            inputmode="url"
            :placeholder="$t('settings.photoUrlPlaceholder')"
            class="input input-bordered flex-1 bg-base-100/70 text-sm"
          />
          <button type="button" class="btn btn-outline btn-sm tap-target" @click="applyUrl">{{ $t('settings.photoPreview') }}</button>
        </div>
      </div>

      <!-- Actions -->
      <button
        type="button"
        class="btn btn-primary w-full tap-target"
        :disabled="saving || !preview"
        @click="save"
      >
        <span v-if="saving" class="loading loading-spinner loading-sm" />
        {{ $t('settings.savePhoto') }}
      </button>

      <button
        v-if="auth.user?.avatar_url"
        type="button"
        class="btn btn-ghost w-full text-error tap-target"
        :disabled="saving"
        @click="remove"
      >
        {{ $t('settings.removePhoto') }}
      </button>
    </div>
  </div>
</template>
