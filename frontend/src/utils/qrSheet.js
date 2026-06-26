import QRCode from 'qrcode'

const escapeHtml = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c])

// Build a printable sheet of QR codes for an event's badges and open it in a new window,
// ready to print or "Save as PDF". QR images are rendered client-side from each badge's
// redeem URL (the list API omits the heavy base64 image), so this works for any badge.
export async function printQrSheet(eventName, badges) {
  if (!badges?.length) return false

  const items = await Promise.all(
    badges.map(async (b) => ({
      name: b.name,
      token: b.token || '',
      qr: await QRCode.toDataURL(b.qr_url, { width: 320, margin: 1, errorCorrectionLevel: 'H' }),
    })),
  )

  const cards = items
    .map(
      (it) => `
      <div class="card">
        <img src="${it.qr}" alt="" />
        <div class="name">${escapeHtml(it.name)}</div>
        <div class="hint">Scan to earn your badge</div>
        ${it.token ? `<div class="token">${escapeHtml(it.token)}</div>` : ''}
      </div>`,
    )
    .join('')

  const html = `<!doctype html><html><head><meta charset="utf-8" />
    <title>${escapeHtml(eventName)} — QR codes</title>
    <style>
      * { box-sizing: border-box; }
      body { font-family: system-ui, -apple-system, sans-serif; margin: 0; padding: 16px; color: #0b0d14; }
      h1 { font-size: 18px; margin: 0 0 14px; }
      .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
      .card { border: 1px solid #dcdfe6; border-radius: 12px; padding: 12px; text-align: center;
              break-inside: avoid; page-break-inside: avoid; }
      .card img { width: 100%; max-width: 210px; height: auto; }
      .name { font-weight: 700; margin-top: 6px; font-size: 14px; }
      .hint { font-size: 11px; color: #6b7280; }
      .token { font-family: ui-monospace, monospace; font-size: 8px; color: #aab; margin-top: 4px; word-break: break-all; }
      @media print { body { padding: 0; } .grid { gap: 8px; } @page { margin: 12mm; } }
    </style></head>
    <body>
      <h1>${escapeHtml(eventName)} — Badge QR codes (${items.length})</h1>
      <div class="grid">${cards}</div>
      <script>window.onload = function () { setTimeout(function () { window.print(); }, 300); };<\/script>
    </body></html>`

  const w = window.open('', '_blank')
  if (!w) return false // popup blocked
  w.document.open()
  w.document.write(html)
  w.document.close()
  w.focus()
  return true
}
