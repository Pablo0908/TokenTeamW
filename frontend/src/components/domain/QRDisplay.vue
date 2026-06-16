<script setup>
import { ref, watch, onMounted } from 'vue'
import QRCode from 'qrcode'

const props = defineProps({
  value: { type: String, default: '' }, // the redeem URL the QR encodes
  image: { type: String, default: '' }, // optional QR image URL/data-URL from the backend
  label: { type: String, default: '' },
  size: { type: Number, default: 220 },
  filename: { type: String, default: 'badge-qr.png' },
})

const qrSrc = ref('')
const failed = ref(false)
const copied = ref(false)

const isImageUrl = (s) => /^data:image\//.test(s) || /^https?:\/\/.+\.(png|jpe?g|svg|gif|webp)/i.test(s)

// Prefer a backend-rendered QR image; otherwise generate a real, scannable QR locally
// (no third-party service — keeps the redemption token off external servers and works offline).
async function generate() {
  failed.value = false
  if (props.image && isImageUrl(props.image)) {
    qrSrc.value = props.image
    return
  }
  const text = props.value || props.image || ''
  if (!text) {
    qrSrc.value = ''
    return
  }
  try {
    qrSrc.value = await QRCode.toDataURL(text, {
      width: props.size,
      margin: 1,
      errorCorrectionLevel: 'M',
      color: { dark: '#0b0d14', light: '#ffffff' },
    })
  } catch {
    failed.value = true
  }
}

async function download() {
  if (!qrSrc.value) return
  if (qrSrc.value.startsWith('data:')) {
    const a = document.createElement('a')
    a.href = qrSrc.value
    a.download = props.filename
    a.click()
    return
  }
  try {
    const res = await fetch(qrSrc.value, { mode: 'cors' })
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = props.filename
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    window.open(qrSrc.value, '_blank', 'noopener')
  }
}

async function copyLink() {
  try {
    await navigator.clipboard.writeText(props.value)
    copied.value = true
    setTimeout(() => (copied.value = false), 1500)
  } catch {
    /* clipboard unavailable */
  }
}

onMounted(generate)
watch(() => [props.value, props.image], generate)
</script>

<template>
  <div class="flex flex-col items-center gap-3">
    <div class="rounded-2xl bg-white p-3 shadow-lg">
      <img
        v-if="qrSrc"
        :src="qrSrc"
        :width="size"
        :height="size"
        :alt="(label ? label + ' — ' : '') + 'Badge QR code'"
        class="block h-auto w-full max-w-[220px] rounded-lg"
        @error="failed = true"
      />
      <div v-else class="grid h-[220px] w-[220px] place-items-center text-sm text-base-300">…</div>
    </div>
    <p v-if="failed" class="text-center text-xs text-warning">
      Couldn’t render the QR — share this link instead.
    </p>
    <p v-if="value" class="max-w-full truncate text-center text-xs text-base-content/50">{{ value }}</p>

    <div class="flex w-full gap-2">
      <button type="button" class="btn btn-primary btn-sm flex-1 tap-target" @click="download">
        Download QR
      </button>
      <button type="button" class="btn btn-outline btn-sm flex-1 tap-target" @click="copyLink">
        {{ copied ? 'Copied!' : 'Copy link' }}
      </button>
    </div>
  </div>
</template>
