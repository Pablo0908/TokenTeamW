<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import QrScanner from 'qr-scanner'
import { useBadgesStore } from '@/stores/badges'
import { isMock } from '@/services/api'
import Confetti from '@/components/domain/Confetti.vue'

const router = useRouter()
const badges = useBadgesStore()

// qr-scanner is the decode engine: BarcodeDetector isn't available on iOS Safari,
// so we use this library for reliable cross-browser scanning (TDD §QR Scanning).
const video = ref(null)
const state = ref('scanning') // scanning | working | result
const camError = ref('')
const flash = ref('')
const result = ref(null)
const secure = typeof window !== 'undefined' ? window.isSecureContext : true

let scanner = null
let locked = false
let flashTimer = null

const celebrating = computed(() => ['success', 'completed'].includes(result.value?.kind))

function parseRedeem(text) {
  const m = String(text).match(/\/(?:redeem|scan)\/([^/?#]+)\/([^/?#]+)/)
  return m ? { eventId: m[1], token: decodeURIComponent(m[2]) } : null
}

async function startScanner() {
  camError.value = ''
  // Tear down any prior instance so repeated scan→result→scan cycles don't leak
  // workers/listeners or race on the camera stream.
  if (scanner) {
    scanner.destroy()
    scanner = null
  }

  // Over plain http (non-localhost) the browser exposes no camera API at all and
  // will never prompt — retrying can't help, so say so up front.
  if (!secure) {
    camError.value =
      'Your phone’s browser blocks the camera on insecure (http://) pages, so it can’t ask for permission. Open the app over HTTPS (or on the computer at localhost) to scan QR codes.'
    return
  }

  try {
    // Explicitly request the camera first: on a fresh/dismissed state this is what
    // pops the permission prompt; if it was hard-blocked it rejects without prompting.
    const probe = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
    probe.getTracks().forEach((t) => t.stop()) // release it; QrScanner re-acquires below

    scanner = new QrScanner(video.value, (res) => handleDecode(res.data), {
      preferredCamera: 'environment',
      highlightScanRegion: true,
      highlightCodeOutline: true,
      maxScansPerSecond: 5,
    })
    await scanner.start()
  } catch (e) {
    const name = e?.name || ''
    const msg = String(e?.message || e || '')
    if (name === 'NotAllowedError' || /denied|permission|dismiss/i.test(msg)) {
      // The browser won't re-prompt after a block — guide the user to re-enable it.
      camError.value =
        'Camera permission is blocked. Tap the camera (or 🔒) icon in your browser’s address bar, set Camera to “Allow”, then press “Try camera again”.'
    } else if (name === 'NotFoundError' || /not found|no camera/i.test(msg)) {
      camError.value = 'No camera was found on this device.'
    } else if (name === 'NotReadableError' || /in use|readable|busy/i.test(msg)) {
      camError.value = 'Another app is using the camera. Close it, then press “Try camera again”.'
    } else {
      camError.value = 'Couldn’t start the camera. Press “Try camera again”.'
    }
  }
}

function handleDecode(text) {
  if (locked) return
  const parsed = parseRedeem(text)
  if (!parsed) {
    flash.value = 'This QR code is not a Lyfter badge. Try again.'
    clearTimeout(flashTimer)
    flashTimer = setTimeout(() => (flash.value = ''), 2500)
    return
  }
  locked = true
  scanner?.stop()
  redeemAndShow(parsed.eventId, parsed.token)
}

const OUTCOMES = {
  409: { kind: 'duplicate', title: 'Already collected', message: 'You already have this badge.' },
  403: { kind: 'error', title: 'Not available', message: 'This badge isn’t available right now.' },
  410: { kind: 'error', title: 'No longer available', message: 'This badge has reached its limit.' },
  401: { kind: 'error', title: 'Session expired', message: 'Please sign in again to continue.' },
}

async function redeemAndShow(eventId, token) {
  state.value = 'working'
  const res = await badges.redeem(eventId, token)
  if (res.ok) {
    const completed = res.data.event_completed
    result.value = {
      kind: completed ? 'completed' : 'success',
      title: completed ? 'Event completed!' : 'Badge earned!',
      badge: res.data.badge,
      event: res.data.event,
      prize: res.data.prize,
    }
  } else {
    result.value = OUTCOMES[res.status] || {
      kind: 'error',
      title: 'Scan failed',
      message: res.error || 'Something went wrong. Please try again.',
    }
  }
  state.value = 'result'
}

function scanAgain() {
  result.value = null
  locked = false
  state.value = 'scanning'
  startScanner()
}

// Demo: exercise the full earn flow without a printed QR.
const demoTargets = [
  ['ev_cit', 'cit-streak'],
  ['ev_cit', 'cit-top10'],
  ['ev_cit', 'cit-closing'],
  ['ev_techfair', 'tf-welcome'],
  ['ev_techfair', 'tf-sponsor'],
  ['ev_techfair', 'tf-workshop'],
]
let demoIdx = 0
function simulate() {
  const [e, t] = demoTargets[demoIdx % demoTargets.length]
  demoIdx += 1
  locked = true
  scanner?.stop()
  redeemAndShow(e, t)
}

onMounted(startScanner)
onBeforeUnmount(() => {
  clearTimeout(flashTimer)
  scanner?.destroy()
  scanner = null
})
</script>

<template>
  <div class="min-h-dvh px-4 pb-4 pt-6">
    <header class="mb-4">
      <h1 class="text-2xl font-bold">Scan badges</h1>
    </header>

    <Confetti :active="celebrating" />

    <!-- Scanning -->
    <div v-if="state !== 'result'" class="space-y-5">
      <div class="surface relative aspect-square w-full overflow-hidden p-0">
        <video ref="video" class="h-full w-full object-cover" playsinline muted />

        <!-- viewfinder frame -->
        <div class="pointer-events-none absolute inset-0 grid place-items-center">
          <div class="relative h-3/5 w-3/5">
            <span class="absolute left-0 top-0 h-7 w-7 rounded-tl-lg border-l-2 border-t-2 border-primary" />
            <span class="absolute right-0 top-0 h-7 w-7 rounded-tr-lg border-r-2 border-t-2 border-primary" />
            <span class="absolute bottom-0 left-0 h-7 w-7 rounded-bl-lg border-b-2 border-l-2 border-primary" />
            <span class="absolute bottom-0 right-0 h-7 w-7 rounded-br-lg border-b-2 border-r-2 border-primary" />
            <span v-if="!camError" class="scanline absolute inset-x-2 top-0 h-0.5 rounded bg-primary/80" />
          </div>
        </div>

        <div v-if="state === 'working'" class="absolute inset-0 grid place-items-center bg-base-300/70 backdrop-blur-sm">
          <span class="loading loading-spinner loading-lg text-primary" />
        </div>

        <div
          v-if="flash"
          class="absolute inset-x-3 bottom-3 rounded-xl bg-error/90 px-3 py-2 text-center text-sm text-error-content"
        >
          {{ flash }}
        </div>
      </div>

      <div class="text-center">
        <h2 class="text-lg font-semibold">Scan to earn</h2>
        <p class="text-sm text-base-content/60">Point at any QR at an event station</p>
      </div>

      <div v-if="camError" class="space-y-3">
        <div role="alert" class="alert alert-warning text-sm">{{ camError }}</div>
        <button type="button" class="btn btn-outline btn-sm w-full tap-target" @click="startScanner">Try camera again</button>
      </div>

      <button
        v-if="isMock"
        type="button"
        class="btn btn-secondary btn-outline w-full tap-target"
        @click="simulate"
      >
        Simulate a scan (demo)
      </button>
    </div>

    <!-- Result -->
    <div v-else class="flex flex-col items-center gap-5 py-6 text-center">
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
        <h2 class="text-2xl font-bold">{{ result.title }}</h2>
        <p v-if="result.badge" class="mt-1 text-base-content/70">
          {{ result.badge.name }} · {{ result.event }}
        </p>
        <p v-else class="mt-1 text-base-content/70">{{ result.message }}</p>
      </div>

      <div
        v-if="result.kind === 'completed' && result.prize"
        class="surface w-full bg-gradient-to-r from-warning/20 to-secondary/15 p-4"
      >
        <p class="text-xs uppercase tracking-wide text-base-content/55">Prize unlocked</p>
        <p class="mt-1 font-semibold text-warning">🎁 {{ result.prize }}</p>
      </div>

      <div class="mt-2 w-full space-y-2">
        <button class="btn btn-primary w-full tap-target" @click="router.push('/badges')">View my collection</button>
        <button class="btn btn-ghost w-full tap-target" @click="scanAgain">Scan another</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.scanline {
  animation: scan 2.2s ease-in-out infinite;
  box-shadow: 0 0 12px 1px rgba(45, 212, 191, 0.7);
}
@keyframes scan {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(150%);
  }
}
@media (prefers-reduced-motion: reduce) {
  .scanline {
    animation: none;
  }
}
</style>
