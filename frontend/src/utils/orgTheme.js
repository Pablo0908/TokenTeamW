// Per-org theming: temporarily override DaisyUI's color CSS variables on the document
// root so org-scoped screens (org panel) and an org's event screens adopt the org's brand
// colors. Mirrors the appearance hook in stores/settings.js (which sets data-theme +
// classes); we layer inline --p/--s/--a on top and clear them to revert.
//
// DaisyUI (v4) colors are HSL channels in the form "H S% L%", consumed as hsl(var(--p)).

function parseHex(hex) {
  if (typeof hex !== 'string') return null
  let h = hex.trim().replace('#', '')
  if (h.length === 3) h = h.split('').map((c) => c + c).join('')
  if (h.length !== 6 || /[^0-9a-fA-F]/.test(h)) return null
  return {
    r: parseInt(h.slice(0, 2), 16) / 255,
    g: parseInt(h.slice(2, 4), 16) / 255,
    b: parseInt(h.slice(4, 6), 16) / 255,
  }
}

function hexToHsl(hex) {
  const rgb = parseHex(hex)
  if (!rgb) return null
  const { r, g, b } = rgb
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
  return { h: Math.round(hue), s: Math.round(sat * 100), l: Math.round(l * 100) }
}

// WCAG relative luminance (sRGB-linearized). HSL lightness is a poor proxy for perceived
// brightness — e.g. pure yellow/cyan have lightness 0.5 yet read as "light", so picking the
// text color from HSL lightness leaves white text on a light button (unreadable). Relative
// luminance gets this right.
function relativeLuminance(hex) {
  const rgb = parseHex(hex)
  if (!rgb) return null
  const lin = (c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)
  return 0.2126 * lin(rgb.r) + 0.7152 * lin(rgb.g) + 0.0722 * lin(rgb.b)
}

// Readable text on a brand color: 0.179 is the WCAG crossover that maximizes contrast
// against black vs white.
function contentChannels(hex) {
  const lum = relativeLuminance(hex)
  return lum != null && lum > 0.179 ? '0 0% 13%' : '0 0% 100%'
}

// DaisyUI variable name per theme key + its "content" (text-on-color) companion.
const VARS = {
  primary: ['--p', '--pc'],
  secondary: ['--s', '--sc'],
  accent: ['--a', '--ac'],
}

export function applyOrgTheme(theme) {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  // For each slot: apply the org color if valid, otherwise REMOVE any prior override so the
  // base theme shows through. Removing on the empty case is what prevents one org's colors
  // from bleeding into the next.
  for (const [key, [base, content]] of Object.entries(VARS)) {
    const hsl = theme && hexToHsl(theme[key])
    if (hsl) {
      root.style.setProperty(base, `${hsl.h} ${hsl.s}% ${hsl.l}%`)
      root.style.setProperty(content, contentChannels(theme[key]))
    } else {
      root.style.removeProperty(base)
      root.style.removeProperty(content)
    }
  }
}

export function clearOrgTheme() {
  if (typeof document === 'undefined') return
  // Unconditional + idempotent: always restore the base theme. (A guarded clear can get
  // out of sync across the several screens that apply/clear, leaving colors stuck globally.)
  const root = document.documentElement
  for (const [, [base, content]] of Object.entries(VARS)) {
    root.style.removeProperty(base)
    root.style.removeProperty(content)
  }
}

export function hasOrgColors(theme) {
  return !!(theme && (theme.primary || theme.secondary || theme.accent))
}
