<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { locale, setLocale } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import { useBadgesStore } from '@/stores/badges'
import StatTile from '@/components/domain/StatTile.vue'
import ProgressBar from '@/components/domain/ProgressBar.vue'

const router = useRouter()
const auth = useAuthStore()
const badges = useBadgesStore()

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

    <!-- Language setting -->
    <section class="space-y-2">
      <h2 class="font-semibold">{{ $t('profile.language') }}</h2>
      <div class="surface flex gap-2 p-2">
        <button
          type="button"
          class="tap-target flex-1 rounded-xl py-2 text-sm font-medium transition-colors"
          :class="locale === 'en' ? 'bg-primary text-primary-content' : 'text-base-content/60'"
          @click="setLocale('en')"
        >
          English
        </button>
        <button
          type="button"
          class="tap-target flex-1 rounded-xl py-2 text-sm font-medium transition-colors"
          :class="locale === 'es' ? 'bg-primary text-primary-content' : 'text-base-content/60'"
          @click="setLocale('es')"
        >
          Español
        </button>
      </div>
    </section>

    <RouterLink v-if="auth.isStaff" to="/admin/events" class="btn btn-outline w-full tap-target">
      {{ $t('profile.openAdmin') }}
    </RouterLink>

    <button class="btn btn-ghost w-full text-error tap-target" @click="logout">{{ $t('common.logout') }}</button>
  </div>
</template>
