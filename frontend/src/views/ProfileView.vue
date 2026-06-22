<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { locale, setLocale } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import { useBadgesStore } from '@/stores/badges'
import { useSettingsStore, CONTRAST_RANGE, FONT_SIZE_RANGE } from '@/stores/settings'
import { api } from '@/services/api'
import StatTile from '@/components/domain/StatTile.vue'
import ProgressBar from '@/components/domain/ProgressBar.vue'
import AlertMessage from '@/components/ui/AlertMessage.vue'
import PasswordInput from '@/components/ui/PasswordInput.vue'

const router = useRouter()
const auth = useAuthStore()
const badges = useBadgesStore()
const settings = useSettingsStore()

const initials = computed(() => {
  const n = auth.user?.name ?? ''
  const l = auth.user?.lastname ?? ''
  return ((n[0] ?? '') + (l[0] ?? '')).toUpperCase() || (auth.user?.email?.[0] ?? 'U').toUpperCase()
})
const fullName = computed(() =>
  [auth.user?.name, auth.user?.lastname].filter(Boolean).join(' ') || auth.displayName,
)

onMounted(() => {
  if (!badges.loaded) badges.fetchMyBadges()
})

const openSection = ref(null)
function toggle(key) {
  if (openSection.value === key) {
    openSection.value = null
    if (key === 'password') resetPwdSection()
  } else {
    openSection.value = key
  }
}

function accEnter(el) {
  el.style.overflow = 'hidden'
  el.style.height = '0'
  el.offsetHeight
  el.style.transition = 'height 0.4s cubic-bezier(0.34,1.15,0.64,1)'
  el.style.height = el.scrollHeight + 'px'
  el.style.animation = 'accReveal 0.45s cubic-bezier(0.34,1.4,0.64,1) both'
}
function accAfterEnter(el) {
  el.style.height = ''
  el.style.overflow = ''
  el.style.transition = ''
  el.style.animation = ''
}
function accLeave(el) {
  el.style.overflow = 'hidden'
  el.style.height = el.scrollHeight + 'px'
  el.style.opacity = '1'
  el.offsetHeight
  el.style.transition = 'height 0.35s cubic-bezier(0.2,0.7,0.2,1), opacity 0.25s ease'
  el.style.height = '0'
  el.style.opacity = '0'
}
function accAfterLeave(el) {
  el.style.height = ''
  el.style.overflow = ''
  el.style.transition = ''
  el.style.opacity = ''
}

function logout() {
  auth.logout()
  router.push('/login')
}

// Change password (2-step: email verification → new password)
const pwdStep = ref('email') // 'email' | 'code'
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
    pwdError.value = err.response?.data?.error ?? 'Error inesperado'
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
    pwdError.value = err.response?.data?.error ?? 'Error inesperado'
  } finally {
    pwdLoading.value = false
  }
}
</script>

<template>
  <div class="space-y-6 px-4 pb-4 pt-6">
    <header class="flex flex-col items-center gap-3 pt-2 text-center">
      <span class="grid h-20 w-20 place-items-center rounded-full bg-gradient-to-br from-primary to-secondary text-2xl font-bold text-primary-content">
        {{ initials }}
      </span>
      <div>
        <h1 class="text-xl font-bold">{{ fullName }}</h1>
        <p class="text-sm text-base-content/60">{{ auth.user?.email }}</p>
        <span class="badge badge-sm mt-2 border-0" :class="auth.isAdmin ? 'badge-secondary' : auth.isAssistant ? 'badge-accent' : 'badge-primary'">
          {{ auth.isAdmin ? $t('profile.organizer') : auth.isAssistant ? $t('profile.assistant') : $t('profile.attendee') }}
        </span>
      </div>
    </header>

    <section class="grid grid-cols-3 gap-3">
      <StatTile :value="badges.totalEarned" :label="$t('profile.badges')" tone="primary" />
      <StatTile :value="badges.eventsCount" :label="$t('profile.events')" tone="secondary" />
      <StatTile :value="badges.completedEvents" :label="$t('profile.done')" tone="accent" />
    </section>

    <section v-if="badges.groups.length" class="space-y-3">
      <h2 class="font-semibold">{{ $t('profile.progressByEvent') }}</h2>
      <div class="surface space-y-4 p-4">
        <div v-for="g in badges.groups" :key="g.event_id" class="space-y-1.5">
          <div class="flex items-center justify-between text-sm">
            <span class="truncate">{{ g.event }}</span>
            <span class="text-base-content/55">{{ g.badges_earned }}/{{ g.badges_total }}</span>
          </div>
          <ProgressBar :value="g.badges_earned" :max="g.badges_total" :show-count="false" />
        </div>
      </div>
    </section>

    <!-- Configuration -->
    <section class="space-y-2">
      <h2 class="font-semibold">{{ $t('settings.title') }}</h2>

      <!-- Language group -->
      <div class="surface overflow-hidden">
        <button
          type="button"
          class="flex w-full items-center justify-between gap-3 p-4 tap-target transition-colors"
          @click="toggle('language')"
        >
          <div class="flex items-center gap-3">
            <span class="grid h-9 w-9 shrink-0 place-items-center rounded-2xl bg-secondary/15 drop-shadow-[0_0_6px_rgba(167,139,250,0.3)]">
              <svg class="h-4.5 w-4.5 text-secondary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/>
              </svg>
            </span>
            <div class="text-left">
              <p class="text-sm font-semibold">{{ $t('settings.language') }}</p>
              <p class="text-xs text-base-content/50">{{ locale === 'en' ? 'English' : 'Español' }}</p>
            </div>
          </div>
          <svg
            class="h-4 w-4 shrink-0 text-base-content/40 transition-transform duration-300"
            :class="openSection === 'language' ? 'rotate-180' : ''"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"
          >
            <path d="M6 9l6 6 6-6"/>
          </svg>
        </button>
        <transition :css="false" @enter="accEnter" @after-enter="accAfterEnter" @leave="accLeave" @after-leave="accAfterLeave">
          <div v-if="openSection === 'language'" class="border-t border-base-300/60 px-4 pb-4 pt-4">
            <div class="surface-soft flex gap-2 p-1.5">
              <button
                type="button"
                class="tap-target flex-1 rounded-xl py-2 text-sm font-medium transition-colors"
                :class="locale === 'en' ? 'bg-primary text-primary-content' : 'text-base-content/60'"
                @click="setLocale('en')"
              >English</button>
              <button
                type="button"
                class="tap-target flex-1 rounded-xl py-2 text-sm font-medium transition-colors"
                :class="locale === 'es' ? 'bg-primary text-primary-content' : 'text-base-content/60'"
                @click="setLocale('es')"
              >Español</button>
            </div>
          </div>
        </transition>
      </div>
      <!-- Change password group -->
      <div class="surface overflow-hidden">
        <button
          type="button"
          class="flex w-full items-center justify-between gap-3 p-4 tap-target transition-colors"
          @click="toggle('password')"
        >
          <div class="flex items-center gap-3">
            <span class="grid h-9 w-9 shrink-0 place-items-center rounded-2xl bg-primary/15 drop-shadow-[0_0_6px_rgba(67,97,238,0.3)]">
              <svg class="h-4.5 w-4.5 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/>
              </svg>
            </span>
            <div class="text-left">
              <p class="text-sm font-semibold">{{ $t('settings.changePassword') }}</p>
              <p class="text-xs text-base-content/50">{{ $t('settings.changePasswordHint') }}</p>
            </div>
          </div>
          <svg
            class="h-4 w-4 shrink-0 text-base-content/40 transition-transform duration-300"
            :class="openSection === 'password' ? 'rotate-180' : ''"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"
          ><path d="M6 9l6 6 6-6"/></svg>
        </button>
        <transition :css="false" @enter="accEnter" @after-enter="accAfterEnter" @leave="accLeave" @after-leave="accAfterLeave">
          <div v-if="openSection === 'password'" class="border-t border-base-300/60 px-4 pb-5 pt-4">
            <AlertMessage type="error" :message="pwdError" />
            <AlertMessage v-if="pwdSuccess" type="success" :message="$t('settings.changePasswordSuccess')" />

            <!-- Step 1: email -->
            <form v-if="pwdStep === 'email'" class="mt-3 space-y-4" novalidate @submit.prevent="sendPwdCode">
              <p class="text-sm text-base-content/60">{{ $t('settings.changePasswordEmailStep') }}</p>
              <label class="form-control w-full">
                <span class="label-text mb-1 text-base-content/70">{{ $t('auth.email') }}</span>
                <input
                  v-model="pwdForm.email"
                  type="email"
                  inputmode="email"
                  autocomplete="email"
                  placeholder="you@email.com"
                  class="input input-bordered w-full bg-base-100/70"
                  :class="{ 'input-error': pwdEmailTouched && !pwdEmailValid }"
                />
                <span v-if="pwdEmailTouched && !pwdEmailValid" class="mt-1 text-xs text-error">{{ $t('auth.errEmail') }}</span>
              </label>
              <button type="submit" class="btn btn-primary w-full tap-target" :disabled="pwdLoading">
                <span v-if="pwdLoading" class="loading loading-spinner loading-sm" />
                {{ pwdLoading ? $t('settings.changePasswordSending') : $t('settings.changePasswordSendCode') }}
              </button>
            </form>

            <!-- Step 2: code + new password -->
            <form v-else class="mt-3 space-y-4" novalidate @submit.prevent="submitPasswordChange">
              <p class="text-sm text-base-content/60">
                {{ $t('settings.changePasswordCodeSent').replace('{email}', pwdForm.email) }}
              </p>

              <label class="form-control w-full">
                <span class="label-text mb-1 text-base-content/70">{{ $t('auth.resetCodeLabel') }}</span>
                <input
                  v-model="pwdForm.code"
                  type="text"
                  inputmode="numeric"
                  autocomplete="one-time-code"
                  maxlength="6"
                  placeholder="000000"
                  class="input input-bordered w-full bg-base-100/70 text-center text-2xl tracking-[.3em] font-bold"
                  :class="{ 'input-error': pwdCodeTouched && !pwdForm.code.trim() }"
                />
                <span v-if="pwdCodeTouched && !pwdForm.code.trim()" class="mt-1 text-xs text-error">{{ $t('auth.errOtpRequired') }}</span>
              </label>

              <label class="form-control w-full">
                <span class="label-text mb-1 text-base-content/70">{{ $t('settings.newPassword') }}</span>
                <PasswordInput
                  v-model="pwdForm.newPwd"
                  autocomplete="new-password"
                  :input-class="pwdCodeTouched && !newPwdValid ? 'input-error' : ''"
                />
                <ul v-if="pwdForm.newPwd || pwdCodeTouched" class="mt-2 space-y-1">
                  <li
                    v-for="rule in newPwdRules"
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
                  v-model="pwdForm.confirm"
                  autocomplete="new-password"
                  :input-class="pwdCodeTouched && !pwdsMatch ? 'input-error' : ''"
                />
                <span v-if="pwdCodeTouched && !pwdsMatch" class="mt-1 text-xs text-error">{{ $t('auth.errMatch') }}</span>
              </label>

              <button type="submit" class="btn btn-primary w-full tap-target" :disabled="pwdLoading">
                <span v-if="pwdLoading" class="loading loading-spinner loading-sm" />
                {{ pwdLoading ? $t('settings.changePasswordSubmitting') : $t('settings.changePasswordSubmit') }}
              </button>

              <div class="flex justify-between text-sm">
                <button type="button" class="text-base-content/50 hover:text-base-content" @click="resetPwdSection">
                  {{ $t('common.back') }}
                </button>
                <button type="button" class="text-primary" :disabled="pwdLoading" @click="sendPwdCode">
                  {{ pwdLoading ? $t('auth.resending') : $t('auth.resendReset') }}
                </button>
              </div>
            </form>
          </div>
        </transition>
      </div>

      <!-- Accessibility group -->
      <div class="surface overflow-hidden">
        <button
          type="button"
          class="flex w-full items-center justify-between gap-3 p-4 tap-target transition-colors"
          @click="toggle('accessibility')"
        >
          <div class="flex items-center gap-3">
            <span class="grid h-9 w-9 shrink-0 place-items-center rounded-2xl bg-accent/15 drop-shadow-[0_0_6px_rgba(251,191,36,0.3)]">
              <svg class="h-4.5 w-4.5 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/>
              </svg>
            </span>
            <div class="text-left">
              <p class="text-sm font-semibold">{{ $t('settings.accessibility') }}</p>
              <p class="text-xs text-base-content/50">{{ $t('settings.accessibilityHint') }}</p>
            </div>
          </div>
          <svg
            class="h-4 w-4 shrink-0 text-base-content/40 transition-transform duration-300"
            :class="openSection === 'accessibility' ? 'rotate-180' : ''"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"
          ><path d="M6 9l6 6 6-6"/></svg>
        </button>

        <transition :css="false" @enter="accEnter" @after-enter="accAfterEnter" @leave="accLeave" @after-leave="accAfterLeave">
          <div v-if="openSection === 'accessibility'" class="space-y-4 border-t border-base-300/60 px-4 pb-5 pt-4">

            <!-- TEXT & READABILITY -->
            <p class="text-[0.65rem] font-semibold uppercase tracking-widest text-base-content/40">{{ $t('settings.textReadability') }}</p>
            <div class="surface-soft space-y-4 p-4">
              <!-- Font size -->
              <div class="space-y-2">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2.5">
                    <span class="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-primary/15 text-sm font-bold text-primary">A</span>
                    <span class="text-sm font-medium">{{ $t('settings.fontSize') }}</span>
                  </div>
                  <span class="text-sm font-semibold tabular-nums text-primary">{{ settings.fontSize }}px</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-xs font-medium text-base-content/50">A</span>
                  <input v-model.number="settings.fontSize" type="range" class="range range-primary range-xs flex-1" :min="FONT_SIZE_RANGE.min" :max="FONT_SIZE_RANGE.max" :step="FONT_SIZE_RANGE.step" />
                  <span class="text-base font-bold text-base-content/50">A</span>
                </div>
              </div>

              <!-- Dyslexia font -->
              <label class="flex cursor-pointer items-center justify-between gap-3">
                <div class="flex items-center gap-2.5">
                  <span class="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-secondary/15 text-sm font-bold text-secondary">A</span>
                  <span>
                    <span class="block text-sm font-medium">{{ $t('settings.dyslexiaFont') }}</span>
                    <span class="block text-xs text-base-content/50">{{ $t('settings.dyslexiaFontHint') }}</span>
                  </span>
                </div>
                <input v-model="settings.dyslexiaFont" type="checkbox" class="toggle toggle-primary toggle-sm" />
              </label>

              <!-- Line spacing -->
              <label class="flex cursor-pointer items-center justify-between gap-3">
                <div class="flex items-center gap-2.5">
                  <span class="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-accent/15">
                    <svg class="h-4 w-4 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 6h16M4 10h16M4 14h16M4 18h16"/></svg>
                  </span>
                  <span>
                    <span class="block text-sm font-medium">{{ $t('settings.lineSpacing') }}</span>
                    <span class="block text-xs text-base-content/50">{{ $t('settings.lineSpacingHint') }}</span>
                  </span>
                </div>
                <input v-model="settings.lineSpacing" type="checkbox" class="toggle toggle-primary toggle-sm" />
              </label>

              <!-- Bold text -->
              <label class="flex cursor-pointer items-center justify-between gap-3">
                <div class="flex items-center gap-2.5">
                  <span class="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-primary/15 text-sm font-black text-primary">B</span>
                  <span>
                    <span class="block text-sm font-medium">{{ $t('settings.boldText') }}</span>
                    <span class="block text-xs text-base-content/50">{{ $t('settings.boldTextHint') }}</span>
                  </span>
                </div>
                <input v-model="settings.boldText" type="checkbox" class="toggle toggle-primary toggle-sm" />
              </label>

              <!-- Live preview -->
              <div class="rounded-2xl border border-base-300/50 bg-base-100/40 p-3">
                <p class="mb-1 text-[0.65rem] uppercase tracking-wider text-base-content/40">{{ $t('settings.preview') }}</p>
                <p class="text-sm leading-relaxed">{{ $t('settings.previewText') }}</p>
              </div>
            </div>

            <!-- COLOR & CONTRAST -->
            <p class="text-[0.65rem] font-semibold uppercase tracking-widest text-base-content/40">{{ $t('settings.colorContrast') }}</p>
            <div class="surface-soft space-y-4 p-4">
              <!-- Auto theme -->
              <label class="flex cursor-pointer items-center justify-between gap-3">
                <div class="flex items-center gap-2.5">
                  <span class="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-primary/15">
                    <svg class="h-4 w-4 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>
                  </span>
                  <span>
                    <span class="block text-sm font-medium">{{ $t('settings.autoTheme') }}</span>
                    <span class="block text-xs text-base-content/50">{{ $t('settings.autoThemeHint') }}</span>
                  </span>
                </div>
                <input v-model="settings.autoTheme" type="checkbox" class="toggle toggle-primary toggle-sm" />
              </label>

              <!-- High contrast -->
              <label class="flex cursor-pointer items-center justify-between gap-3">
                <div class="flex items-center gap-2.5">
                  <span class="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-secondary/15">
                    <svg class="h-4 w-4 text-secondary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 3v18"/></svg>
                  </span>
                  <span>
                    <span class="block text-sm font-medium">{{ $t('settings.highContrast') }}</span>
                    <span class="block text-xs text-base-content/50">{{ $t('settings.highContrastHint') }}</span>
                  </span>
                </div>
                <input v-model="settings.highContrast" type="checkbox" class="toggle toggle-primary toggle-sm" />
              </label>

              <!-- Color-blind -->
              <label class="flex cursor-pointer items-center justify-between gap-3">
                <div class="flex items-center gap-2.5">
                  <span class="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-accent/15">
                    <svg class="h-4 w-4 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  </span>
                  <span>
                    <span class="block text-sm font-medium">{{ $t('settings.colorBlind') }}</span>
                    <span class="block text-xs text-base-content/50">{{ $t('settings.colorBlindHint') }}</span>
                  </span>
                </div>
                <input v-model="settings.colorBlind" type="checkbox" class="toggle toggle-primary toggle-sm" />
              </label>

              <!-- Contrast level slider -->
              <div class="space-y-2">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2.5">
                    <span class="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-primary/15">
                      <svg class="h-4 w-4 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M4 6h16M7 12h10M10 18h4"/></svg>
                    </span>
                    <span class="text-sm font-medium">{{ $t('settings.contrastLevel') }}</span>
                  </div>
                  <span class="text-sm font-semibold tabular-nums text-primary">{{ Math.round((settings.contrast - CONTRAST_RANGE.min) / (CONTRAST_RANGE.max - CONTRAST_RANGE.min) * 100) }}%</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="text-xs text-base-content/50">{{ $t('settings.low') }}</span>
                  <input v-model.number="settings.contrast" type="range" class="range range-primary range-xs flex-1" :min="CONTRAST_RANGE.min" :max="CONTRAST_RANGE.max" :step="CONTRAST_RANGE.step" />
                  <span class="text-xs text-base-content/50">{{ $t('settings.high') }}</span>
                </div>
              </div>
            </div>

            <!-- MOTOR & INTERACTION -->
            <p class="text-[0.65rem] font-semibold uppercase tracking-widest text-base-content/40">{{ $t('settings.motorInteraction') }}</p>
            <div class="surface-soft space-y-4 p-4">
              <!-- Large tap targets -->
              <label class="flex cursor-pointer items-center justify-between gap-3">
                <div class="flex items-center gap-2.5">
                  <span class="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-primary/15">
                    <svg class="h-4 w-4 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="4"/><circle cx="12" cy="12" r="3"/></svg>
                  </span>
                  <span>
                    <span class="block text-sm font-medium">{{ $t('settings.largeTapTargets') }}</span>
                    <span class="block text-xs text-base-content/50">{{ $t('settings.largeTapTargetsHint') }}</span>
                  </span>
                </div>
                <input v-model="settings.largeTapTargets" type="checkbox" class="toggle toggle-primary toggle-sm" />
              </label>

              <!-- Focus highlight -->
              <label class="flex cursor-pointer items-center justify-between gap-3">
                <div class="flex items-center gap-2.5">
                  <span class="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-secondary/15">
                    <svg class="h-4 w-4 text-secondary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><rect x="2" y="2" width="20" height="20" rx="5"/><rect x="7" y="7" width="10" height="10" rx="2"/></svg>
                  </span>
                  <span>
                    <span class="block text-sm font-medium">{{ $t('settings.focusHighlight') }}</span>
                    <span class="block text-xs text-base-content/50">{{ $t('settings.focusHighlightHint') }}</span>
                  </span>
                </div>
                <input v-model="settings.focusHighlight" type="checkbox" class="toggle toggle-primary toggle-sm" />
              </label>
            </div>

            <button type="button" class="btn btn-outline btn-primary btn-sm w-full tap-target" @click="settings.reset()">
              {{ $t('settings.reset') }}
            </button>
          </div>
        </transition>
      </div>
    </section>

    <RouterLink v-if="auth.isStaff" to="/admin/events" class="btn btn-outline w-full tap-target">
      {{ $t('profile.openAdmin') }}
    </RouterLink>

    <button class="btn btn-ghost w-full text-error tap-target" @click="logout">{{ $t('common.logout') }}</button>
  </div>
</template>
