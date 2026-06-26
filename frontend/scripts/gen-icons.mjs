// Generates PWA PNG icons (192, 512, 512-maskable) with no external dependency.
// Draws a teal "medal" badge on a dark background using a hand-rolled PNG encoder.
import { deflateSync } from 'node:zlib'
import { writeFileSync, mkdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const here = dirname(fileURLToPath(import.meta.url))
const outDir = join(here, '..', 'public', 'icons')

const CRC_TABLE = (() => {
  const t = new Uint32Array(256)
  for (let n = 0; n < 256; n++) {
    let c = n
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1
    t[n] = c >>> 0
  }
  return t
})()

function crc32(buf) {
  let crc = 0xffffffff
  for (let i = 0; i < buf.length; i++) crc = CRC_TABLE[(crc ^ buf[i]) & 0xff] ^ (crc >>> 8)
  return (crc ^ 0xffffffff) >>> 0
}

function chunk(type, data) {
  const len = Buffer.alloc(4)
  len.writeUInt32BE(data.length, 0)
  const body = Buffer.concat([Buffer.from(type, 'latin1'), data])
  const crc = Buffer.alloc(4)
  crc.writeUInt32BE(crc32(body), 0)
  return Buffer.concat([len, body, crc])
}

function encodePNG(size, rgba) {
  const sig = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])
  const ihdr = Buffer.alloc(13)
  ihdr.writeUInt32BE(size, 0)
  ihdr.writeUInt32BE(size, 4)
  ihdr[8] = 8 // bit depth
  ihdr[9] = 6 // RGBA
  const stride = size * 4
  const raw = Buffer.alloc((stride + 1) * size)
  for (let y = 0; y < size; y++) {
    raw[y * (stride + 1)] = 0 // filter: none
    rgba.copy(raw, y * (stride + 1) + 1, y * stride, y * stride + stride)
  }
  const idat = deflateSync(raw, { level: 9 })
  return Buffer.concat([sig, chunk('IHDR', ihdr), chunk('IDAT', idat), chunk('IEND', Buffer.alloc(0))])
}

const hex = (h) => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)]
const lerp = (a, b, t) => a + (b - a) * t
const mix = (c1, c2, t) => [lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t)]

function makeIcon(size, maskable = false) {
  const buf = Buffer.alloc(size * size * 4)
  const cx = size / 2
  const cy = maskable ? size / 2 : size * 0.46
  const bg = hex('#0b0d14')
  const teal1 = hex('#2dd4bf')
  const teal2 = hex('#0e7490')
  const white = [233, 240, 247]
  const R = size * (maskable ? 0.3 : 0.36)
  const ring = R * 0.66
  const ringW = Math.max(2, size * 0.05)
  const dot = R * 0.26
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const i = (y * size + x) * 4
      let col = maskable ? mix(teal2, teal1, (x + y) / (2 * size)) : bg.slice()
      const dx = x - cx
      const dy = y - cy
      const d = Math.sqrt(dx * dx + dy * dy)
      if (d <= R) {
        col = mix(teal1, teal2, y / size)
        if (d <= ring && d > ring - ringW) col = white.slice()
        if (d <= dot) col = white.slice()
      }
      buf[i] = Math.round(col[0])
      buf[i + 1] = Math.round(col[1])
      buf[i + 2] = Math.round(col[2])
      buf[i + 3] = 255
    }
  }
  return encodePNG(size, buf)
}

mkdirSync(outDir, { recursive: true })
writeFileSync(join(outDir, 'icon-192.png'), makeIcon(192))
writeFileSync(join(outDir, 'icon-512.png'), makeIcon(512))
writeFileSync(join(outDir, 'icon-512-maskable.png'), makeIcon(512, true))
console.log('PWA icons generated in', outDir)
