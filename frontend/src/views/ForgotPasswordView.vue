<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/services/api'
import AlertMessage from '@/components/ui/AlertMessage.vue'
import BrandLogo from '@/components/ui/BrandLogo.vue'

const router = useRouter()

// step: 'email' | 'reset'
const step = ref('email')
const loading = ref(false)
const errorMsg = ref('')
const email = ref('')
const emailTouched = ref(false)

const emailValid = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value))

const reset = reactive({ code: '', password: '', confirmPassword: '' })
const resetTouched = ref(false)
const successMsg = ref('')

const passwordRules = computed(() => [
  { key: 'pwdLen',     ok: reset.password.length >= 8 },
  { key: 'pwdUpper',  ok: /[A-Z]/.test(reset.password) },
  { key: 'pwdLower',  ok: /[a-z]/.test(reset.password) },
  { key: 'pwdNumber', ok: /\d/.test(reset.password) },
  { key: 'pwdSpecial',ok: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>/?`~]/.test(reset.password) },
])
const passwordValid = computed(() => passwordRules.value.every(r => r.ok))
const passwordsMatch = computed(() => reset.password === reset.confirmPassword)

async function submitEmail() {
  emailTouched.value = true
  if (!emailValid.value) return
  loading.value = true
  errorMsg.value = ''
  try {
    await api.post('/auth/forgot-password', { email: email.value.trim().toLowerCase() })
    step.value = 'reset'
  } catch (err) {
    errorMsg.value = err.response?.data?.error ?? 'Error inesperado'
  } finally {
    loading.value = false
  }
}

async function resendCode() {
  loading.value = true
  errorMsg.value = ''
  try {
    await api.post('/auth/forgot-password', { email: email.value.trim().toLowerCase() })
    errorMsg.value = ''
  } catch (err) {
    errorMsg.value = err.response?.data?.error ?? 'Error inesperado'
  } finally {
    loading.value = false
  }
}

async function submitReset() {
  resetTouched.value = true
  if (!reset.code.trim() || !passwordValid.value || !passwordsMatch.value) return
  loading.value = true
  errorMsg.value = ''
  try {
    await api.post('/auth/reset-password', {
      email: email.value.trim().toLowerCase(),
      code: reset.code.trim(),
      password: reset.password,
    })
    successMsg.value = 'resetSuccess'
    setTimeout(() => router.push({ name: 'login' }), 2000)
  } catch (err) {
    errorMsg.value = err.response?.data?.error ?? 'Error inesperado'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-dvh flex-col justify-center px-6 py-10">
    <div class="mb-8 flex flex-col items-center gap-4 text-center">
      <BrandLogo :size="56" wordmark-class="text-2xl" class="anim-pop" :float="true" />
      <div>
        <h1 class="text-2xl font-bold">
          {{ step === 'email' ? $t('auth.forgotTitle') : $t('auth.resetTitle') }}
        </h1>
        <p class="text-sm text-base-content/60">
          <template v-if="step === 'email'">{{ $t('auth.forgotSubtitle') }}</template>
          <template v-else>{{ $t('auth.forgotSent').replace('{email}', email) }}</template>
        </p>
      </div>
    </div>

    <!-- ── Step 1: email ── -->
    <form v-if="step === 'email'" class="space-y-4" novalidate @submit.prevent="submitEmail">
      <AlertMessage type="error" :message="errorMsg" />

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">{{ $t('auth.email') }}</span>
        <input
          v-model="email"
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
        {{ loading ? $t('auth.forgotSubmitting') : $t('auth.forgotSubmit') }}
      </button>

      <p class="text-center text-sm text-base-content/60">
        <RouterLink to="/login" class="text-primary hover:underline">{{ $t('auth.backToSignIn') }}</RouterLink>
      </p>
    </form>

    <!-- ── Step 2: code + new password ── -->
    <form v-else class="space-y-4" novalidate @submit.prevent="submitReset">
      <AlertMessage type="error" :message="errorMsg" />
      <AlertMessage v-if="successMsg" type="success" :message="$t('auth.' + successMsg)" />

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">{{ $t('auth.resetCodeLabel') }}</span>
        <input
          v-model="reset.code"
          type="text"
          inputmode="numeric"
          autocomplete="one-time-code"
          maxlength="6"
          placeholder="000000"
          class="input input-bordered w-full bg-base-100/70 text-center text-2xl tracking-[.3em] font-bold"
          :class="{ 'input-error': resetTouched && !reset.code.trim() }"
        />
        <span v-if="resetTouched && !reset.code.trim()" class="mt-1 text-xs text-error">{{ $t('auth.errOtpRequired') }}</span>
      </label>

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">{{ $t('auth.newPasswordLabel') }}</span>
        <input
          v-model="reset.password"
          type="password"
          autocomplete="new-password"
          placeholder="••••••••"
          class="input input-bordered w-full bg-base-100/70"
          :class="{ 'input-error': resetTouched && !passwordValid }"
        />
        <ul v-if="reset.password || resetTouched" class="mt-2 space-y-1">
          <li
            v-for="rule in passwordRules"
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
        <input
          v-model="reset.confirmPassword"
          type="password"
          autocomplete="new-password"
          placeholder="••••••••"
          class="input input-bordered w-full bg-base-100/70"
          :class="{ 'input-error': resetTouched && !passwordsMatch }"
        />
        <span v-if="resetTouched && !passwordsMatch" class="mt-1 text-xs text-error">{{ $t('auth.errMatch') }}</span>
      </label>

      <button type="submit" class="btn btn-primary w-full tap-target" :disabled="loading">
        <span v-if="loading" class="loading loading-spinner loading-sm" />
        {{ loading ? $t('auth.resetSubmitting') : $t('auth.resetSubmit') }}
      </button>

      <div class="flex justify-between text-sm">
        <RouterLink to="/login" class="text-base-content/50 hover:text-base-content">
          {{ $t('auth.backToSignIn') }}
        </RouterLink>
        <button type="button" class="text-primary" :disabled="loading" @click="resendCode">
          {{ loading ? $t('auth.resending') : $t('auth.resendReset') }}
        </button>
      </div>
    </form>
  </div>
</template>
