<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useOnboardingStore } from '@/stores/onboarding'
import { isMock } from '@/services/api'
import AlertMessage from '@/components/ui/AlertMessage.vue'
import BrandLogo from '@/components/ui/BrandLogo.vue'
import AuthSplit from '@/components/ui/AuthSplit.vue'
import GoogleSignInButton from '@/components/ui/GoogleSignInButton.vue'
import PasswordInput from '@/components/ui/PasswordInput.vue'

const router = useRouter()
const auth = useAuthStore()
const onboarding = useOnboardingStore()

// step: 'credentials' | 'otp'
const step = ref('credentials')

const form = reactive({ email: '', password: '' })
const otpCode = ref('')
const otpTouched = ref(false)
const touched = ref(false)
const otpInfo = ref('')  // success message (e.g. "New code sent")

const emailValid = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))
const valid = computed(() => emailValid.value && form.password.length >= 1)

function finishLogin() {
  // Skip the attendee coach-marks for platform super admins; everyone else gets the tour.
  if (auth.user?.platform_role !== 'super_admin') onboarding.maybeStart(auth.user?.id)
  // Everyone (admins included) lands on home first; a saved deep-link redirect
  // (e.g. a QR scan or a protected page they were headed to) still takes priority.
  const target = auth.consumeRedirect()
  router.push(target || '/')
}

async function handleGoogle(credential) {
  const ok = await auth.loginWithGoogle(credential)
  if (ok) finishLogin()
}

async function submitCredentials() {
  touched.value = true
  if (!valid.value) return
  const result = await auth.login({ email: form.email.trim(), password: form.password })
  if (result === 'otp') {
    step.value = 'otp'
    otpCode.value = ''
    otpTouched.value = false
    otpInfo.value = ''
  } else if (result === true) {
    finishLogin()
  }
}

async function submitOtp() {
  otpTouched.value = true
  if (!otpCode.value.trim()) return
  const ok = await auth.verify2fa(form.email.trim(), otpCode.value.trim())
  if (ok) finishLogin()
}

async function resendCode() {
  otpInfo.value = ''
  const result = await auth.login({ email: form.email.trim(), password: form.password })
  if (result === 'otp') otpInfo.value = 'otpSent'
}

function backToCredentials() {
  step.value = 'credentials'
  otpCode.value = ''
  otpTouched.value = false
  otpInfo.value = ''
  auth.error = null
}
</script>

<template>
  <AuthSplit>
    <div class="mb-8 flex flex-col items-center gap-4 text-center">
      <BrandLogo :size="56" wordmark-class="text-2xl" class="anim-pop lg:hidden" :float="true" />
      <div>
        <h1 class="text-2xl font-bold">
          {{ step === 'otp' ? $t('auth.twoFaTitle') : $t('auth.loginTitle') }}
        </h1>
        <p class="text-sm text-base-content/60">
          <template v-if="step === 'otp'">
            {{ $t('auth.twoFaSubtitle').replace('{email}', form.email) }}
          </template>
          <template v-else>
            {{ $t('auth.loginSubtitle') }}
          </template>
        </p>
      </div>
    </div>

    <!-- ── Step 1: email + password ── -->
    <form v-if="step === 'credentials'" class="space-y-4" novalidate @submit.prevent="submitCredentials">
      <AlertMessage type="error" :message="auth.error || ''" />

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">{{ $t('auth.email') }}</span>
        <input
          v-model="form.email"
          type="email"
          inputmode="email"
          autocomplete="email"
          placeholder="you@email.com"
          class="input input-bordered w-full bg-base-100/70"
          :class="{ 'input-error': touched && !emailValid }"
        />
        <span v-if="touched && !emailValid" class="mt-1 text-xs text-error">{{ $t('auth.errEmail') }}</span>
      </label>

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">{{ $t('auth.password') }}</span>
        <PasswordInput
          v-model="form.password"
          autocomplete="current-password"
          :input-class="touched && !form.password ? 'input-error' : ''"
        />
        <span v-if="touched && !form.password" class="mt-1 text-xs text-error">{{ $t('auth.errPasswordRequired') }}</span>
        <div class="mt-1 text-right">
          <RouterLink to="/forgot-password" class="text-xs text-primary hover:underline">{{ $t('auth.forgotPassword') }}</RouterLink>
        </div>
      </label>

      <button type="submit" class="btn btn-primary w-full tap-target btn-flash" :disabled="auth.loading">
        <span v-if="auth.loading" class="loading loading-spinner loading-sm" />
        {{ auth.loading ? $t('auth.signingIn') : $t('auth.signIn') }}
      </button>
    </form>

    <!-- ── Step 2: OTP ── -->
    <form v-else class="space-y-4" novalidate @submit.prevent="submitOtp">
      <AlertMessage type="error" :message="auth.error || ''" />
      <AlertMessage v-if="otpInfo" type="success" :message="$t('auth.' + otpInfo)" />

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">{{ $t('auth.otpLabel') }}</span>
        <input
          v-model="otpCode"
          type="text"
          inputmode="numeric"
          autocomplete="one-time-code"
          maxlength="6"
          :placeholder="$t('auth.otpPlaceholder')"
          class="input input-bordered w-full bg-base-100/70 text-center text-2xl tracking-[.3em] font-bold"
          :class="{ 'input-error': otpTouched && !otpCode.trim() }"
        />
        <span v-if="otpTouched && !otpCode.trim()" class="mt-1 text-xs text-error">{{ $t('auth.errOtpRequired') }}</span>
      </label>

      <button type="submit" class="btn btn-primary w-full tap-target" :disabled="auth.loading">
        <span v-if="auth.loading" class="loading loading-spinner loading-sm" />
        {{ auth.loading ? $t('auth.verifying') : $t('auth.verify') }}
      </button>

      <div class="flex justify-between text-sm">
        <button type="button" class="text-base-content/50 hover:text-base-content" @click="backToCredentials">
          {{ $t('auth.backToSignIn') }}
        </button>
        <button type="button" class="text-primary" :disabled="auth.loading" @click="resendCode">
          {{ auth.loading ? $t('auth.resending') : $t('auth.resend') }}
        </button>
      </div>
    </form>

    <div v-if="step === 'credentials'" class="mt-6 flex flex-col gap-3">
      <div class="flex items-center gap-3 text-xs text-base-content/40">
        <span class="flex-1 border-t border-base-content/10" />
        <span>{{ $t('common.or') }}</span>
        <span class="flex-1 border-t border-base-content/10" />
      </div>
      <GoogleSignInButton @credential="handleGoogle" />
    </div>

    <p v-if="step === 'credentials'" class="mt-6 text-center text-sm text-base-content/60">
      {{ $t('auth.newHere') }}
      <RouterLink to="/register" class="link-glow font-medium text-primary underline underline-offset-2">{{ $t('auth.createLink') }}</RouterLink>
    </p>

    <p v-if="isMock" class="mt-6 rounded-xl border border-base-300/60 bg-base-100/40 p-3 text-center text-xs text-base-content/50">
      Demo mode is on. Any password works — sign in with an email containing
      <span class="font-semibold text-secondary">"admin"</span> to open the organizer panel.
    </p>
  </AuthSplit>
</template>
