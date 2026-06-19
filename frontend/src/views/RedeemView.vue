<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { t } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import { useBadgesStore } from '@/stores/badges'
import Confetti from '@/components/domain/Confetti.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const badges = useBadgesStore()

const state = ref('working') // working | result
const result = ref(null)

const celebrating = computed(() => ['success', 'completed'].includes(result.value?.kind))

function outcomeFor(status) {
  switch (status) {
    case 409:
      return { kind: 'duplicate', title: t('outcome.duplicateTitle'), message: t('outcome.duplicateMsg') }
    case 403:
      return { kind: 'error', title: t('outcome.notAvailableTitle'), message: t('outcome.notAvailableMsg') }
    case 410:
      return { kind: 'error', title: t('outcome.limitTitle'), message: t('outcome.limitMsg') }
    case 401:
      return { kind: 'error', title: t('outcome.sessionTitle'), message: t('outcome.sessionMsg') }
    default:
      return null
  }
}

async function redeem() {
  const { eventId, token } = route.params
  const res = await badges.redeem(eventId, token)
  if (res.ok) {
    const completed = res.data.event_completed
    result.value = {
      kind: completed ? 'completed' : 'success',
      title: completed ? t('outcome.eventCompleted') : t('outcome.badgeEarned'),
      badge: res.data.badge,
      event: res.data.event,
      prize: res.data.prize,
    }
  } else {
    result.value = outcomeFor(res.status) || {
      kind: 'error',
      title: t('redeem.failTitle'),
      message: res.error || t('outcome.genericMsg'),
    }
  }
  state.value = 'result'
}

onMounted(() => {
  // Public QR landing: send unauthenticated users to login, then back here (TDD §5).
  if (!auth.isAuthenticated) {
    auth.setRedirect(route.fullPath)
    router.replace('/login')
    return
  }
  redeem()
})
</script>

<template>
  <div class="flex min-h-dvh flex-col items-center justify-center px-6 py-10 text-center">
    <Confetti :active="celebrating" />

    <LoadingSpinner v-if="state === 'working'" :label="$t('redeem.working')" />

    <div v-else class="flex w-full flex-col items-center gap-5">
      <div
        class="grid h-28 w-28 place-items-center rounded-full text-6xl shadow-2xl"
        :class="{
          'bg-gradient-to-br from-success/30 to-primary/20 shadow-success/30': celebrating,
          'bg-warning/15 shadow-warning/20': result.kind === 'duplicate',
          'bg-error/15 shadow-error/20': result.kind === 'error',
        }"
      >
        <template v-if="celebrating">{{ result.badge?.icon || '🏅' }}</template>
        <template v-else-if="result.kind === 'duplicate'">✅</template>
        <template v-else>⚠️</template>
      </div>

      <div>
        <h1 class="text-2xl font-bold">{{ result.title }}</h1>
        <p v-if="result.badge" class="mt-1 text-base-content/70">{{ result.badge.name }} · {{ result.event }}</p>
        <p v-else class="mt-1 text-base-content/70">{{ result.message }}</p>
      </div>

      <div
        v-if="result.kind === 'completed' && result.prize"
        class="surface w-full max-w-sm bg-gradient-to-r from-warning/20 to-secondary/15 p-4"
      >
        <p class="text-xs uppercase tracking-wide text-base-content/55">{{ $t('outcome.prizeUnlocked') }}</p>
        <p class="mt-1 font-semibold text-warning">🎁 {{ result.prize }}</p>
      </div>

      <div class="w-full max-w-sm space-y-2">
        <button class="btn btn-primary w-full tap-target" @click="router.push('/badges')">{{ $t('redeem.viewCollection') }}</button>
        <button class="btn btn-ghost w-full tap-target" @click="router.push('/scan')">{{ $t('redeem.scanAnother') }}</button>
      </div>
    </div>
  </div>
</template>
