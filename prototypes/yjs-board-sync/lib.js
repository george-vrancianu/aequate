// PROTOTYPE (throwaway): shared helpers. Seeded RNG, synthetic strokes, packing, layouts.
import * as Y from 'yjs'

export function mulberry32(seed) {
  let a = seed >>> 0
  return () => {
    a = (a + 0x6d2b79f5) >>> 0
    let t = a
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

// ---- stroke = {x: number[], y: number[], p: number[]}; packed = Uint8Array ----
export function genStroke(rng) {
  const n = 50 + Math.floor(rng() * 251) // 50..300 points
  let x = rng() * 2000, y = rng() * 3000, ang = rng() * 6.283, speed = 1 + rng() * 4
  const xs = [], ys = [], ps = []
  let pr = 0.2 + rng() * 0.5
  for (let i = 0; i < n; i++) {
    ang += (rng() - 0.5) * 0.6
    speed = Math.max(0.3, Math.min(8, speed + (rng() - 0.5) * 0.8))
    x += Math.cos(ang) * speed
    y += Math.sin(ang) * speed
    pr = Math.max(0.05, Math.min(1, pr + (rng() - 0.5) * 0.1))
    xs.push(Math.round(x * 10) / 10); ys.push(Math.round(y * 10) / 10); ps.push(Math.round(pr * 255))
  }
  return { x: xs, y: ys, p: ps }
}

const zz = (v) => (v << 1) ^ (v >> 31)
const unzz = (v) => (v >>> 1) ^ -(v & 1)
// format: varint n, then per point: zigzag-varint dx, dy (0.1 px units, delta vs previous, first vs 0), dp (delta pressure 0..255)
export function pack(s) {
  const n = s.x.length
  const buf = new Uint8Array(5 + n * 8)
  let o = 0
  const w = (v) => { while (v > 127) { buf[o++] = (v & 127) | 128; v >>>= 7 } buf[o++] = v }
  w(n)
  let px = 0, py = 0, pp = 0
  for (let i = 0; i < n; i++) {
    const x = Math.round(s.x[i] * 10), y = Math.round(s.y[i] * 10)
    w(zz(x - px)); w(zz(y - py)); w(zz(s.p[i] - pp))
    px = x; py = y; pp = s.p[i]
  }
  return buf.slice(0, o)
}
export function unpack(buf) {
  let o = 0
  const r = () => { let v = 0, sh = 0, b; do { b = buf[o++]; v |= (b & 127) << sh; sh += 7 } while (b & 128); return v >>> 0 }
  const n = r()
  const x = new Array(n), y = new Array(n), p = new Array(n)
  let px = 0, py = 0, pp = 0
  for (let i = 0; i < n; i++) {
    px += unzz(r()); py += unzz(r()); pp += unzz(r())
    x[i] = px / 10; y[i] = py / 10; p[i] = pp
  }
  return { x, y, p }
}

export function genStrokes(N, seed = 42) {
  const rng = mulberry32(seed)
  const out = []
  for (let i = 0; i < N; i++) {
    const id = (Math.floor(rng() * 36 ** 6)).toString(36).padStart(6, '0') + i.toString(36).padStart(4, '0')
    out.push({ id, packed: pack(genStroke(rng)) })
  }
  return out
}

export const pageOf = (i, N, P) => Math.floor((i * P) / N)
export const median = (a) => { const s = [...a].sort((x, y) => x - y); const m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2 }
export const pct = (a, q) => { const s = [...a].sort((x, y) => x - y); return s[Math.min(s.length - 1, Math.floor(q * s.length))] }

// ---- layouts. Strokes are one Y.Map entry per stroke: id -> packed Uint8Array, one transaction per stroke ----
// A: one doc, one root Y.Map per page.  B: root doc with Y.Map pageId -> subdoc (Y.Doc with root map 'strokes').  C: one doc per page.
export function newDoc(clientID, guid) {
  const d = new Y.Doc(guid ? { guid } : undefined)
  d.clientID = clientID
  return d
}

export function buildBoard(layout, strokes, P, updateSizes) {
  const N = strokes.length
  const track = (d) => d.on('update', (u) => updateSizes.push(u.length))
  if (layout === 'A') {
    const doc = newDoc(1001); track(doc)
    const maps = Array.from({ length: P }, (_, p) => doc.getMap('strokes:' + p))
    strokes.forEach((s, i) => doc.transact(() => maps[pageOf(i, N, P)].set(s.id, s.packed)))
    return { docs: [doc], root: doc }
  }
  if (layout === 'B') {
    const root = newDoc(1001)
    const pages = root.getMap('pages')
    const subs = []
    for (let p = 0; p < P; p++) { const sd = newDoc(2000 + p, 'page-' + p); pages.set('page-' + p, sd); subs.push(sd); track(sd) }
    const maps = subs.map((sd) => sd.getMap('strokes'))
    strokes.forEach((s, i) => { const p = pageOf(i, N, P); subs[p].transact(() => maps[p].set(s.id, s.packed)) })
    return { root, docs: subs }
  }
  // C
  const docs = Array.from({ length: P }, (_, p) => { const d = newDoc(3000 + p, 'page-' + p); track(d); return d })
  const maps = docs.map((d) => d.getMap('strokes'))
  strokes.forEach((s, i) => { const p = pageOf(i, N, P); docs[p].transact(() => maps[p].set(s.id, s.packed)) })
  return { docs }
}

// read (decode) every stroke of a map, return total points so work is not optimised away
export function readMap(map) {
  let pts = 0
  map.forEach((v) => { pts += unpack(v).x.length })
  return pts
}
