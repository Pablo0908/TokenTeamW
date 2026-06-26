import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { setLocale } from '@/i18n'

// First-run flow: greet the user + ask their language, then walk them through the home
// screen one coachmark at a time (scan -> badges -> events).
// Tracked PER USER (by account id) so every new email that signs in for the first time
// gets it — not just the first user on a given device.
const COMPLETED_KEY = 'lyfter_onboarded_users'
const TIP_ORDER = ['streak', 'scan', 'badges', 'events']

function completedIds() {
  try {
    return JSON.parse(localStorage.getItem(COMPLETED_KEY) || '[]')
  } catch {
    return []
  }
}
function markCompleted(id) {
  if (!id) return
  const ids = completedIds()
  if (!ids.includes(id)) {
    ids.push(id)
    try {
      localStorage.setItem(COMPLETED_KEY, JSON.stringify(ids))
    } catch {
      /* storage unavailable */
    }
  }
}

export const useOnboardingStore = defineStore('onboarding', () => {
  const welcomeOpen = ref(false)
  const tipsActive = ref(false)
  const dismissed = ref({})
  const userId = ref(null)

  // Start the flow for a user who hasn't completed it yet (first sign-in / registration).
  function maybeStart(id) {
    userId.value = id || null
    if (id && completedIds().includes(id)) return
    dismissed.value = {}
    tipsActive.value = false
    welcomeOpen.value = true
  }

  // Replay the whole flow on demand (e.g. ?welcome=1), ignoring completion state.
  function forceStart(id) {
    if (id) userId.value = id
    dismissed.value = {}
    tipsActive.value = false
    welcomeOpen.value = true
  }

  function chooseLanguage(value) {
    setLocale(value)
    welcomeOpen.value = false
    tipsActive.value = true
  }

  // One coachmark at a time, in order; null when finished.
  const currentTip = computed(() =>
    tipsActive.value ? TIP_ORDER.find((k) => !dismissed.value[k]) ?? null : null,
  )
  const showTip = (key) => currentTip.value === key

  function dismissTip(key) {
    if (!tipsActive.value) return
    dismissed.value = { ...dismissed.value, [key]: true }
    if (TIP_ORDER.every((k) => dismissed.value[k])) finish()
  }

  function finish() {
    tipsActive.value = false
    welcomeOpen.value = false
    markCompleted(userId.value)
  }

  return { welcomeOpen, tipsActive, currentTip, maybeStart, forceStart, chooseLanguage, showTip, dismissTip, finish }
})
