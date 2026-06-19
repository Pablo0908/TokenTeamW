import { defineStore } from 'pinia'
import { ref, watch, nextTick } from 'vue'
import { api } from '@/services/api'
import { locale, setLocale } from '@/i18n'

// User appearance/behaviour preferences.
// Source of truth is the server (a `preferences` object on the user document), so a
// choice follows the account across devices and survives redeploys. localStorage is a
// fast-boot/offline cache only: it themes the app instantly on reload, then the server
// copy is hydrated right after login. Language is owned by i18n but synced here too.
const KEY = 'lyfter_settings'
const DEFAULTS = { effects: true, lightMode: false, saturation: 1, contrast: 1 }

// Slider bounds (kept modest so the app stays legible at the extremes).
export const SATURATION_RANGE = { min: 0.5, max: 1.5, step: 0.05 }
export const CONTRAST_RANGE = { min: 0.8, max: 1.2, step: 0.02 }

function loadCache() {
  try {
    return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(KEY) || '{}') }
  } catch {
    return { ...DEFAULTS }
  }
}

const clamp = (n, { min, max }, fallback) => {
  const v = Number(n)
  return Number.isFinite(v) ? Math.min(max, Math.max(min, v)) : fallback
}

export const useSettingsStore = defineStore('settings', () => {
  const cached = loadCache()
  const effects = ref(!!cached.effects)
  const lightMode = ref(!!cached.lightMode)
  const saturation = ref(clamp(cached.saturation, SATURATION_RANGE, DEFAULTS.saturation))
  const contrast = ref(clamp(cached.contrast, CONTRAST_RANGE, DEFAULTS.contrast))

  // True while applying server values, so the watcher doesn't echo them straight back.
  let hydrating = false
  let saveTimer = null

  // Push the current preferences onto the document. Safe to call before mount.
  function apply() {
    if (typeof document === 'undefined') return
    const el = document.documentElement
    el.dataset.theme = lightMode.value ? 'tokenteam-light' : 'tokenteam'
    el.classList.toggle('theme-light', lightMode.value)
    el.classList.toggle('fx-off', !effects.value)
    el.style.colorScheme = lightMode.value ? 'light' : 'dark'
  }

  function persistCache() {
    try {
      localStorage.setItem(
        KEY,
        JSON.stringify({
          effects: effects.value,
          lightMode: lightMode.value,
          saturation: saturation.value,
          contrast: contrast.value,
        }),
      )
    } catch {
      /* storage unavailable */
    }
  }

  function payload() {
    return {
      language: locale.value,
      lightMode: lightMode.value,
      effects: effects.value,
      saturation: saturation.value,
      contrast: contrast.value,
    }
  }

  // Persist to the server (debounced). Only when signed in; the server attaches the
  // JWT via the api interceptor. A failed save keeps the local copy — no user-facing error.
  async function saveToServer() {
    const { useAuthStore } = await import('@/stores/auth')
    if (!useAuthStore().isAuthenticated) return
    try {
      await api.put('/me/settings', payload())
    } catch {
      /* offline or transient — local cache already holds the change */
    }
  }

  function scheduleSave() {
    if (saveTimer) clearTimeout(saveTimer)
    saveTimer = setTimeout(saveToServer, 500)
  }

  // Apply server-stored preferences after login (server wins when signed in).
  function hydrate(prefs) {
    if (!prefs || typeof prefs !== 'object') return
    hydrating = true
    if (prefs.language) setLocale(prefs.language)
    if (typeof prefs.effects === 'boolean') effects.value = prefs.effects
    if (typeof prefs.lightMode === 'boolean') lightMode.value = prefs.lightMode
    if (prefs.saturation != null) saturation.value = clamp(prefs.saturation, SATURATION_RANGE, saturation.value)
    if (prefs.contrast != null) contrast.value = clamp(prefs.contrast, CONTRAST_RANGE, contrast.value)
    apply()
    persistCache()
    // Release the guard only after the triggered watchers have flushed this tick.
    nextTick(() => {
      hydrating = false
    })
  }

  function reset() {
    effects.value = DEFAULTS.effects
    lightMode.value = DEFAULTS.lightMode
    saturation.value = DEFAULTS.saturation
    contrast.value = DEFAULTS.contrast
  }

  // Theme/class changes apply immediately. Any change also caches locally and (when
  // signed in) syncs to the server. `locale` is watched so a language switch persists too.
  watch([effects, lightMode], apply)
  watch([effects, lightMode, saturation, contrast, locale], () => {
    if (hydrating) return
    persistCache()
    scheduleSave()
  })

  return { effects, lightMode, saturation, contrast, apply, hydrate, reset }
})
