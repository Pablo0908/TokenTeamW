<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/services/api'
import AlertMessage from '@/components/ui/AlertMessage.vue'

const router = useRouter()
const auth = useAuthStore()

const form = reactive({
  name: auth.user?.name ?? '',
  lastname: auth.user?.lastname ?? '',
})
const saving = ref(false)
const error = ref('')
const success = ref(false)

async function save() {
  if (!form.name.trim()) {
    error.value = 'First name is required.'
    return
  }
  saving.value = true
  error.value = ''
  success.value = false
  try {
    const { data } = await api.patch('/me/profile', {
      name: form.name.trim(),
      lastname: form.lastname.trim(),
    })
    auth.updateUser({ name: data.name, lastname: data.lastname })
    success.value = true
    setTimeout(() => router.back(), 900)
  } catch (e) {
    error.value = e.response?.data?.error ?? 'Could not save changes.'
  } finally {
    saving.value = false
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

    <form class="surface space-y-4 p-4" novalidate @submit.prevent="save">
      <AlertMessage type="error" :message="error" />
      <AlertMessage v-if="success" type="success" message="Profile updated!" />

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
