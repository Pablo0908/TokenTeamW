// Per-org theming: temporarily override DaisyUI's color CSS variables on the document
// root so org-scoped screens (org panel) and an org's event screens adopt the org's brand
// colors. Mirrors the appearance hook in stores/settings.js (which sets data-theme +
// classes); we layer inline --p/--s/--a on top and clear them to revert.
//
// DaisyUI colors are HSL channels in the form "H S% L%", consumed as hsl(var(--p)).

function hexToHsl(hex) {
  if (typeof hex !== 'string') return null
  let h = hex.trim().replace('#', '')
  if (h.length === 3) h = h.split('').map((c) => c + c).join('')
  if (h.length !== 6) return null
  const r = parseInt(h.slice(0, 2), 16) / 255
  const g = parseInt(h.slice(2, 4), 16) / 255
  const b = parseInt(h.slice(4, 6), 16) / 255
  const max = Math.max(r, g, b), min = Math.min(r, g, b)
  let hue = 0, sat = 0
  const l = (max + min) / 2
  const d = max - min
  if (d !== 0) {
    sat = d / (1 - Math.abs(2 * l - 1))
    if (max === r) hue = ((g - b) / d) % 6
    else if (max === g) hue = (b - r) / d + 2
    else hue = (r - g) / d + 4
    hue *= 60
    if (hue < 0) hue += 360
  }
  return { h: Math.round(hue), s: Math.round(sat * 100), l: Math.round(l * 100), lum: l }
}

// DaisyUI variable name per theme key + its "content" (text-on-color) companion.
const VARS = {
  primary: ['--p', '--pc'],
  secondary: ['--s', '--sc'],
  accent: ['--a', '--ac'],
}

let applied = false

export function applyOrgTheme(theme) {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  let touched = false
  for (const [key, [base, content]] of Object.entries(VARS)) {
    const hsl = theme && hexToHsl(theme[key])
    if (!hsl) continue
    root.style.setProperty(base, `${hsl.h} ${hsl.s}% ${hsl.l}%`)
    // Readable text on the brand color: dark text on light fills, light text on dark.
    root.style.setProperty(content, hsl.lum > 0.6 ? '0 0% 12%' : '0 0% 100%')
    touched = true
  }
  applied = applied || touched
}

export function clearOrgTheme() {
  if (typeof document === 'undefined' || !applied) return
  const root = document.documentElement
  for (const [, [base, content]] of Object.entries(VARS)) {
    root.style.removeProperty(base)
    root.style.removeProperty(content)
  }
  applied = false
}

export function hasOrgColors(theme) {
  return !!(theme && (theme.primary || theme.secondary || theme.accent))
}
