<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/services/api'
import AlertMessage from '@/components/ui/AlertMessage.vue'
import PasswordInput from '@/components/ui/PasswordInput.vue'

const router = useRouter()
const auth = useAuthStore()

const step = ref('email') // 'email' | 'code'
const form = reactive({ email: '', code: '', newPwd: '', confirm: '' })
const emailTouched = ref(false)
const codeTouched = ref(false)
const loading = ref(false)
const error = ref('')
const success = ref(false)

const emailValid = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))

const pwdRules = computed(() => [
  { key: 'pwdLen',     ok: form.newPwd.length >= 8 },
  { key: 'pwdUpper',  ok: /[A-Z]/.test(form.newPwd) },
  { key: 'pwdLower',  ok: /[a-z]/.test(form.newPwd) },
  { key: 'pwdNumber', ok: /\d/.test(form.newPwd) },
  { key: 'pwdSpecial',ok: /[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?`~]/.test(form.newPwd) },
])
const pwdValid = computed(() => pwdRules.value.every(r => r.ok))
const pwdsMatch = computed(() => form.newPwd === form.confirm)

function reset() {
  step.value = 'email'
  form.email = ''
  form.code = ''
  form.newPwd = ''
  form.confirm = ''
  emailTouched.value = false
  codeTouched.value = false
  error.value = ''
  success.value = false
}

async function sendCode() {
  emailTouched.value = true
  if (!emailValid.value) return
  loading.value = true
  error.value = ''
  try {
    await api.post('/me/password/send-code', { email: form.email.trim().toLowerCase() })
    step.value = 'code'
  } catch (e) {
    error.value = e.response?.data?.error ?? 'Unexpected error.'
  } finally {
    loading.value = false
  }
}

async function submit() {
  codeTouched.value = true
  if (!form.code.trim() || !pwdValid.value || !pwdsMatch.value) return
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.put('/me/password', {
      email: form.email.trim().toLowerCase(),
      code: form.code.trim(),
      new_password: form.newPwd,
    })
    // The change revoked old sessions; keep this device signed in with the fresh token.
    if (data?.token) auth.setToken(data.token)
    success.value = true
    setTimeout(() => router.replace('/profile/settings'), 1500)
  } catch (e) {
    error.value = e.response?.data?.error ?? 'Unexpected error.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="mx-auto w-full max-w-md space-y-6 px-4 pb-4 pt-6 lg:px-8">
    <header class="flex items-center gap-3">
      <button type="button" class="tap-target -ml-2 grid h-10 w-10 place-items-center rounded-2xl transition-colors hover:bg-base-300/40" @click="router.back()">
        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M15 18l-6-6 6-6"/>
        </svg>
      </button>
      <h1 class="text-xl font-bold">{{ $t('settings.changePassword') }}</h1>
    </header>

    <div class="surface space-y-4 p-4">
      <AlertMessage type="error" :message="error" />
      <AlertMessage v-if="success" type="success" :message="$t('settings.changePasswordSuccess')" />

      <!-- Step 1: email -->
      <form v-if="step === 'email'" class="space-y-4" novalidate @submit.prevent="sendCode">
        <p class="text-sm text-base-content/60">{{ $t('settings.changePasswordEmailStep') }}</p>
        <label class="form-control w-full">
          <span class="label-text mb-1 text-base-content/70">{{ $t('auth.email') }}</span>
          <input
            v-model="form.email"
            type="email"
            inputmode="email"
            autocomplete="email"
            placeholder="you@email.com"
            class="input input-bordered w-full bg-base-100/70"
            :class="{ 'input-error': emailTouched && !emailValid }"
          />
          <span v-if="emailTouched && !emailValid" class="mt-1 text-xs text-error">{{ $t('auth.errEmail') }}</span>
        </label>
        <button type="submit" class="btn btn-primary w-full tap-target" :disabled="loading">
          <span v-if="loading" class="loading loading-spinner loading-sm" />
          {{ loading ? $t('settings.changePasswordSending') : $t('settings.changePasswordSendCode') }}
        </button>
      </form>

      <!-- Step 2: code + new password -->
      <form v-else class="space-y-4" novalidate @submit.prevent="submit">
        <p class="text-sm text-base-content/60">
          {{ $t('settings.changePasswordCodeSent').replace('{email}', form.email) }}
        </p>

        <label class="form-control w-full">
          <span class="label-text mb-1 text-base-content/70">{{ $t('auth.resetCodeLabel') }}</span>
          <input
            v-model="form.code"
            type="text"
            inputmode="numeric"
            autocomplete="one-time-code"
            maxlength="6"
            placeholder="000000"
            class="input input-bordered w-full bg-base-100/70 text-center text-2xl tracking-[.3em] font-bold"
            :class="{ 'input-error': codeTouched && !form.code.trim() }"
          />
          <span v-if="codeTouched && !form.code.trim()" class="mt-1 text-xs text-error">{{ $t('auth.errOtpRequired') }}</span>
        </label>

        <label class="form-control w-full">
          <span class="label-text mb-1 text-base-content/70">{{ $t('settings.newPassword') }}</span>
          <PasswordInput
            v-model="form.newPwd"
            autocomplete="new-password"
            :input-class="codeTouched && !pwdValid ? 'input-error' : ''"
          />
          <ul v-if="form.newPwd || codeTouched" class="mt-2 space-y-1">
            <li
              v-for="rule in pwdRules"
              :key="rule.key"
              class="flex items-center gap-2 text-xs"
              :class="rule.ok ? 'text-success' : 'text-base-content/40'"
            >
              <span>{{ rule.ok ? '✓' : '○' }}</span>
              {{ $t('auth.' + rule.key) }}
            </li>
          </ul>
        </label>

        <label class="form-control w-full">
          <span class="label-text mb-1 text-base-content/70">{{ $t('auth.confirmPassword') }}</span>
          <PasswordInput
            v-model="form.confirm"
            autocomplete="new-password"
            :input-class="codeTouched && !pwdsMatch ? 'input-error' : ''"
          />
          <span v-if="codeTouched && !pwdsMatch" class="mt-1 text-xs text-error">{{ $t('auth.errMatch') }}</span>
        </label>

        <button type="submit" class="btn btn-primary w-full tap-target" :disabled="loading">
          <span v-if="loading" class="loading loading-spinner loading-sm" />
          {{ loading ? $t('settings.changePasswordSubmitting') : $t('settings.changePasswordSubmit') }}
        </button>

        <div class="flex justify-between text-sm">
          <button type="button" class="text-base-content/50 hover:text-base-content" @click="reset">
            {{ $t('common.back') }}
          </button>
          <button type="button" class="text-primary" :disabled="loading" @click="sendCode">
            {{ loading ? $t('auth.resending') : $t('auth.resendReset') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
