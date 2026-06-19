<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useOnboardingStore } from '@/stores/onboarding'
import { isMock } from '@/services/api'
import AlertMessage from '@/components/ui/AlertMessage.vue'
import BrandLogo from '@/components/ui/BrandLogo.vue'

const router = useRouter()
const auth = useAuthStore()
const onboarding = useOnboardingStore()

const form = reactive({ email: '', password: '' })
const touched = ref(false)

const emailValid = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))
const valid = computed(() => emailValid.value && form.password.length >= 1)

async function submit() {
  touched.value = true
  if (!valid.value) return
  const ok = await auth.login({ email: form.email.trim(), password: form.password })
  if (!ok) return
  // First-time attendees (per account) get the greeting + language picker + tutorial on home.
  if (!auth.isStaff) onboarding.maybeStart(auth.user?.id)
  const target = auth.consumeRedirect()
  router.push(target || (auth.isStaff ? '/admin/events' : '/'))
}
</script>

<template>
  <div class="flex min-h-dvh flex-col justify-center px-6 py-10">
    <div class="mb-8 flex flex-col items-center gap-4 text-center">
      <BrandLogo :size="56" wordmark-class="text-2xl" class="anim-pop" />
      <div>
        <h1 class="text-2xl font-bold">{{ $t('auth.loginTitle') }}</h1>
        <p class="text-sm text-base-content/60">{{ $t('auth.loginSubtitle') }}</p>
      </div>
    </div>

    <form class="space-y-4" novalidate @submit.prevent="submit">
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
        <input
          v-model="form.password"
          type="password"
          autocomplete="current-password"
          placeholder="••••••••"
          class="input input-bordered w-full bg-base-100/70"
          :class="{ 'input-error': touched && !form.password }"
        />
        <span v-if="touched && !form.password" class="mt-1 text-xs text-error">{{ $t('auth.errPasswordRequired') }}</span>
      </label>

      <button type="submit" class="btn btn-primary w-full tap-target" :disabled="auth.loading">
        <span v-if="auth.loading" class="loading loading-spinner loading-sm" />
        {{ auth.loading ? $t('auth.signingIn') : $t('auth.signIn') }}
      </button>
    </form>

    <p class="mt-6 text-center text-sm text-base-content/60">
      {{ $t('auth.newHere') }}
      <RouterLink to="/register" class="font-medium text-primary">{{ $t('auth.createLink') }}</RouterLink>
    </p>

    <p v-if="isMock" class="mt-6 rounded-xl border border-base-300/60 bg-base-100/40 p-3 text-center text-xs text-base-content/50">
      Demo mode is on. Any password works — sign in with an email containing
      <span class="font-semibold text-secondary">“admin”</span> to open the organizer panel.
    </p>
  </div>
</template>
