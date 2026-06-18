<script setup>
import { ref, computed } from 'vue'

// Share a public badge link. The link renders a branded preview card (OG image)
// on every platform. Web-intent platforms open a share dialog; Discord/Instagram
// have no web intent, so we copy the link (pasting it auto-embeds the card).
const props = defineProps({
  url: { type: String, required: true },
  text: { type: String, default: '' },
  title: { type: String, default: 'Lyfter badge' },
})

const copied = ref(false)
const copyNote = ref('')
const canNativeShare = typeof navigator !== 'undefined' && !!navigator.share
const enc = encodeURIComponent

const ICON = {
  whatsapp: 'M17.5 14.4c-.3-.15-1.76-.87-2.03-.97-.27-.1-.47-.15-.67.15s-.77.96-.94 1.16-.35.22-.64.07-1.26-.46-2.4-1.48c-.88-.79-1.48-1.76-1.65-2.06s-.02-.46.13-.6c.13-.14.3-.35.44-.52s.2-.3.3-.5.05-.37-.02-.52-.67-1.61-.92-2.21c-.24-.58-.49-.5-.67-.51h-.57c-.2 0-.52.07-.79.37s-1.04 1.02-1.04 2.48 1.07 2.88 1.21 3.07 2.1 3.2 5.08 4.49c.71.3 1.26.49 1.69.62.71.23 1.36.2 1.87.12.57-.08 1.76-.72 2-1.41s.25-1.29.18-1.41-.27-.2-.57-.35M12.05 21.8a9.9 9.9 0 01-5.03-1.38l-.36-.21-3.74.98 1-3.65-.24-.37a9.86 9.86 0 01-1.51-5.26C2.17 6.46 6.6 2.03 12.05 2.03c2.64 0 5.12 1.03 6.99 2.9a9.83 9.83 0 012.89 6.99c0 5.45-4.44 9.88-9.88 9.88M20.46 3.49A11.82 11.82 0 0012.05.0C5.5.0.16 5.34.16 11.89c0 2.1.55 4.14 1.59 5.95L.06 24l6.3-1.65a11.88 11.88 0 005.69 1.45c6.55 0 11.89-5.34 11.89-11.89a11.82 11.82 0 00-3.48-8.42',
  facebook: 'M24 12.07C24 5.44 18.63.07 12 .07S0 5.44 0 12.07c0 5.99 4.39 10.95 10.13 11.85v-8.38H7.08v-3.47h3.05V9.43c0-3.01 1.79-4.67 4.53-4.67 1.31 0 2.69.24 2.69.24v2.95h-1.51c-1.49 0-1.96.93-1.96 1.87v2.25h3.33l-.53 3.47h-2.8v8.38C19.61 23.02 24 18.06 24 12.07',
  x: 'M18.24 2.25h3.31l-7.23 8.26L23.07 21.75H16.17l-5.21-6.82L4.99 21.75H1.68l7.73-8.84L.92 2.25H8.08l4.71 6.23zm-1.16 17.52h1.83L7.08 4.13H5.12z',
  linkedin: 'M20.45 20.45h-3.55v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46zM5.34 7.43a2.06 2.06 0 110-4.13 2.06 2.06 0 010 4.13M7.12 20.45H3.56V9h3.56zM22.22 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.22 0',
  telegram: 'M11.94 0A12 12 0 000 12a12 12 0 0012 12 12 12 0 0012-12A12 12 0 0011.94 0m4.96 7.22c.1 0 .32.02.46.14a.5.5 0 01.17.33c.02.09.04.3.02.47-.18 1.9-.96 6.5-1.36 8.63-.17.9-.5 1.2-.82 1.23-.7.06-1.23-.46-1.9-.9-1.06-.7-1.65-1.12-2.68-1.8-1.19-.78-.42-1.21.26-1.91.18-.18 3.25-2.98 3.3-3.23a.24.24 0 00-.05-.21c-.07-.06-.17-.04-.25-.02-.1.02-1.79 1.14-5.06 3.34-.48.33-.91.5-1.3.48-.43 0-1.25-.24-1.86-.44-.75-.25-1.35-.37-1.3-.79.03-.21.33-.43.9-.66 3.5-1.52 5.83-2.53 7-3.01 3.33-1.39 4.02-1.63 4.47-1.64',
  discord: 'M20.32 4.37a19.79 19.79 0 00-4.89-1.52.07.07 0 00-.07.04c-.21.37-.45.86-.61 1.25a18.27 18.27 0 00-5.49 0 12.6 12.6 0 00-.62-1.25.08.08 0 00-.08-.04 19.74 19.74 0 00-4.88 1.52.07.07 0 00-.04.03C.53 9.05-.32 13.58.1 18.06a.08.08 0 00.03.06 19.9 19.9 0 005.99 3.03.08.08 0 00.09-.03c.46-.63.87-1.3 1.23-1.99a.08.08 0 00-.04-.11 13.1 13.1 0 01-1.87-.89.08.08 0 01-.01-.13l.37-.29a.07.07 0 01.08-.01 14.2 14.2 0 0012.06 0 .07.07 0 01.08.01l.37.29a.08.08 0 01-.01.13c-.6.35-1.21.65-1.87.89a.08.08 0 00-.04.11c.36.69.78 1.36 1.23 1.99a.08.08 0 00.08.03 19.84 19.84 0 006-3.03.08.08 0 00.03-.06c.5-5.18-.84-9.67-3.55-13.66a.06.06 0 00-.03-.03M8.02 15.33c-1.18 0-2.16-1.08-2.16-2.42s.96-2.42 2.16-2.42c1.21 0 2.18 1.1 2.16 2.42 0 1.34-.96 2.42-2.16 2.42m7.97 0c-1.18 0-2.16-1.08-2.16-2.42s.96-2.42 2.16-2.42c1.21 0 2.18 1.1 2.16 2.42 0 1.34-.95 2.42-2.16 2.42',
  instagram: 'M12 2.16c3.2 0 3.58.02 4.85.07 1.17.06 1.8.25 2.23.42.56.21.96.47 1.38.9.42.41.68.81.9 1.38.16.42.36 1.05.41 2.23.06 1.27.07 1.65.07 4.85s-.01 3.58-.07 4.85c-.06 1.17-.26 1.8-.42 2.23-.22.56-.48.96-.9 1.38-.42.42-.82.68-1.38.9-.42.16-1.06.36-2.23.41-1.27.06-1.65.07-4.85.07s-3.59-.01-4.86-.07c-1.17-.06-1.81-.26-2.24-.42-.57-.22-.96-.48-1.38-.9-.42-.42-.69-.82-.9-1.38-.16-.42-.36-1.06-.42-2.23C2.18 15.58 2.16 15.2 2.16 12s.02-3.59.07-4.86c.06-1.17.26-1.81.42-2.23.21-.57.48-.96.9-1.38.42-.42.81-.69 1.38-.9.42-.16 1.05-.36 2.22-.42C8.42 2.18 8.8 2.16 12 2.16M12 0C8.74 0 8.33.01 7.05.07c-1.28.06-2.15.26-2.91.56-.79.3-1.46.71-2.13 1.38S.94 3.35.63 4.14c-.3.76-.5 1.63-.56 2.91C.01 8.33 0 8.74 0 12s.01 3.67.07 4.95c.06 1.28.26 2.15.56 2.91.3.79.71 1.46 1.38 2.13s1.34 1.08 2.13 1.38c.76.3 1.63.5 2.91.56C8.33 23.99 8.74 24 12 24s3.67-.01 4.95-.07c1.28-.06 2.15-.26 2.91-.56a5.88 5.88 0 002.13-1.38 5.88 5.88 0 001.38-2.13c.3-.76.5-1.63.56-2.91.06-1.28.07-1.69.07-4.95s-.01-3.67-.07-4.95c-.06-1.28-.26-2.15-.56-2.91a5.88 5.88 0 00-1.38-2.13A5.88 5.88 0 0019.86.63c-.76-.3-1.63-.5-2.91-.56C15.67.01 15.26 0 12 0m0 5.84A6.16 6.16 0 1018.16 12 6.16 6.16 0 0012 5.84M12 16a4 4 0 110-8 4 4 0 010 8m6.41-10.41a1.44 1.44 0 11-1.44-1.44 1.44 1.44 0 011.44 1.44',
  link: 'M3.9 12a3.1 3.1 0 013.1-3.1h4V7H7a5 5 0 100 10h4v-1.9H7A3.1 3.1 0 013.9 12M8 13h8v-2H8zm9-6h-4v1.9h4a3.1 3.1 0 010 6.2h-4V17h4a5 5 0 000-10',
}

const webTargets = computed(() => {
  const u = enc(props.url)
  const t = enc(props.text || props.title)
  const tu = enc((props.text ? props.text + ' ' : '') + props.url)
  return [
    { key: 'whatsapp', label: 'WhatsApp', bg: '#25D366', href: `https://wa.me/?text=${tu}` },
    { key: 'facebook', label: 'Facebook', bg: '#1877F2', href: `https://www.facebook.com/sharer/sharer.php?u=${u}` },
    { key: 'x', label: 'X', bg: '#18181b', href: `https://twitter.com/intent/tweet?text=${t}&url=${u}` },
    { key: 'linkedin', label: 'LinkedIn', bg: '#0A66C2', href: `https://www.linkedin.com/sharing/share-offsite/?url=${u}` },
    { key: 'telegram', label: 'Telegram', bg: '#229ED9', href: `https://t.me/share/url?url=${u}&text=${t}` },
  ]
})
const copyTargets = [
  { key: 'discord', label: 'Discord', bg: '#5865F2' },
  { key: 'instagram', label: 'Instagram', bg: '#E1306C' },
]

function openTarget(href) {
  window.open(href, '_blank', 'noopener,noreferrer,width=620,height=650')
}
async function copyLink(note) {
  try {
    await navigator.clipboard.writeText(props.url)
    copied.value = true
    copyNote.value = note || 'Link copied!'
    setTimeout(() => {
      copied.value = false
      copyNote.value = ''
    }, 2200)
  } catch {
    /* clipboard unavailable */
  }
}
async function nativeShare() {
  try {
    await navigator.share({ title: props.title, text: props.text, url: props.url })
  } catch {
    /* cancelled / unsupported */
  }
}
</script>

<template>
  <div class="space-y-3">
    <p class="text-left text-xs font-medium uppercase tracking-wide text-base-content/45">Share this badge</p>

    <div class="grid grid-cols-4 gap-3">
      <button
        v-for="t in webTargets"
        :key="t.key"
        type="button"
        class="flex flex-col items-center gap-1.5 tap-target"
        @click="openTarget(t.href)"
      >
        <span class="grid h-12 w-12 place-items-center rounded-full text-white shadow-lg" :style="{ backgroundColor: t.bg }">
          <svg class="h-6 w-6" viewBox="0 0 24 24" fill="currentColor"><path :d="ICON[t.key]" /></svg>
        </span>
        <span class="text-[0.65rem] text-base-content/60">{{ t.label }}</span>
      </button>

      <button
        v-for="t in copyTargets"
        :key="t.key"
        type="button"
        class="flex flex-col items-center gap-1.5 tap-target"
        :title="`Copy the link, then paste it in ${t.label}`"
        @click="copyLink(`Link copied — paste it in ${t.label}`)"
      >
        <span class="grid h-12 w-12 place-items-center rounded-full text-white shadow-lg" :style="{ backgroundColor: t.bg }">
          <svg class="h-6 w-6" viewBox="0 0 24 24" fill="currentColor"><path :d="ICON[t.key]" /></svg>
        </span>
        <span class="text-[0.65rem] text-base-content/60">{{ t.label }}</span>
      </button>

      <button
        v-if="canNativeShare"
        type="button"
        class="flex flex-col items-center gap-1.5 tap-target"
        @click="nativeShare"
      >
        <span class="grid h-12 w-12 place-items-center rounded-full bg-base-300 text-base-content shadow-lg">
          <svg class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" />
            <path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4" />
          </svg>
        </span>
        <span class="text-[0.65rem] text-base-content/60">More</span>
      </button>
    </div>

    <button type="button" class="btn btn-outline btn-sm w-full gap-2 tap-target" @click="copyLink()">
      <svg class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><path :d="ICON.link" /></svg>
      {{ copied ? (copyNote || 'Copied!') : 'Copy link' }}
    </button>
  </div>
</template>
