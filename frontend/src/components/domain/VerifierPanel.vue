<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import QrScanner from 'qr-scanner'
import { t } from '@/i18n'
import { api } from '@/services/api'

// Staff-facing prize verifier. Scans an attendee's claim QR (a signed, opaque token) and
// posts it to POST /claims/verify. The QR carries NO authority — the server re-checks
// completion + not-already-claimed and performs the atomic flip; this view only relays the
// scan and shows the AWARDED / DENIED verdict. It is org-agnostic: the backend derives the
// org from the signed token and authorizes the scanning staff against it.
const video = ref(null)
const state = ref('scanning') // scanning | working | result
const camError = ref('')
const flash = ref('')
const result = ref(null)
const claimantName = ref('')
const secure = typeof window !== 'undefined' ? window.isSecureContext : true

let scanner = null
let locked = false
let flashTimer = null

// A badge redeem/scan URL is NOT a prize claim — reject it clearly instead of posting it.
const isRedeemUrl = (text) => /\/(?:redeem|scan)\/[^/?#]+\/[^/?#]+/.test(String(text))

async function startScanner() {
  camError.value = ''
  if (scanner) { scanner.destroy(); scanner = null }
  if (!secure) { camError.value = t('scan.errInsecure'); return }
  try {
    const probe = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
    probe.getTracks().forEach((tr) => tr.stop())
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
    if (name === 'NotAllowedError' || /denied|permission|dismiss/i.test(msg)) camError.value = t('scan.errDenied')
    else if (name === 'NotFoundError' || /not found|no camera/i.test(msg)) camError.value = t('scan.errNotFound')
    else if (name === 'NotReadableError' || /in use|readable|busy/i.test(msg)) camError.value = t('scan.errBusy')
    else camError.value = t('scan.errGeneric')
  }
}

function handleDecode(text) {
  if (locked) return
  if (isRedeemUrl(text)) {
    flash.value = t('verifier.notClaim')
    clearTimeout(flashTimer)
    flashTimer = setTimeout(() => (flash.value = ''), 2500)
    return
  }
  locked = true
  scanner?.stop()
  verifyClaim(String(text).trim())
}

const REASON_KEY = {
  invalid_token: 'reasonInvalidToken',
  not_completed: 'reasonNotCompleted',
  already_claimed: 'reasonAlreadyClaimed',
  out_of_scope: 'reasonOutOfScope',
  not_found: 'reasonNotFound',
}
function denied(reason, claim) {
  return {
    kind: 'denied',
    message: t(`verifier.${REASON_KEY[reason] || 'reasonGeneric'}`),
    claim: claim || null,
  }
}

async function verifyClaim(token) {
  state.value = 'working'
  const payload = { token, claimant_name: claimantName.value.trim() || undefined }
  try {
    const { data } = await api.post('/claims/verify', payload)
    result.value = data.result === 'awarded'
      ? { kind: 'awarded', attendee: data.attendee, prize: data.prize, claim: data.claim }
      : denied(data.reason, data.claim)
  } catch (e) {
    const data = e.response?.data || {}
    result.value = denied(data.reason, data.claim)
  }
  state.value = 'result'
}

function scanAgain() {
  result.value = null
  claimantName.value = ''
  locked = false
  state.value = 'scanning'
  startScanner()
}

onMounted(startScanner)
onBeforeUnmount(() => {
  clearTimeout(flashTimer)
  scanner?.destroy()
  scanner = null
})
</script>

<template>
  <div class="space-y-4">
    <div class="text-center">
      <h2 class="text-lg font-semibold">{{ $t('verifier.title') }}</h2>
      <p class="text-sm text-base-content/60">{{ $t('verifier.sub') }}</p>
    </div>

    <!-- Scanning -->
    <div v-if="state !== 'result'" class="space-y-4">
      <label class="form-control w-full">
        <span class="label-text mb-1 text-xs text-base-content/60">{{ $t('verifier.claimantLabel') }}</span>
        <input v-model="claimantName" :placeholder="$t('verifier.claimantPlaceholder')" class="input input-bordered input-sm w-full bg-base-100/70" />
      </label>

      <div class="surface relative aspect-square w-full overflow-hidden p-0">
        <video ref="video" class="h-full w-full object-cover" playsinline muted />
        <div class="pointer-events-none absolute inset-0 grid place-items-center">
          <div class="relative h-3/5 w-3/5">
            <span class="absolute left-0 top-0 h-7 w-7 rounded-tl-lg border-l-2 border-t-2 border-primary" />
            <span class="absolute right-0 top-0 h-7 w-7 rounded-tr-lg border-r-2 border-t-2 border-primary" />
            <span class="absolute bottom-0 left-0 h-7 w-7 rounded-bl-lg border-b-2 border-l-2 border-primary" />
            <span class="absolute bottom-0 right-0 h-7 w-7 rounded-br-lg border-b-2 border-r-2 border-primary" />
          </div>
        </div>
        <div v-if="state === 'working'" class="absolute inset-0 grid place-items-center bg-base-300/70 backdrop-blur-sm">
          <span class="loading loading-spinner loading-lg text-primary" />
        </div>
        <div v-if="flash" class="absolute inset-x-3 bottom-3 rounded-xl bg-error/90 px-3 py-2 text-center text-sm text-error-content">
          {{ flash }}
        </div>
      </div>

      <div v-if="camError" class="space-y-3">
        <div role="alert" class="alert alert-warning text-sm">{{ camError }}</div>
        <button type="button" class="btn btn-outline btn-sm w-full tap-target" @click="startScanner">{{ $t('scan.tryAgain') }}</button>
      </div>
    </div>

    <!-- Result -->
    <div v-else class="flex flex-col items-center gap-4 py-4 text-center">
      <div
        class="grid h-24 w-24 place-items-center rounded-full text-5xl shadow-2xl"
        :class="result.kind === 'awarded' ? 'bg-gradient-to-br from-success/30 to-primary/20 shadow-success/30' : 'bg-error/15 shadow-error/20'"
      >
        <template v-if="result.kind === 'awarded'">🎁</template>
        <template v-else>⚠️</template>
      </div>
      <div>
        <h3 class="text-xl font-bold">
          {{ result.kind === 'awarded' ? $t('verifier.awardedTitle') : $t('verifier.deniedTitle') }}
        </h3>
        <template v-if="result.kind === 'awarded'">
          <p class="mt-1 text-base-content/70">{{ $t('verifier.awardedTo', { name: result.attendee }) }}</p>
          <p v-if="result.prize" class="mt-1 text-sm font-semibold text-warning">🎁 {{ result.prize }}</p>
        </template>
        <template v-else>
          <p class="mt-1 text-base-content/70">{{ result.message }}</p>
          <p v-if="result.claim" class="mt-1 text-xs text-base-content/55">
            <span v-if="result.claim.awarded_by_name">{{ $t('verifier.awardedBy', { name: result.claim.awarded_by_name }) }}</span>
            <span v-if="result.claim.awarded_on"> {{ $t('verifier.awardedAt', { date: result.claim.awarded_on }) }}</span>
          </p>
        </template>
      </div>
      <button class="btn btn-primary w-full tap-target" @click="scanAgain">{{ $t('verifier.scanAnother') }}</button>
    </div>
  </div>
</template>
