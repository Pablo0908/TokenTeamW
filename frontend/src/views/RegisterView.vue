<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useOnboardingStore } from '@/stores/onboarding'
import AlertMessage from '@/components/ui/AlertMessage.vue'
import BrandLogo from '@/components/ui/BrandLogo.vue'
import GoogleSignInButton from '@/components/ui/GoogleSignInButton.vue'

const router = useRouter()
const auth = useAuthStore()
const onboarding = useOnboardingStore()

const form = reactive({ name: '', lastname: '', email: '', password: '', confirm: '' })
const touched = ref(false)
const emailTaken = ref(false)

const emailValid = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))

const pwdRules = computed(() => ({
  len:     form.password.length >= 8,
  upper:   /[A-Z]/.test(form.password),
  lower:   /[a-z]/.test(form.password),
  number:  /\d/.test(form.password),
  special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>/?`~]/.test(form.password),
}))
const passwordValid = computed(() => Object.values(pwdRules.value).every(Boolean))
const match = computed(() => form.password === form.confirm)
const valid = computed(() => form.name.trim() && emailValid.value && passwordValid.value && match.value)

async function handleGoogle(credential) {
  const ok = await auth.loginWithGoogle(credential)
  if (ok) {
    if (!auth.isStaff) onboarding.maybeStart(auth.user?.id)
    const target = auth.consumeRedirect()
    router.push(target || '/')
  }
}

async function submit() {
  touched.value = true
  emailTaken.value = false
  if (!valid.value) return
  const registered = await auth.register({
    name: form.name.trim(),
    lastname: form.lastname.trim(),
    email: form.email.trim(),
    password: form.password,
  })
  if (registered === 'duplicate') { emailTaken.value = true; return }
  if (!registered) return
  // Auto-login after self-registration to shorten the door flow.
  const loggedIn = await auth.login({ email: form.email.trim(), password: form.password })
  if (loggedIn !== true) {
    // 'otp' means 2FA was triggered — LoginView will show the OTP screen.
    // false means an error occurred — login page will show it.
    router.push('/login')
    return
  }
  const target = auth.consumeRedirect()
  // A QR deep link takes priority; otherwise land on home and run the first-run
  // greeting + language picker + tutorial (note: a saved redirect of "/" is common,
  // so we don't treat its mere presence as a reason to skip onboarding).
  if (target && target.startsWith('/redeem')) {
    router.push(target)
  } else {
    onboarding.maybeStart(auth.user?.id)
    router.push('/')
  }
}
</script>

<template>
  <div class="flex min-h-dvh flex-col justify-center px-6 py-10">
    <div class="mb-6 flex flex-col items-center gap-4 text-center">
      <BrandLogo :size="56" wordmark-class="text-2xl" class="anim-pop" :float="true" />
      <div>
        <h1 class="text-2xl font-bold">{{ $t('auth.registerTitle') }}</h1>
        <p class="text-sm text-base-content/60">{{ $t('auth.registerSubtitle') }}</p>
      </div>
    </div>

    <form class="space-y-3.5" novalidate @submit.prevent="submit">
      <AlertMessage type="error" :message="auth.error || ''" />

      <div class="flex gap-3">
        <label class="form-control flex-1">
          <span class="label-text mb-1 text-base-content/70">{{ $t('auth.firstName') }}</span>
          <input
            v-model="form.name"
            type="text"
            autocomplete="given-name"
            class="input input-bordered w-full bg-base-100/70"
            :class="{ 'input-error': touched && !form.name.trim() }"
          />
        </label>
        <label class="form-control flex-1">
          <span class="label-text mb-1 text-base-content/70">{{ $t('auth.lastName') }}</span>
          <input
            v-model="form.lastname"
            type="text"
            autocomplete="family-name"
            class="input input-bordered w-full bg-base-100/70"
          />
        </label>
      </div>

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">{{ $t('auth.email') }}</span>
        <input
          v-model="form.email"
          type="email"
          inputmode="email"
          autocomplete="email"
          class="input input-bordered w-full bg-base-100/70"
          :class="{ 'input-error': (touched && !emailValid) || emailTaken }"
          @input="emailTaken = false"
        />
        <span v-if="touched && !emailValid" class="mt-1 text-xs text-error">{{ $t('auth.errEmail') }}</span>
        <span v-else-if="emailTaken" class="mt-1 text-xs text-error">{{ $t('auth.errEmailTaken') }}</span>
      </label>

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">{{ $t('auth.password') }}</span>
        <input
          v-model="form.password"
          type="password"
          autocomplete="new-password"
          class="input input-bordered w-full bg-base-100/70"
          :class="{ 'input-error': touched && !passwordValid }"
        />
        <!-- Password strength checklist — shown while the user is typing -->
        <ul v-if="form.password || touched" class="mt-2 space-y-0.5">
          <li v-for="[key, label] in [['len', $t('auth.pwdLen')], ['upper', $t('auth.pwdUpper')], ['lower', $t('auth.pwdLower')], ['number', $t('auth.pwdNumber')], ['special', $t('auth.pwdSpecial')]]" :key="key"
              class="flex items-center gap-1.5 text-xs transition-colors"
              :class="pwdRules[key] ? 'text-success' : 'text-base-content/50'">
            <span>{{ pwdRules[key] ? '✓' : '○' }}</span>
            <span>{{ label }}</span>
          </li>
        </ul>
        <span v-if="touched && !passwordValid" class="mt-1 text-xs text-error">{{ $t('auth.errPasswordWeak') }}</span>
      </label>

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">{{ $t('auth.confirmPassword') }}</span>
        <input
          v-model="form.confirm"
          type="password"
          autocomplete="new-password"
          class="input input-bordered w-full bg-base-100/70"
          :class="{ 'input-error': touched && !match }"
        />
        <span v-if="touched && !match" class="mt-1 text-xs text-error">{{ $t('auth.errMatch') }}</span>
      </label>

      <button type="submit" class="btn btn-primary w-full tap-target btn-flash" :disabled="auth.loading">
        <span v-if="auth.loading" class="loading loading-spinner loading-sm" />
        {{ auth.loading ? $t('auth.creating') : $t('auth.create') }}
      </button>
    </form>

    <div class="mt-6 flex flex-col gap-3">
      <div class="flex items-center gap-3 text-xs text-base-content/40">
        <span class="flex-1 border-t border-base-content/10" />
        <span>or</span>
        <span class="flex-1 border-t border-base-content/10" />
      </div>
      <GoogleSignInButton @credential="handleGoogle" />
    </div>

    <p class="mt-6 text-center text-sm text-base-content/60">
      {{ $t('auth.haveAccount') }}
      <RouterLink to="/login" class="link-glow font-medium text-primary underline underline-offset-2">{{ $t('auth.signInLink') }}</RouterLink>
    </p>
  </div>
</template>
