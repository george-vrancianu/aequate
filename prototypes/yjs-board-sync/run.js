// PROTOTYPE (throwaway): runs everything sequentially -> results.json + results-tables.md
// Each measurement runs in its own child process (clean heap, capped at 4 GB, gc exposed).
import { spawnSync } from 'node:child_process'
import fs from 'node:fs'
import os from 'node:os'
import { runUndoChecks } from './undo.js'

const here = new URL('.', import.meta.url).pathname
const NODE = ['--max-old-space-size=4096', '--expose-gc']
const SIZES = [1000, 3000, 5000, 10000], PAGES = [1, 5, 20], LAYOUTS = ['A', 'B', 'C']
const t0 = Date.now()
let peakUsedGB = 0

function usedGB() {
  const m = Object.fromEntries(fs.readFileSync('/proc/meminfo', 'utf8').split('\n').filter(Boolean).map((l) => { const [k, v] = l.split(/:\s+/); return [k, parseInt(v)] }))
  return (m.MemTotal - m.MemAvailable) / 1024 / 1024
}
async function waitMem() {
  for (;;) { const u = usedGB(); peakUsedGB = Math.max(peakUsedGB, u); if (u < 18) return; console.error(`memory used ${u.toFixed(1)} GB > 18, waiting`); await new Promise((r) => setTimeout(r, 10000)) }
}
function child(script, args) {
  const r = spawnSync('node', [...NODE, here + script, ...args], { encoding: 'utf8', maxBuffer: 1 << 28 })
  if (r.status !== 0) throw new Error(`${script} ${args} failed: ${r.stderr}`)
  return JSON.parse(r.stdout)
}

const results = { machine: { cpu: fs.readFileSync('/proc/cpuinfo', 'utf8').match(/model name\s*:\s*(.*)/)[1], cores: os.cpus().length, node: process.version, kernel: os.release(), totalMemGB: +(os.totalmem() / 2 ** 30).toFixed(1) }, undo: {}, pure: [], hocuspocus: null }

console.error('undo checks')
for (const l of LAYOUTS) results.undo[l] = runUndoChecks(l)

for (const N of SIZES) for (const P of PAGES) for (const L of LAYOUTS) {
  await waitMem()
  const b = child('measure.js', ['build', L, N, P])
  const full = child('measure.js', ['memfull', L, N, P])
  const page = child('measure.js', ['mempage', L, N, P])
  results.pure.push({ layout: L, N, P, ...b, mem: { fullHeap: full.heapDelta, pageHeap: page.heapDelta } })
  console.error(`pure ${L} N=${N} P=${P} done (${((Date.now() - t0) / 1000).toFixed(0)}s)`)
}

await waitMem()
console.error('hocuspocus')
results.hocuspocus = child('hp.js', SIZES.map(String))
results.runSeconds = Math.round((Date.now() - t0) / 1000)
results.peakUsedGB = +peakUsedGB.toFixed(1)
fs.writeFileSync(here + 'results.json', JSON.stringify(results, null, 1))

// ---------- tables ----------
const kb = (n) => (n / 1024).toFixed(0)
const mb = (n) => (n / 1048576).toFixed(1)
const ms = (n) => (n < 10 ? n.toFixed(2) : n < 100 ? n.toFixed(1) : n.toFixed(0))
const get = (L, N, P) => results.pure.find((r) => r.layout === L && r.N === N && r.P === P)
let md = ''
const table = (head, rows) => { md += `| ${head.join(' | ')} |\n|${head.map(() => '---').join('|')}|\n` + rows.map((r) => `| ${r.join(' | ')} |`).join('\n') + '\n\n' }
const grid = (fn, head) => { const rows = []; for (const N of SIZES) for (const P of PAGES) rows.push([N, P, ...LAYOUTS.flatMap((L) => fn(get(L, N, P)))]); return [['strokes', 'pages', ...head], rows] }
const H3 = (a) => LAYOUTS.flatMap((L) => a.map((x) => `${L} ${x}`))

md += '### Undo correctness (two clients, per-origin UndoManager, cap)\n\n'
const names = results.undo.A.checks.map((c) => c.name)
const allNames = [...new Set(LAYOUTS.flatMap((L) => results.undo[L].checks.map((c) => c.name)))]
table(['check', 'A', 'B', 'C'], allNames.map((n) => [n, ...LAYOUTS.map((L) => { const c = results.undo[L].checks.find((x) => x.name === n); return c ? (c.pass ? 'PASS' : '**FAIL**') : 'n/a' })]))
md += LAYOUTS.map((L) => results.undo[L].notes.map((n) => `- ${L}: ${n}`).join('\n')).join('\n') + '\n\n'

md += '### Encoded size in bytes (Yjs update as stored/sent; B and C = sum over all docs)\n\n'
{ const [h, r] = grid((x) => [x.sizes.v1, x.sizes.v2], ['v1', 'v2']); h.splice(2, 6, ...H3(['v1', 'v2'])); table(['strokes', 'pages', 'raw packed payload', ...H3(['v1 B', 'v2 B']), 'B root doc v1 B'], r.map((row, i) => { const N = row[0], P = row[1]; return [N, P, get('A', N, P).rawPayloadBytes, ...row.slice(2), get('B', N, P).sizes.rootV1] })) }

md += '### Update size per stroke (bytes of the update emitted by one pen-up transaction; median / p95 over all strokes of the build)\n\n'
{ const rows = []; for (const N of SIZES) for (const P of PAGES) rows.push([N, P, get('A', N, P).update.avgStrokeBytes.toFixed(0), ...LAYOUTS.map((L) => `${get(L, N, P).update.median} / ${get(L, N, P).update.p95}`)]); table(['strokes', 'pages', 'avg packed stroke B', 'A', 'B', 'C'], rows) }

md += '### Cold load, whole board (ms, median of 7 fresh docs; apply = decode + integrate the stored update, read = unpack every stroke)\n\n'
{ const rows = []; for (const N of SIZES) for (const P of PAGES) rows.push([N, P, ...LAYOUTS.flatMap((L) => { const m = get(L, N, P).ms; return [ms(m.applyFullV1), ms(m.applyFullV2), ms(m.readFull)] })]); table(['strokes', 'pages', ...H3(['apply v1', 'apply v2', 'read'])], rows) }

md += '### Open a single page (ms, median; A must load the whole board, B = root doc + that subdoc, C = that doc only)\n\n'
{ const rows = []; for (const N of SIZES) for (const P of PAGES) rows.push([N, P, ...LAYOUTS.flatMap((L) => { const m = get(L, N, P).ms; return [ms(m.openPageApply), ms(m.openPageRead)] })]); table(['strokes', 'pages', ...H3(['apply', 'read page'])], rows) }

md += '### Memory (heap used delta after gc, fresh child process; MB)\n\n'
{ const rows = []; for (const N of SIZES) for (const P of PAGES) rows.push([N, P, ...LAYOUTS.flatMap((L) => [mb(get(L, N, P).mem.fullHeap), mb(get(L, N, P).mem.pageHeap)])]); table(['strokes', 'pages', ...H3(['whole board', 'one page'])], rows) }

md += '### Hocuspocus over local WebSocket: fresh client sync\n\nTime from constructing the provider to the first `synced`, server loading the doc from SQLite each rep (median of 7). Board of A uses 5 page maps; C uses separate documents.\n\n'
table(['strokes', 'layout', 'pages', 'what is synced', 'client sync ms', 'of which server load ms', 'strokes received'], results.hocuspocus.sync.map((s) => [s.N, s.layout, s.P, s.what, ms(s.ms), ms(s.serverLoadMs), s.strokesReceived]))
md += '### Hocuspocus: per-save cost after adding one stroke (SQLite whole-doc upsert)\n\nonStoreDocument = `encodeStateAsUpdate` of the whole doc + write. "Stroke to stored" includes the configured 20 ms server debounce.\n\n'
table(['strokes', 'layout', 'pages', 'doc', 'bytes written per save', 'bytes of the stroke update', 'write amplification', 'encode ms', 'sqlite write ms', 'onStoreDocument ms', 'stroke to stored ms'], results.hocuspocus.save.map((s) => [s.N, s.layout, s.P, s.what, s.docBytesWritten, s.updateBytes, (s.docBytesWritten / s.updateBytes).toFixed(0) + 'x', ms(s.encodeMs), ms(s.writeMs), ms(s.onStoreMs), ms(s.strokeToStoredMs)]))
md += '### Hocuspocus: layout B (subdocuments)\n\n```json\n' + JSON.stringify(results.hocuspocus.subdoc, null, 1) + '\n```\n'
fs.writeFileSync(here + 'results-tables.md', md)
console.error(`done in ${results.runSeconds}s, peak used ${results.peakUsedGB} GB`)
rmTmp()
function rmTmp() { fs.rmSync(here + '.tmp', { recursive: true, force: true }) }
