// PROTOTYPE (throwaway): child process; measures one layout/size/pages combination in pure Yjs.
// usage: node --expose-gc measure.js <build|memfull|mempage> <A|B|C> <N> <P>
import * as Y from 'yjs'
import fs from 'node:fs'
import { genStrokes, buildBoard, readMap, median, pct, newDoc } from './lib.js'

const [mode, layout, N, P] = [process.argv[2], process.argv[3], +process.argv[4], +process.argv[5]]
const dir = new URL('./.tmp/', import.meta.url).pathname
fs.mkdirSync(dir, { recursive: true })
const f = (name) => `${dir}${layout}-${N}-${P}-${name}.bin`
const gc = () => { global.gc(); global.gc() }
const T = (fn) => { gc(); const t = performance.now(); const r = fn(); return [performance.now() - t, r] }
const REPS = 7

// Loading one Y.Doc from stored update(s). B: root update then each subdoc's update applied into the subdoc object found in the root map.
function loadFull(files, apply = Y.applyUpdate) {
  if (layout === 'B') {
    const root = new Y.Doc()
    apply(root, files.root)
    const subs = []
    root.getMap('pages').forEach((sd, key) => { apply(sd, files[key]); subs.push(sd) })
    return { root, docs: subs }
  }
  if (layout === 'A') { const d = new Y.Doc(); apply(d, files.page0); return { docs: [d] } }
  const docs = []
  for (let p = 0; p < P; p++) { const d = new Y.Doc(); apply(d, files['page-' + p]); docs.push(d) }
  return { docs }
}
function loadPage0(files, apply = Y.applyUpdate) {
  if (layout === 'B') {
    const root = new Y.Doc(); apply(root, files.root)
    const sd = root.getMap('pages').get('page-0'); apply(sd, files['page-0']); return { root, docs: [sd] }
  }
  if (layout === 'A') { const d = new Y.Doc(); apply(d, files.page0); return { docs: [d] } }
  const d = new Y.Doc(); apply(d, files['page-0']); return { docs: [d] }
}
const readAll = (b) => b.docs.reduce((n, d) => n + (layout === 'A' ? [...d.share.keys()].reduce((m, k) => m + readMap(d.getMap(k)), 0) : readMap(d.getMap('strokes'))), 0)
const readPage0 = (b) => layout === 'A' ? readMap(b.docs[0].getMap('strokes:0')) : readMap(b.docs[0].getMap('strokes'))

// stored files keyed: A -> page0 (the single doc); B -> root + page-i; C -> page-i
function readFiles() {
  const o = {}
  for (const name of fs.readdirSync(dir)) {
    const pre = `${layout}-${N}-${P}-`
    if (name.startsWith(pre) && name.endsWith('.v1.bin')) o[name.slice(pre.length, -7)] = new Uint8Array(fs.readFileSync(dir + name))
  }
  return o
}
function readFilesV2() {
  const o = {}
  for (const name of fs.readdirSync(dir)) {
    const pre = `${layout}-${N}-${P}-`
    if (name.startsWith(pre) && name.endsWith('.v2.bin')) o[name.slice(pre.length, -7)] = new Uint8Array(fs.readFileSync(dir + name))
  }
  return o
}

if (mode === 'build') {
  const strokes = genStrokes(N)
  const raw = strokes.reduce((n, s) => n + s.packed.length, 0)
  const updateSizes = []
  const [buildMs, board] = T(() => buildBoard(layout, strokes, P, updateSizes))
  // encode + persist (for the memory children)
  for (const f2 of fs.readdirSync(dir)) if (f2.startsWith(`${layout}-${N}-${P}-`)) fs.unlinkSync(dir + f2)
  const out = {}
  const sizes = { v1: 0, v2: 0, rootV1: 0, rootV2: 0, perDoc: [] }
  const put = (key, d) => {
    const v1 = Y.encodeStateAsUpdate(d), v2 = Y.encodeStateAsUpdateV2(d)
    fs.writeFileSync(`${dir}${layout}-${N}-${P}-${key}.v1.bin`, v1); fs.writeFileSync(`${dir}${layout}-${N}-${P}-${key}.v2.bin`, v2)
    sizes.v1 += v1.length; sizes.v2 += v2.length
    return [v1.length, v2.length]
  }
  if (layout === 'A') put('page0', board.docs[0])
  else {
    if (layout === 'B') { const [a, b] = put('root', board.root); sizes.rootV1 = a; sizes.rootV2 = b }
    board.docs.forEach((d, i) => sizes.perDoc.push(put('page-' + i, d)))
  }
  out.rawPayloadBytes = raw
  out.sizes = { v1: sizes.v1, v2: sizes.v2, rootV1: sizes.rootV1, rootV2: sizes.rootV2, pageV1: sizes.perDoc.length ? median(sizes.perDoc.map((a) => a[0])) : null, pageV2: sizes.perDoc.length ? median(sizes.perDoc.map((a) => a[1])) : null }
  out.buildMs = buildMs
  out.update = { mean: updateSizes.reduce((a, b) => a + b, 0) / updateSizes.length, median: median(updateSizes), p95: pct(updateSizes, 0.95), n: updateSizes.length, avgStrokeBytes: raw / N }
  // cold load timings from fresh docs each rep (build objects released first)
  board.docs.length = 0
  const files = readFiles(), files2 = readFilesV2()
  const rep = (fn) => { const a = []; for (let i = 0; i < REPS + 1; i++) a.push(T(fn)[0]); a.shift(); return median(a) } // first rep discarded (JIT warm-up)
  const t = {}
  t.applyFullV1 = rep(() => loadFull(files))
  t.applyFullV2 = rep(() => loadFull(files2, Y.applyUpdateV2))
  { const a = []; for (let i = 0; i < REPS + 1; i++) { const b = loadFull(files); a.push(T(() => readAll(b))[0]) } a.shift(); t.readFull = median(a) }
  t.openPageApply = rep(() => loadPage0(files))
  { const a = []; for (let i = 0; i < REPS + 1; i++) { const b = loadPage0(files); a.push(T(() => readPage0(b))[0]) } a.shift(); t.openPageRead = median(a) }
  out.ms = t
  console.log(JSON.stringify(out))
} else {
  // memory: heap used delta of holding freshly loaded docs
  let files = readFiles()
  gc(); const m0 = process.memoryUsage()
  const held = mode === 'memfull' ? loadFull(files) : loadPage0(files)
  files = null
  gc(); const m1 = process.memoryUsage()
  console.log(JSON.stringify({ heapDelta: m1.heapUsed - m0.heapUsed, extDelta: m1.arrayBuffers - m0.arrayBuffers, held: held.docs.length }))
}
