import { defineStore } from 'pinia'
import { ref, watch, nextTick } from 'vue'
import { api } from '@/services/api'
import { locale, setLocale } from '@/i18n'

const KEY = 'lyfter_settings'
const DEFAULTS = {
  effects: true, lightMode: false, saturation: 1, contrast: 1,
  fontSize: 16, dyslexiaFont: false, lineSpacing: false, boldText: false,
  autoTheme: false, highContrast: false, colorBlind: false,
  largeTapTargets: false, focusHighlight: false,
}

export const SATURATION_RANGE = { min: 0.5, max: 1.5, step: 0.05 }
export const CONTRAST_RANGE   = { min: 0.8, max: 1.2, step: 0.02 }
export const FONT_SIZE_RANGE  = { min: 14,  max: 22,  step: 1 }

function loadCache() {
  try { return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(KEY) || '{}') } }
  catch { return { ...DEFAULTS } }
}

const clamp = (n, { min, max }, fallback) => {
  const v = Number(n)
  return Number.isFinite(v) ? Math.min(max, Math.max(min, v)) : fallback
}

export const useSettingsStore = defineStore('settings', () => {
  const cached = loadCache()

  const effects        = ref(!!cached.effects)
  const lightMode      = ref(!!cached.lightMode)
  const saturation     = ref(clamp(cached.saturation, SATURATION_RANGE, DEFAULTS.saturation))
  const contrast       = ref(clamp(cached.contrast,   CONTRAST_RANGE,   DEFAULTS.contrast))
  const fontSize       = ref(clamp(cached.fontSize,   FONT_SIZE_RANGE,  DEFAULTS.fontSize))
  const dyslexiaFont   = ref(!!cached.dyslexiaFont)
  const lineSpacing    = ref(!!cached.lineSpacing)
  const boldText       = ref(!!cached.boldText)
  const autoTheme      = ref(!!cached.autoTheme)
  const highContrast   = ref(!!cached.highContrast)
  const colorBlind     = ref(!!cached.colorBlind)
  const largeTapTargets = ref(!!cached.largeTapTargets)
  const focusHighlight  = ref(!!cached.focusHighlight)

  let hydrating = false
  let saveTimer = null

  function apply() {
    if (typeof document === 'undefined') return
    const el = document.documentElement

    const useLight = autoTheme.value
      ? (typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: light)').matches)
      : lightMode.value
    el.dataset.theme = useLight ? 'tokenteam-light' : 'tokenteam'
    el.classList.toggle('theme-light', useLight)
    el.style.colorScheme = useLight ? 'light' : 'dark'
    el.classList.toggle('fx-off', !effects.value)

    el.style.fontSize = fontSize.value !== 16 ? `${fontSize.value}px` : ''
    el.classList.toggle('dyslexia-font',    dyslexiaFont.value)
    el.classList.toggle('line-spacing',     lineSpacing.value)
    el.classList.toggle('bold-text',        boldText.value)
    el.classList.toggle('high-contrast',    highContrast.value)
    el.classList.toggle('color-blind',      colorBlind.value)
    el.classList.toggle('large-targets',    largeTapTargets.value)
    el.classList.toggle('focus-highlight',  focusHighlight.value)
  }

  function persistCache() {
    try {
      localStorage.setItem(KEY, JSON.stringify({
        effects: effects.value, lightMode: lightMode.value,
        saturation: saturation.value, contrast: contrast.value,
        fontSize: fontSize.value, dyslexiaFont: dyslexiaFont.value,
        lineSpacing: lineSpacing.value, boldText: boldText.value,
        autoTheme: autoTheme.value, highContrast: highContrast.value,
        colorBlind: colorBlind.value, largeTapTargets: largeTapTargets.value,
        focusHighlight: focusHighlight.value,
      }))
    } catch { /* storage unavailable */ }
  }

  function payload() {
    return {
      language: locale.value, lightMode: lightMode.value, effects: effects.value,
      saturation: saturation.value, contrast: contrast.value,
      fontSize: fontSize.value, dyslexiaFont: dyslexiaFont.value,
      lineSpacing: lineSpacing.value, boldText: boldText.value,
      autoTheme: autoTheme.value, highContrast: highContrast.value,
      colorBlind: colorBlind.value, largeTapTargets: largeTapTargets.value,
      focusHighlight: focusHighlight.value,
    }
  }

  async function saveToServer() {
    const { useAuthStore } = await import('@/stores/auth')
    if (!useAuthStore().isAuthenticated) return
    try { await api.put('/me/settings', payload()) } catch { /* offline */ }
  }

  function scheduleSave() {
    if (saveTimer) clearTimeout(saveTimer)
    saveTimer = setTimeout(saveToServer, 500)
  }

  function hydrate(prefs) {
    if (!prefs || typeof prefs !== 'object') return
    hydrating = true
    if (prefs.language) setLocale(prefs.language)
    if (typeof prefs.effects   === 'boolean') effects.value   = prefs.effects
    if (typeof prefs.lightMode === 'boolean') lightMode.value = prefs.lightMode
    if (prefs.saturation != null) saturation.value = clamp(prefs.saturation, SATURATION_RANGE, saturation.value)
    if (prefs.contrast   != null) contrast.value   = clamp(prefs.contrast,   CONTRAST_RANGE,   contrast.value)
    if (prefs.fontSize   != null) fontSize.value   = clamp(prefs.fontSize,   FONT_SIZE_RANGE,  fontSize.value)
    if (typeof prefs.dyslexiaFont    === 'boolean') dyslexiaFont.value    = prefs.dyslexiaFont
    if (typeof prefs.lineSpacing     === 'boolean') lineSpacing.value     = prefs.lineSpacing
    if (typeof prefs.boldText        === 'boolean') boldText.value        = prefs.boldText
    if (typeof prefs.autoTheme       === 'boolean') autoTheme.value       = prefs.autoTheme
    if (typeof prefs.highContrast    === 'boolean') highContrast.value    = prefs.highContrast
    if (typeof prefs.colorBlind      === 'boolean') colorBlind.value      = prefs.colorBlind
    if (typeof prefs.largeTapTargets === 'boolean') largeTapTargets.value = prefs.largeTapTargets
    if (typeof prefs.focusHighlight  === 'boolean') focusHighlight.value  = prefs.focusHighlight
    apply()
    persistCache()
    nextTick(() => { hydrating = false })
  }

  function reset() {
    effects.value = DEFAULTS.effects; lightMode.value = DEFAULTS.lightMode
    saturation.value = DEFAULTS.saturation; contrast.value = DEFAULTS.contrast
    fontSize.value = DEFAULTS.fontSize; dyslexiaFont.value = DEFAULTS.dyslexiaFont
    lineSpacing.value = DEFAULTS.lineSpacing; boldText.value = DEFAULTS.boldText
    autoTheme.value = DEFAULTS.autoTheme; highContrast.value = DEFAULTS.highContrast
    colorBlind.value = DEFAULTS.colorBlind; largeTapTargets.value = DEFAULTS.largeTapTargets
    focusHighlight.value = DEFAULTS.focusHighlight
  }

  watch([effects, lightMode, autoTheme, highContrast, colorBlind, dyslexiaFont,
         lineSpacing, boldText, largeTapTargets, focusHighlight, fontSize], apply)
  watch([effects, lightMode, saturation, contrast, fontSize, dyslexiaFont,
         lineSpacing, boldText, autoTheme, highContrast, colorBlind,
         largeTapTargets, focusHighlight, locale], () => {
    if (hydrating) return
    persistCache()
    scheduleSave()
  })

  return {
    effects, lightMode, saturation, contrast,
    fontSize, dyslexiaFont, lineSpacing, boldText,
    autoTheme, highContrast, colorBlind, largeTapTargets, focusHighlight,
    apply, hydrate, reset,
  }
})
