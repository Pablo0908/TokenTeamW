<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/services/api'
import AlertMessage from '@/components/ui/AlertMessage.vue'
import PasswordInput from '@/components/ui/PasswordInput.vue'

const router = useRouter()
const auth = useAuthStore()

const initials = computed(() => {
  const n = auth.user?.name ?? ''
  const l = auth.user?.lastname ?? ''
  return ((n[0] ?? '') + (l[0] ?? '')).toUpperCase() || (auth.user?.email?.[0] ?? 'U').toUpperCase()
})
const fullName = computed(() =>
  [auth.user?.name, auth.user?.lastname].filter(Boolean).join(' ') || auth.displayName,
)

// Accordion helpers
const openSection = ref(null)
function toggle(key) {
  if (openSection.value === key) {
    openSection.value = null
    if (key === 'password') resetPwdSection()
    if (key === 'email') resetEmailSection()
    if (key === 'edit') { editError.value = ''; editSuccess.value = false }
  } else {
    openSection.value = key
    if (key === 'edit') {
      editForm.name = auth.user?.name ?? ''
      editForm.lastname = auth.user?.lastname ?? ''
    }
  }
}

function accEnter(el) {
  el.style.overflow = 'hidden'
  el.style.height = '0'
  el.offsetHeight
  el.style.transition = 'height 0.4s cubic-bezier(0.34,1.15,0.64,1)'
  el.style.height = el.scrollHeight + 'px'
}
function accAfterEnter(el) { el.style.height = ''; el.style.overflow = ''; el.style.transition = '' }
function accLeave(el) {
  el.style.overflow = 'hidden'
  el.style.height = el.scrollHeight + 'px'
  el.style.opacity = '1'
  el.offsetHeight
  el.style.transition = 'height 0.35s cubic-bezier(0.2,0.7,0.2,1), opacity 0.25s ease'
  el.style.height = '0'
  el.style.opacity = '0'
}
function accAfterLeave(el) { el.style.height = ''; el.style.overflow = ''; el.style.transition = ''; el.style.opacity = '' }

function logout() {
  auth.logout()
  router.push('/login')
}

// Edit profile
const editForm = reactive({ name: '', lastname: '' })
const editLoading = ref(false)
const editError = ref('')
const editSuccess = ref(false)

async function submitEditProfile() {
  if (!editForm.name.trim()) return
  editLoading.value = true
  editError.value = ''
  editSuccess.value = false
  try {
    const { data } = await api.put('/me/profile', { name: editForm.name.trim(), lastname: editForm.lastname.trim() })
    auth.patchUser({ name: data.name, lastname: data.lastname })
    editSuccess.value = true
    setTimeout(() => { editSuccess.value = false }, 3000)
  } catch (err) {
    editError.value = err.response?.data?.error ?? 'Unexpected error'
  } finally {
    editLoading.value = false
  }
}

// Change email
const emailStep = ref('input')
const emailForm = reactive({ newEmail: '', code: '' })
const emailLoading = ref(false)
const emailError = ref('')
const emailSuccess = ref(false)
const emailNewTouched = ref(false)
const emailCodeTouched = ref(false)
const emailNewValid = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailForm.newEmail))

function resetEmailSection() {
  emailStep.value = 'input'
  emailForm.newEmail = ''
  emailForm.code = ''
  emailError.value = ''
  emailSuccess.value = false
  emailNewTouched.value = false
  emailCodeTouched.value = false
}

async function sendEmailCode() {
  emailNewTouched.value = true
  if (!emailNewValid.value) return
  emailLoading.value = true
  emailError.value = ''
  try {
    await api.post('/me/email/send-code', { new_email: emailForm.newEmail.trim().toLowerCase() })
    emailStep.value = 'code'
  } catch (err) {
    emailError.value = err.response?.data?.error ?? 'Unexpected error'
  } finally {
    emailLoading.value = false
  }
}

async function submitEmailChange() {
  emailCodeTouched.value = true
  if (!emailForm.code.trim()) return
  emailLoading.value = true
  emailError.value = ''
  try {
    const { data } = await api.put('/me/email', { code: emailForm.code.trim() })
    auth.patchUser({ email: data.email })
    emailSuccess.value = true
    resetEmailSection()
    emailSuccess.value = true
  } catch (err) {
    emailError.value = err.response?.data?.error ?? 'Unexpected error'
  } finally {
    emailLoading.value = false
  }
}

// Change password
const pwdStep = ref('email')
const pwdForm = reactive({ email: '', code: '', newPwd: '', confirm: '' })
const pwdEmailTouched = ref(false)
const pwdCodeTouched = ref(false)
const pwdLoading = ref(false)
const pwdError = ref('')
const pwdSuccess = ref(false)
const pwdEmailValid = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(pwdForm.email))
const newPwdRules = computed(() => [
  { key: 'pwdLen',     ok: pwdForm.newPwd.length >= 8 },
  { key: 'pwdUpper',  ok: /[A-Z]/.test(pwdForm.newPwd) },
  { key: 'pwdLower',  ok: /[a-z]/.test(pwdForm.newPwd) },
  { key: 'pwdNumber', ok: /\d/.test(pwdForm.newPwd) },
  { key: 'pwdSpecial',ok: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>/?`~]/.test(pwdForm.newPwd) },
])
const newPwdValid = computed(() => newPwdRules.value.every(r => r.ok))
const pwdsMatch = computed(() => pwdForm.newPwd === pwdForm.confirm)

function resetPwdSection() {
  pwdStep.value = 'email'
  pwdForm.email = ''
  pwdForm.code = ''
  pwdForm.newPwd = ''
  pwdForm.confirm = ''
  pwdEmailTouched.value = false
  pwdCodeTouched.value = false
  pwdError.value = ''
  pwdSuccess.value = false
}

async function sendPwdCode() {
  pwdEmailTouched.value = true
  if (!pwdEmailValid.value) return
  pwdLoading.value = true
  pwdError.value = ''
  try {
    await api.post('/me/password/send-code', { email: pwdForm.email.trim().toLowerCase() })
    pwdStep.value = 'code'
  } catch (err) {
    pwdError.value = err.response?.data?.error ?? 'Unexpected error'
  } finally {
    pwdLoading.value = false
  }
}

async function submitPasswordChange() {
  pwdCodeTouched.value = true
  if (!pwdForm.code.trim() || !newPwdValid.value || !pwdsMatch.value) return
  pwdLoading.value = true
  pwdError.value = ''
  pwdSuccess.value = false
  try {
    await api.put('/me/password', {
      email: pwdForm.email.trim().toLowerCase(),
      code: pwdForm.code.trim(),
      new_password: pwdForm.newPwd,
    })
    pwdSuccess.value = true
    resetPwdSection()
    pwdSuccess.value = true
  } catch (err) {
    pwdError.value = err.response?.data?.error ?? 'Unexpected error'
  } finally {
    pwdLoading.value = false
  }
}
</script>

<template>
  <div class="space-y-6 px-4 pb-4 pt-6">
    <!-- Header -->
    <header class="flex items-center gap-3">
      <button type="button" class="tap-target grid h-9 w-9 shrink-0 place-items-center rounded-2xl bg-base-300/60 transition-colors" @click="router.back()">
        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M15 18l-6-6 6-6"/>
        </svg>
      </button>
      <h1 class="text-xl font-bold">{{ $t('settings.title') }}</h1>
    </header>

    <!-- User card (display only) -->
    <div class="surface flex items-center gap-4 p-4">
      <span class="grid h-12 w-12 shrink-0 place-items-center rounded-full bg-gradient-to-br from-primary to-secondary text-base font-bold text-primary-content">
        {{ initials }}
      </span>
      <div class="min-w-0 flex-1">
        <p class="truncate font-semibold">{{ fullName }}</p>
        <p class="truncate text-sm text-base-content/55">{{ auth.user?.email }}</p>
      </div>
    </div>

    <!-- Profile & Security -->
    <div class="space-y-1">
      <p class="px-1 pb-1 text-[0.65rem] font-semibold uppercase tracking-widest text-base-content/40">{{ $t('profile.profileSecurity') }}</p>

      <div class="surface overflow-hidden">
        <!-- Edit profile -->
        <div class="border-b border-base-300/40">
          <button type="button" class="flex w-full items-center justify-between gap-3 p-4 tap-target transition-colors" @click="toggle('edit')">
            <div class="flex items-center gap-3">
              <span class="grid h-9 w-9 shrink-0 place-items-center rounded-2xl bg-primary/15">
                <svg class="h-4.5 w-4.5 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              </span>
              <div class="text-left">
                <p class="text-sm font-semibold">{{ $t('profile.editProfile') }}</p>
                <p class="text-xs text-base-content/50">{{ $t('profile.editProfileHint') }}</p>
              </div>
            </div>
            <svg class="h-4 w-4 shrink-0 text-base-content/40 transition-transform duration-300" :class="openSection === 'edit' ? 'rotate-90' : ''" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
          </button>
          <transition :css="false" @enter="accEnter" @after-enter="accAfterEnter" @leave="accLeave" @after-leave="accAfterLeave">
            <div v-if="openSection === 'edit'" class="border-t border-base-300/40 px-4 pb-4 pt-3">
              <AlertMessage type="error" :message="editError" />
              <AlertMessage v-if="editSuccess" type="success" :message="$t('profile.saveSuccess')" />
              <form class="space-y-3" novalidate @submit.prevent="submitEditProfile">
                <label class="form-control w-full">
                  <span class="label-text mb-1 text-base-content/70">{{ $t('auth.firstName') }}</span>
                  <input v-model="editForm.name" type="text" autocomplete="given-name" class="input input-bordered w-full bg-base-100/70" />
                </label>
                <label class="form-control w-full">
                  <span class="label-text mb-1 text-base-content/70">{{ $t('auth.lastName') }}</span>
                  <input v-model="editForm.lastname" type="text" autocomplete="family-name" class="input input-bordered w-full bg-base-100/70" />
                </label>
                <button type="submit" class="btn btn-primary w-full tap-target" :disabled="editLoading">
                  <span v-if="editLoading" class="loading loading-spinner loading-sm" />
                  {{ $t('profile.saveProfile') }}
                </button>
              </form>
            </div>
          </transition>
        </div>

        <!-- Change email -->
        <div class="border-b border-base-300/40">
          <button type="button" class="flex w-full items-center justify-between gap-3 p-4 tap-target transition-colors" @click="toggle('email')">
            <div class="flex items-center gap-3">
              <span class="grid h-9 w-9 shrink-0 place-items-center rounded-2xl bg-secondary/15">
                <svg class="h-4.5 w-4.5 text-secondary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M2 7l10 7 10-7"/></svg>
              </span>
              <div class="text-left">
                <p class="text-sm font-semibold">{{ $t('profile.changeEmail') }}</p>
                <p class="text-xs text-base-content/50">{{ auth.user?.email }}</p>
              </div>
            </div>
            <svg class="h-4 w-4 shrink-0 text-base-content/40 transition-transform duration-300" :class="openSection === 'email' ? 'rotate-90' : ''" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
          </button>
          <transition :css="false" @enter="accEnter" @after-enter="accAfterEnter" @leave="accLeave" @after-leave="accAfterLeave">
            <div v-if="openSection === 'email'" class="border-t border-base-300/40 px-4 pb-4 pt-3">
              <AlertMessage type="error" :message="emailError" />
              <AlertMessage v-if="emailSuccess" type="success" :message="$t('profile.changeEmailSuccess')" />
              <form v-if="emailStep === 'input'" class="space-y-3" novalidate @submit.prevent="sendEmailCode">
                <p class="text-sm text-base-content/60">{{ $t('profile.changeEmailStep') }}</p>
                <label class="form-control w-full">
                  <span class="label-text mb-1 text-base-content/70">{{ $t('auth.email') }}</span>
                  <input v-model="emailForm.newEmail" type="email" inputmode="email" autocomplete="email" placeholder="new@email.com" class="input input-bordered w-full bg-base-100/70" :class="{ 'input-error': emailNewTouched && !emailNewValid }" />
                  <span v-if="emailNewTouched && !emailNewValid" class="mt-1 text-xs text-error">{{ $t('auth.errEmail') }}</span>
                </label>
                <button type="submit" class="btn btn-primary w-full tap-target" :disabled="emailLoading">
                  <span v-if="emailLoading" class="loading loading-spinner loading-sm" />
                  {{ emailLoading ? $t('profile.changeEmailSending') : $t('profile.changeEmailSendCode') }}
                </button>
              </form>
              <form v-else class="space-y-3" novalidate @submit.prevent="submitEmailChange">
                <p class="text-sm text-base-content/60">{{ $t('profile.changeEmailCodeSent') }}</p>
                <label class="form-control w-full">
                  <span class="label-text mb-1 text-base-content/70">{{ $t('auth.resetCodeLabel') }}</span>
                  <input v-model="emailForm.code" type="text" inputmode="numeric" autocomplete="one-time-code" maxlength="6" placeholder="000000" class="input input-bordered w-full bg-base-100/70 text-center text-2xl tracking-[.3em] font-bold" :class="{ 'input-error': emailCodeTouched && !emailForm.code.trim() }" />
                </label>
                <button type="submit" class="btn btn-primary w-full tap-target" :disabled="emailLoading">
                  <span v-if="emailLoading" class="loading loading-spinner loading-sm" />
                  {{ emailLoading ? $t('profile.changeEmailSubmitting') : $t('profile.changeEmailSubmit') }}
                </button>
                <button type="button" class="text-sm text-base-content/50 hover:text-base-content" @click="resetEmailSection">{{ $t('common.back') }}</button>
              </form>
            </div>
          </transition>
        </div>

        <!-- Change password -->
        <div>
          <button type="button" class="flex w-full items-center justify-between gap-3 p-4 tap-target transition-colors" @click="toggle('password')">
            <div class="flex items-center gap-3">
              <span class="grid h-9 w-9 shrink-0 place-items-center rounded-2xl bg-accent/15">
                <svg class="h-4.5 w-4.5 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
              </span>
              <div class="text-left">
                <p class="text-sm font-semibold">{{ $t('settings.changePassword') }}</p>
                <p class="text-xs text-base-content/50">{{ $t('settings.changePasswordHint') }}</p>
              </div>
            </div>
            <svg class="h-4 w-4 shrink-0 text-base-content/40 transition-transform duration-300" :class="openSection === 'password' ? 'rotate-90' : ''" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"/></svg>
          </button>
          <transition :css="false" @enter="accEnter" @after-enter="accAfterEnter" @leave="accLeave" @after-leave="accAfterLeave">
            <div v-if="openSection === 'password'" class="border-t border-base-300/40 px-4 pb-5 pt-3">
              <AlertMessage type="error" :message="pwdError" />
              <AlertMessage v-if="pwdSuccess" type="success" :message="$t('settings.changePasswordSuccess')" />
              <form v-if="pwdStep === 'email'" class="space-y-4" novalidate @submit.prevent="sendPwdCode">
                <p class="text-sm text-base-content/60">{{ $t('settings.changePasswordEmailStep') }}</p>
                <label class="form-control w-full">
                  <span class="label-text mb-1 text-base-content/70">{{ $t('auth.email') }}</span>
                  <input v-model="pwdForm.email" type="email" inputmode="email" autocomplete="email" placeholder="you@email.com" class="input input-bordered w-full bg-base-100/70" :class="{ 'input-error': pwdEmailTouched && !pwdEmailValid }" />
                  <span v-if="pwdEmailTouched && !pwdEmailValid" class="mt-1 text-xs text-error">{{ $t('auth.errEmail') }}</span>
                </label>
                <button type="submit" class="btn btn-primary w-full tap-target" :disabled="pwdLoading">
                  <span v-if="pwdLoading" class="loading loading-spinner loading-sm" />
                  {{ pwdLoading ? $t('settings.changePasswordSending') : $t('settings.changePasswordSendCode') }}
                </button>
              </form>
              <form v-else class="space-y-4" novalidate @submit.prevent="submitPasswordChange">
                <p class="text-sm text-base-content/60">{{ $t('settings.changePasswordCodeSent').replace('{email}', pwdForm.email) }}</p>
                <label class="form-control w-full">
                  <span class="label-text mb-1 text-base-content/70">{{ $t('auth.resetCodeLabel') }}</span>
                  <input v-model="pwdForm.code" type="text" inputmode="numeric" autocomplete="one-time-code" maxlength="6" placeholder="000000" class="input input-bordered w-full bg-base-100/70 text-center text-2xl tracking-[.3em] font-bold" :class="{ 'input-error': pwdCodeTouched && !pwdForm.code.trim() }" />
                  <span v-if="pwdCodeTouched && !pwdForm.code.trim()" class="mt-1 text-xs text-error">{{ $t('auth.errOtpRequired') }}</span>
                </label>
                <label class="form-control w-full">
                  <span class="label-text mb-1 text-base-content/70">{{ $t('settings.newPassword') }}</span>
                  <PasswordInput v-model="pwdForm.newPwd" autocomplete="new-password" :input-class="pwdCodeTouched && !newPwdValid ? 'input-error' : ''" />
                  <ul v-if="pwdForm.newPwd || pwdCodeTouched" class="mt-2 space-y-1">
                    <li v-for="rule in newPwdRules" :key="rule.key" class="flex items-center gap-2 text-xs" :class="rule.ok ? 'text-success' : 'text-base-content/40'">
                      <span>{{ rule.ok ? '✓' : '○' }}</span>{{ $t('auth.' + rule.key) }}
                    </li>
                  </ul>
                </label>
                <label class="form-control w-full">
                  <span class="label-text mb-1 text-base-content/70">{{ $t('auth.confirmPassword') }}</span>
                  <PasswordInput v-model="pwdForm.confirm" autocomplete="new-password" :input-class="pwdCodeTouched && !pwdsMatch ? 'input-error' : ''" />
                  <span v-if="pwdCodeTouched && !pwdsMatch" class="mt-1 text-xs text-error">{{ $t('auth.errMatch') }}</span>
                </label>
                <button type="submit" class="btn btn-primary w-full tap-target" :disabled="pwdLoading">
                  <span v-if="pwdLoading" class="loading loading-spinner loading-sm" />
                  {{ pwdLoading ? $t('settings.changePasswordSubmitting') : $t('settings.changePasswordSubmit') }}
                </button>
                <div class="flex justify-between text-sm">
                  <button type="button" class="text-base-content/50 hover:text-base-content" @click="resetPwdSection">{{ $t('common.back') }}</button>
                  <button type="button" class="text-primary" :disabled="pwdLoading" @click="sendPwdCode">{{ pwdLoading ? $t('auth.resending') : $t('auth.resendReset') }}</button>
                </div>
              </form>
            </div>
          </transition>
        </div>
      </div>

      <!-- Log out -->
      <button type="button" class="surface flex w-full items-center gap-3 p-4 tap-target text-error transition-colors" @click="logout">
        <span class="grid h-9 w-9 shrink-0 place-items-center rounded-2xl bg-error/10">
          <svg class="h-4.5 w-4.5 text-error" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
        </span>
        <span class="text-sm font-semibold">{{ $t('common.logout') }}</span>
      </button>
    </div>
  </div>
</template>
