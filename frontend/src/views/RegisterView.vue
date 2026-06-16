<script setup>
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AlertMessage from '@/components/ui/AlertMessage.vue'

const router = useRouter()
const auth = useAuthStore()

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
  // Open question #4: auto-login after self-registration to shorten the door flow.
  const loggedIn = await auth.login({ email: form.email.trim(), password: form.password })
  const target = auth.consumeRedirect()
  router.push(loggedIn ? target || '/' : '/login')
}
</script>

<template>
  <div class="flex min-h-dvh flex-col justify-center px-6 py-10">
    <div class="mb-6 flex flex-col items-center gap-3 text-center">
      <span class="grid h-16 w-16 place-items-center rounded-2xl bg-gradient-to-br from-secondary to-primary text-3xl shadow-lg shadow-secondary/30">
        ✨
      </span>
      <div>
        <h1 class="text-2xl font-bold">Create your account</h1>
        <p class="text-sm text-base-content/60">Start collecting badges in seconds.</p>
      </div>
    </div>

    <form class="space-y-3.5" novalidate @submit.prevent="submit">
      <AlertMessage type="error" :message="auth.error || ''" />

      <div class="flex gap-3">
        <label class="form-control flex-1">
          <span class="label-text mb-1 text-base-content/70">First name</span>
          <input
            v-model="form.name"
            type="text"
            autocomplete="given-name"
            class="input input-bordered w-full bg-base-100/70"
            :class="{ 'input-error': touched && !form.name.trim() }"
          />
        </label>
        <label class="form-control flex-1">
          <span class="label-text mb-1 text-base-content/70">Last name</span>
          <input
            v-model="form.lastname"
            type="text"
            autocomplete="family-name"
            class="input input-bordered w-full bg-base-100/70"
          />
        </label>
      </div>

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">Email</span>
        <input
          v-model="form.email"
          type="email"
          inputmode="email"
          autocomplete="email"
          class="input input-bordered w-full bg-base-100/70"
          :class="{ 'input-error': touched && !emailValid }"
        />
        <span v-if="touched && !emailValid" class="mt-1 text-xs text-error">Enter a valid email.</span>
      </label>

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">Password</span>
        <input
          v-model="form.password"
          type="password"
          autocomplete="new-password"
          class="input input-bordered w-full bg-base-100/70"
          :class="{ 'input-error': touched && !passwordValid }"
        />
        <span v-if="touched && !passwordValid" class="mt-1 text-xs text-error">At least 6 characters.</span>
      </label>

      <label class="form-control w-full">
        <span class="label-text mb-1 text-base-content/70">Confirm password</span>
        <input
          v-model="form.confirm"
          type="password"
          autocomplete="new-password"
          class="input input-bordered w-full bg-base-100/70"
          :class="{ 'input-error': touched && !match }"
        />
        <span v-if="touched && !match" class="mt-1 text-xs text-error">Passwords don’t match.</span>
      </label>

      <button type="submit" class="btn btn-primary w-full tap-target" :disabled="auth.loading">
        <span v-if="auth.loading" class="loading loading-spinner loading-sm" />
        {{ auth.loading ? 'Creating…' : 'Create account' }}
      </button>
    </form>

    <p class="mt-6 text-center text-sm text-base-content/60">
      Already have an account?
      <RouterLink to="/login" class="font-medium text-primary">Sign in</RouterLink>
    </p>
  </div>
</template>
