<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { locale, setLocale } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import { useBadgesStore } from '@/stores/badges'
import { useSettingsStore, SATURATION_RANGE, CONTRAST_RANGE } from '@/stores/settings'
import StatTile from '@/components/domain/StatTile.vue'
import ProgressBar from '@/components/domain/ProgressBar.vue'

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
  openSection.value = openSection.value === key ? null : key
}

function logout() {
  auth.logout()
  router.push('/login')
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

      <!-- Appearance group -->
      <div class="surface overflow-hidden">
        <button
          type="button"
          class="flex w-full items-center justify-between gap-3 p-4 tap-target transition-colors"
          @click="toggle('appearance')"
        >
          <div class="flex items-center gap-3">
            <span class="grid h-9 w-9 shrink-0 place-items-center rounded-2xl bg-primary/15 drop-shadow-[0_0_6px_rgba(45,212,191,0.3)]">
              <svg class="h-4.5 w-4.5 text-primary" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>
              </svg>
            </span>
            <div class="text-left">
              <p class="text-sm font-semibold">{{ $t('settings.appearance') }}</p>
              <p class="text-xs text-base-content/50">{{ $t('settings.appearanceHint') }}</p>
            </div>
          </div>
          <svg
            class="h-4 w-4 shrink-0 text-base-content/40 transition-transform duration-300"
            :class="openSection === 'appearance' ? 'rotate-180' : ''"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"
          >
            <path d="M6 9l6 6 6-6"/>
          </svg>
        </button>
        <transition name="accordion">
          <div v-if="openSection === 'appearance'" class="space-y-5 border-t border-base-300/60 px-4 pb-5 pt-4">
            <label class="flex cursor-pointer items-center justify-between gap-3">
              <span>
                <span class="block text-sm font-medium">{{ $t('settings.lightMode') }}</span>
                <span class="block text-xs text-base-content/55">{{ $t('settings.lightModeHint') }}</span>
              </span>
              <input v-model="settings.lightMode" type="checkbox" class="toggle toggle-primary" />
            </label>
            <label class="flex cursor-pointer items-center justify-between gap-3">
              <span>
                <span class="block text-sm font-medium">{{ $t('settings.effects') }}</span>
                <span class="block text-xs text-base-content/55">{{ $t('settings.effectsHint') }}</span>
              </span>
              <input v-model="settings.effects" type="checkbox" class="toggle toggle-primary" />
            </label>
            <div class="space-y-1.5">
              <div class="flex items-center justify-between">
                <span class="text-sm font-medium">{{ $t('settings.saturation') }}</span>
                <span class="text-xs tabular-nums text-base-content/55">{{ Math.round(settings.saturation * 100) }}%</span>
              </div>
              <input v-model.number="settings.saturation" type="range" class="range range-primary range-sm" :min="SATURATION_RANGE.min" :max="SATURATION_RANGE.max" :step="SATURATION_RANGE.step" />
            </div>
            <div class="space-y-1.5">
              <div class="flex items-center justify-between">
                <span class="text-sm font-medium">{{ $t('settings.contrast') }}</span>
                <span class="text-xs tabular-nums text-base-content/55">{{ Math.round(settings.contrast * 100) }}%</span>
              </div>
              <input v-model.number="settings.contrast" type="range" class="range range-primary range-sm" :min="CONTRAST_RANGE.min" :max="CONTRAST_RANGE.max" :step="CONTRAST_RANGE.step" />
            </div>
            <button type="button" class="btn btn-outline btn-primary btn-sm w-full tap-target" @click="settings.reset()">
              {{ $t('settings.reset') }}
            </button>
          </div>
        </transition>
      </div>

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
        <transition name="accordion">
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
    </section>

    <RouterLink v-if="auth.isStaff" to="/admin/events" class="btn btn-outline w-full tap-target">
      {{ $t('profile.openAdmin') }}
    </RouterLink>

    <button class="btn btn-ghost w-full text-error tap-target" @click="logout">{{ $t('common.logout') }}</button>
  </div>
</template>
