<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { locale, setLocale } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import { useOrgContextStore } from '@/stores/orgContext'
import { useBadgesStore } from '@/stores/badges'
import { useSettingsStore, CONTRAST_RANGE, FONT_SIZE_RANGE } from '@/stores/settings'
import ProgressBar from '@/components/domain/ProgressBar.vue'

const router = useRouter()
const auth = useAuthStore()
const orgContext = useOrgContextStore()
const badges = useBadgesStore()
const settings = useSettingsStore()

const showAccessibility = ref(false)

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

function accEnter(el) {
  el.style.overflow = 'hidden'
  el.style.height = '0'
  el.offsetHeight
  el.style.transition = 'height 0.35s cubic-bezier(0.2,0.7,0.2,1)'
  el.style.height = el.scrollHeight + 'px'
}
function accAfterEnter(el) {
  el.style.height = ''
  el.style.overflow = ''
  el.style.transition = ''
}
function accLeave(el) {
  el.style.overflow = 'hidden'
  el.style.height = el.scrollHeight + 'px'
  el.offsetHeight
  el.style.transition = 'height 0.3s cubic-bezier(0.2,0.7,0.2,1), opacity 0.2s ease'
  el.style.height = '0'
  el.style.opacity = '0'
}
function accAfterLeave(el) {
  el.style.height = ''
  el.style.overflow = ''
  el.style.transition = ''
  el.style.opacity = ''
}
</script>

<template>
  <div class="space-y-6 px-4 pb-4 pt-6">
    <!-- Profile Settings nav card -->
    <section class="space-y-2">
      <h2 class="font-semibold">{{ $t('settings.profileSettings') }}</h2>
      <RouterLink
        to="/profile/settings"
        class="surface flex items-center gap-3 p-4 transition-transform active:scale-[0.98]"
      >
        <!-- Avatar or initials -->
        <span class="relative h-11 w-11 shrink-0">
          <img
            v-if="auth.user?.avatar_url"
            :src="auth.user.avatar_url"
            class="h-11 w-11 rounded-full object-cover"
            alt=""
          />
          <span
            v-else
            class="grid h-11 w-11 place-items-center rounded-full bg-gradient-to-br from-primary to-secondary text-sm font-bold text-primary-content"
          >{{ initials }}</span>
        </span>
        <div class="min-w-0 flex-1">
          <p class="font-semibold">{{ fullName }}</p>
          <p class="truncate text-sm text-base-content/55">{{ auth.user?.email }}</p>
        </div>
        <svg class="h-4 w-4 shrink-0 text-base-content/40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 18l6-6-6-6"/>
        </svg>
      </RouterLink>
    </section>

    <!-- Settings -->
    <section class="space-y-2">
      <h2 class="font-semibold">{{ $t('settings.title') }}</h2>

      <!-- Language -->
      <div class="surface p-4">
        <div class="flex items-center justify-between gap-3">
          <div class="flex items-center gap-3">
            <span class="grid h-9 w-9 shrink-0 place-items-center rounded-2xl bg-secondary/15 drop-shadow-[0_0_6px_rgba(167,139,250,0.3)]">
              <svg class="h-4 w-4 text-secondary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/>
              </svg>
            </span>
            <p class="text-sm font-semibold">{{ $t('settings.language') }}</p>
          </div>
          <div class="surface-soft flex gap-1 rounded-xl p-1">
            <button
              type="button"
              class="tap-target rounded-lg px-3 py-1.5 text-sm font-medium transition-colors"
              :class="locale === 'en' ? 'bg-primary text-primary-content' : 'text-base-content/60'"
              @click="setLocale('en')"
            >EN</button>
            <button
              type="button"
              class="tap-target rounded-lg px-3 py-1.5 text-sm font-medium transition-colors"
              :class="locale === 'es' ? 'bg-primary text-primary-content' : 'text-base-content/60'"
              @click="setLocale('es')"
            >ES</button>
          </div>
        </div>
      </div>

      <!-- Accessibility — collapsible -->
      <div class="surface overflow-hidden">
        <button
          type="button"
          class="flex w-full items-center justify-between gap-3 p-4 tap-target transition-colors"
          @click="showAccessibility = !showAccessibility"
        >
          <div class="flex items-center gap-3">
            <span class="grid h-9 w-9 shrink-0 place-items-center rounded-2xl bg-accent/15 drop-shadow-[0_0_6px_rgba(251,191,36,0.3)]">
              <svg class="h-4 w-4 text-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="7" r="4"/><path d="M4 21v-1a8 8 0 0116 0v1"/>
              </svg>
            </span>
            <div class="text-left">
              <p class="text-sm font-semibold">{{ $t('settings.accessibility') }}</p>
              <p class="text-xs text-base-content/50">{{ $t('settings.accessibilityHint') }}</p>
            </div>
          </div>
          <svg
            class="h-4 w-4 shrink-0 text-base-content/40 transition-transform duration-300"
            :class="showAccessibility ? 'rotate-180' : ''"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"
          ><path d="M6 9l6 6 6-6"/></svg>
        </button>

        <transition :css="false" @enter="accEnter" @after-enter="accAfterEnter" @leave="accLeave" @after-leave="accAfterLeave">
          <div v-if="showAccessibility" class="space-y-4 border-t border-base-300/60 px-4 pb-5 pt-4">
            <p class="text-[0.65rem] font-semibold uppercase tracking-widest text-base-content/40">{{ $t('settings.textReadability') }}</p>

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

            <p class="text-[0.65rem] font-semibold uppercase tracking-widest text-base-content/40">{{ $t('settings.colorContrast') }}</p>

            <!-- Follow system dark mode -->
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

            <!-- Contrast level -->
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

            <button type="button" class="btn btn-outline btn-primary btn-sm w-full tap-target" @click="settings.reset()">
              {{ $t('settings.reset') }}
            </button>
          </div>
        </transition>
      </div>
    </section>

    <!-- Progress by event (below settings) -->
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

    <RouterLink
      to="/invites"
      class="surface flex items-center gap-3 p-4 transition-transform active:scale-[0.98]"
    >
      <span class="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-primary/15 drop-shadow-[0_0_6px_rgba(99,102,241,0.3)]">
        <svg class="h-5 w-5 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/>
          <circle cx="9" cy="7" r="4"/>
          <path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/>
        </svg>
      </span>
      <div class="flex-1">
        <p class="text-sm font-semibold">Invitations</p>
        <p class="text-xs text-base-content/50">View &amp; manage your invites</p>
      </div>
      <svg class="h-4 w-4 shrink-0 text-base-content/40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M9 18l6-6-6-6"/>
      </svg>
    </RouterLink>

    <RouterLink v-if="orgContext.isSuperAdmin" to="/admin/events" class="btn btn-outline w-full tap-target">
      {{ $t('profile.openAdmin') }}
    </RouterLink>
    <RouterLink v-if="orgContext.isOrgMember" to="/org/events" class="btn btn-outline w-full tap-target">
      Manage organization
    </RouterLink>
  </div>
</template>
