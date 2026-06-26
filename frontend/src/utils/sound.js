// Tiny Web Audio earn chime. No assets — synthesized on the fly so it adds no
// bundle weight and works offline. Gated by Settings → effects at the call site.

let ctx = null

function audioCtx() {
  if (typeof window === 'undefined') return null
  const Ctor = window.AudioContext || window.webkitAudioContext
  if (!Ctor) return null
  if (!ctx) ctx = new Ctor()
  return ctx
}

// Schedule a single pure tone with a short attack/decay envelope.
function tone(ac, freq, start, duration, gain = 0.18) {
  const osc = ac.createOscillator()
  const env = ac.createGain()
  osc.type = 'sine'
  osc.frequency.value = freq
  env.gain.setValueAtTime(0, start)
  env.gain.linearRampToValueAtTime(gain, start + 0.015)
  env.gain.exponentialRampToValueAtTime(0.0001, start + duration)
  osc.connect(env).connect(ac.destination)
  osc.start(start)
  osc.stop(start + duration)
}

/**
 * Play a celebratory chime when a badge is earned.
 * @param {boolean} completed - true when the scan completed a whole event (richer flourish).
 */
export function playEarnChime(completed = false) {
  const ac = audioCtx()
  if (!ac) return
  // Browsers start the context suspended until a user gesture; a scan is one.
  if (ac.state === 'suspended') ac.resume().catch(() => {})

  const now = ac.currentTime
  // Major arpeggio; completing an event adds a higher final note.
  const notes = completed
    ? [523.25, 659.25, 783.99, 1046.5] // C5 E5 G5 C6
    : [523.25, 659.25, 783.99] // C5 E5 G5
  notes.forEach((freq, i) => tone(ac, freq, now + i * 0.12, 0.35))
}
