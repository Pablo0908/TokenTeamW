<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useOnboardingStore } from '@/stores/onboarding'
import AlertMessage from '@/components/ui/AlertMessage.vue'
import BrandLogo from '@/components/ui/BrandLogo.vue'

const router = useRouter()
const auth = useAuthStore()
const onboarding = useOnboardingStore()

const form = reactive({ name: '', lastname: '', email: '', password: '', confirm: '' })
const touched = ref(false)

const emailValid = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))
const passwordValid = computed(() => form.password.length >= 6)
const match = computed(() => form.password === form.confirm)
const valid = computed(() => form.name.trim() && emailValid.value && passwordValid.value && match.value)

async function submit() {
  touched.value = true
  if (!valid.value) return
  const registered = await auth.register({
    name: form.name.trim(),
    lastname: form.lastname.trim(),
    email: form.email.trim(),
    password: form.password,
  })
  if (!registered) return
  // Auto-login after self-registration to shorten the door flow.
  const loggedIn = await auth.login({ email: form.email.trim(), password: form.password })
  if (!loggedIn) {
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
      <BrandLogo :size="56" wordmark-class="text-2xl" class="anim-pop" />
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
          :class="{ 'input-error': touched && !emailValid }"
        />
        <span v-if="touched && !emailValid" class="mt-1 text-xs text-error">{{ $t('auth.errEmail') }}</span>
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
        <span v-if="touched && !passwordValid" class="mt-1 text-xs text-error">{{ $t('auth.errPassword6') }}</span>
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

      <button type="submit" class="btn btn-primary w-full tap-target" :disabled="auth.loading">
        <span v-if="auth.loading" class="loading loading-spinner loading-sm" />
        {{ auth.loading ? $t('auth.creating') : $t('auth.create') }}
      </button>
    </form>

    <p class="mt-6 text-center text-sm text-base-content/60">
      {{ $t('auth.haveAccount') }}
      <RouterLink to="/login" class="font-medium text-primary">{{ $t('auth.signInLink') }}</RouterLink>
    </p>
  </div>
</template>
