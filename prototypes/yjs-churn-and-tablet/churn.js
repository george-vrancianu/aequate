// PROTOTYPE (throwaway): Yjs board under erase/undo/redo churn. Stroke generator copied into ./lib.js from ../yjs-board-sync/lib.js.
// Orchestrator:  node --expose-gc churn.js [quick]      Child (one config):  node --expose-gc churn.js --child '<json>'
import * as Y from 'yjs'
import { spawn, execSync } from 'node:child_process'
import fs from 'node:fs'
import { mulberry32, genStroke, pack, median, pct } from './lib.js'

const P = 20, USERS = 3, CAP = 100
const CHECKPOINTS = [0, 0.5, 1, 3]
const varintLen = (v) => { let n = 1; while (v > 127) { n++; v = Math.floor(v / 128) } return n }
const hashBytes = (b) => { let h = 2166136261; for (let i = 0; i < b.length; i++) { h ^= b[i]; h = Math.imul(h, 16777619) } return (h >>> 0).toString(16) + ':' + b.length }
const gcNow = () => { global.gc(); global.gc() }
const mem = () => { gcNow(); const m = process.memoryUsage(); return { heap: m.heapUsed, ab: m.arrayBuffers } }
const memDelta = (a, b) => ({ heap: b.heap - a.heap, ab: b.ab - a.ab, total: b.heap + b.ab - a.heap - a.ab })

// ---------------------------------------------------------------- struct / delete-set stats
function structStats(doc) {
  const s = { items: 0, deletedItems: 0, gcStructs: 0, retainedDeleted: 0, retainedBytes: 0, keepFlagged: 0 }
  doc.store.clients.forEach((structs) => {
    for (const st of structs) {
      if (st instanceof Y.GC) { s.gcStructs++; continue }
      s.items++
      if (st.keep) s.keepFlagged++
      if (st.deleted) {
        s.deletedItems++
        const c = st.content
        if (!(c instanceof Y.ContentDeleted)) {
          s.retainedDeleted++
          if (c.content instanceof Uint8Array) s.retainedBytes += c.content.length
          else if (c.arr) for (const v of c.arr) s.retainedBytes += v?.length ?? 0
        }
      }
    }
  })
  const ds = Y.createDeleteSetFromStructStore(doc.store)
  let ranges = 0, clocks = 0, bytes = varintLen(ds.clients.size)
  ds.clients.forEach((items, client) => {
    bytes += varintLen(client) + varintLen(items.length)
    ranges += items.length
    for (const it of items) { clocks += it.len; bytes += varintLen(it.clock) + varintLen(it.len) }
  })
  s.dsRanges = ranges; s.dsDeletedClocks = clocks; s.dsBytesV1 = bytes; s.dsClients = ds.clients.size
  s.deletedTotal = s.deletedItems + s.gcStructs // GC structs are items that lost their content AND their parent entry
  return s
}
const addStats = (a, b) => { for (const k in b) a[k] = (a[k] ?? 0) + b[k]; return a }

// ---------------------------------------------------------------- world: 3 users (own replica + UndoManager each) + a server replica (no UndoManager, like Hocuspocus)
function makeWorld(layout, cfg, rng) {
  const nDocs = layout === 'board' ? 1 : P
  const parts = [] // participant: {docs[], origin, ums[], ...}
  const queues = []
  const upd = { draw: [], erase: [], undo: [], redo: [] }
  const world = { layout, cfg, parts, upd, curOp: 'draw', truth: new Map() }
  for (let r = 0; r <= USERS; r++) {
    const docs = Array.from({ length: nDocs }, (_, i) => { const d = new Y.Doc({ gc: cfg.gc, guid: layout === 'board' ? 'board' : 'page-' + i }); d.clientID = 100 + r * 11 + 1; return d })
    parts.push({ r, docs, origin: 'user-' + r, ums: [], undoG: [], redoG: [], busy: false, isServer: r === USERS })
    queues.push(Array.from({ length: nDocs }, () => []))
  }
  parts.forEach((pt) => pt.docs.forEach((d, di) => d.on('update', (u, o) => {
    if (o === 'remote') return
    if (!pt.isServer && world.curOp) upd[world.curOp].push(u.length)
    parts.forEach((q) => { if (q !== pt) queues[q.r][di].push(u) })
  })))
  const di = (p) => (layout === 'board' ? 0 : p)
  world.map = (pt, p) => pt.docs[di(p)].getMap(layout === 'board' ? 'strokes:' + p : 'strokes')
  const release = (pt, di_, si) => { if (cfg.cap === 'release') Y.iterateDeletedStructs({ doc: pt.docs[di_] }, si.deletions, (it) => { if (it instanceof Y.Item) it.keep = false }) }
  if (cfg.cap !== 'noum') {
    parts.slice(0, USERS).forEach((pt) => {
      const mkUm = (scope, di_) => new Y.UndoManager(scope, { trackedOrigins: new Set([pt.origin]), captureTimeout: 0 })
      if (layout === 'board') {
        const um = mkUm(Array.from({ length: P }, (_, p) => pt.docs[0].getMap('strokes:' + p)), 0)
        pt.ums = [um]
        if (cfg.cap !== 'none') um.on('stack-item-added', ({ type }) => {
          const st = type === 'undo' ? um.undoStack : um.redoStack
          while (st.length > CAP) { const si = st.shift(); release(pt, 0, si) }
        })
      } else {
        pt.ums = pt.docs.map((d, i) => mkUm(d.getMap('strokes'), i))
        pt.ums.forEach((um, p) => um.on('stack-item-added', ({ type }) => {
          if (type !== 'undo' || pt.busy) return
          pt.undoG.push(p)
          pt.redoG.length = 0; pt.ums.forEach((u) => u.clear(false, true))
          if (cfg.cap !== 'none') while (pt.undoG.length > CAP) { const q = pt.undoG.shift(); const si = pt.ums[q].undoStack.shift(); release(pt, q, si) }
        }))
      }
    })
  }
  world.undoLen = (pt) => (layout === 'board' ? pt.ums[0]?.undoStack.length : pt.undoG.length) ?? 0
  world.redoLen = (pt) => (layout === 'board' ? pt.ums[0]?.redoStack.length : pt.redoG.length) ?? 0
  world.undo = (pt) => {
    if (!pt.ums.length) return false
    world.curOp = 'undo'
    let r
    if (layout === 'board') r = pt.ums[0].undo()
    else { const p = pt.undoG.pop(); if (p === undefined) { world.curOp = 'draw'; return false } pt.busy = true; r = pt.ums[p].undo(); pt.busy = false; if (r) pt.redoG.push(p) }
    world.curOp = 'draw'; return !!r
  }
  world.redo = (pt) => {
    if (!pt.ums.length) return false
    world.curOp = 'redo'
    let r
    if (layout === 'board') r = pt.ums[0].redo()
    else { const p = pt.redoG.pop(); if (p === undefined) { world.curOp = 'draw'; return false } pt.busy = true; r = pt.ums[p].redo(); pt.busy = false; if (r) pt.undoG.push(p) }
    world.curOp = 'draw'; return !!r
  }
  let idc = 0
  world.draw = (pt, p, packed) => {
    const id = 's' + (idc++).toString(36) + '-' + Math.floor(rng() * 1e6).toString(36)
    world.truth.set(id, hashBytes(packed))
    world.curOp = 'draw'
    pt.docs[di(p)].transact(() => world.map(pt, p).set(id, packed), pt.origin)
    return id
  }
  world.erase = (pt, p, id) => { world.curOp = 'erase'; pt.docs[di(p)].transact(() => world.map(pt, p).delete(id), pt.origin); world.curOp = 'draw' }
  const deliver = (r, d, n) => { const q = queues[r][d], m = n ?? q.length; for (let i = 0; i < m && q.length; i++) Y.applyUpdate(parts[r].docs[d], q.shift(), 'remote') }
  world.flush = () => { for (let k = 0; k < 2; k++) for (let r = 0; r <= USERS; r++) for (let d = 0; d < nDocs; d++) deliver(r, d) }
  world.total = (pt) => { let n = 0; for (let p = 0; p < P; p++) n += world.map(pt, p).size; return n }
  world.liveBytes = (pt) => { let n = 0; for (let p = 0; p < P; p++) world.map(pt, p).forEach((v) => { n += v.length }); return n }
  return world
}

// ---------------------------------------------------------------- measurements
const encodeAll = (pt, v2) => pt.docs.map((d) => (v2 ? Y.encodeStateAsUpdateV2(d) : Y.encodeStateAsUpdate(d)))
function coldLoad(updates, gc, reps = 5) {
  const times = [], pageTimes = []
  for (let i = 0; i < reps + 1; i++) {
    const t0 = performance.now()
    const docs = updates.map((u) => { const d = new Y.Doc({ gc }); Y.applyUpdate(d, u); return d })
    const t = performance.now() - t0
    if (i > 0) times.push(t)
    docs.forEach((d) => d.destroy())
  }
  // one page: apply the single page doc (page layout) / the whole board doc (board layout; same thing)
  const one = updates.length === 1 ? updates[0] : updates[Math.floor(updates.length / 2)]
  for (let i = 0; i < reps + 1; i++) { const t0 = performance.now(); const d = new Y.Doc({ gc }); Y.applyUpdate(d, one); const t = performance.now() - t0; if (i > 0) pageTimes.push(t); d.destroy() }
  const m0 = mem()
  const docs = updates.map((u) => { const d = new Y.Doc({ gc }); Y.applyUpdate(d, u); return d })
  const m1 = mem()
  const stats = {}; docs.forEach((d) => addStats(stats, structStats(d)))
  const reEncoded = docs.reduce((n, d) => n + Y.encodeStateAsUpdate(d).length, 0)
  const out = { wholeBoardMs: median(times), onePageMs: median(pageTimes), mem: memDelta(m0, m1), stats, reEncodedBytes: reEncoded }
  docs.forEach((d) => d.destroy())
  return out
}
const q = (a) => (a.length ? { n: a.length, mean: a.reduce((x, y) => x + y, 0) / a.length, median: median(a), p95: pct(a, 0.95), max: Math.max(...a), total: a.reduce((x, y) => x + y, 0) } : { n: 0 })

function checkpoint(world, label, ops, timing) {
  world.flush()
  const server = world.parts[USERS], u0 = world.parts[0]
  const live = world.total(server), livePayload = world.liveBytes(server)
  const enc = encodeAll(server), encV2 = encodeAll(server, true), encClient = encodeAll(u0)
  const sum = (a) => a.reduce((n, u) => n + u.length, 0)
  const serverStats = {}; server.docs.forEach((d) => addStats(serverStats, structStats(d)))
  const clientStats = {}; u0.docs.forEach((d) => addStats(clientStats, structStats(d)))
  const cl = { gcTrue: coldLoad(enc, true), gcFalse: coldLoad(enc, false) }
  const um = { undo: world.undoLen(u0), redo: world.redoLen(u0) }
  const row = { label, ops: { ...ops }, liveStrokes: live, livePayloadBytes: livePayload, encodedServerV1: sum(enc), encodedServerV2: sum(encV2), encodedClientV1: sum(encClient),
    overheadServer: sum(enc) / livePayload, overheadClient: sum(encClient) / livePayload, serverStats, clientStats, coldLoad: cl, userStack: um, churnMsPerIter: timing }
  const upd = {}; for (const k in world.upd) upd[k] = q(world.upd[k]); row.updateBytes = upd
  return row
}

// ---------------------------------------------------------------- correctness checks
function checks(world) {
  const res = [], check = (name, pass, detail = '') => res.push({ name, pass: !!pass, detail: String(detail).slice(0, 200) })
  const { parts } = world, [X, Y2] = parts, server = parts[USERS], layout = world.layout
  const hasUm = X.ums.length > 0
  const keysOf = (pt) => { const o = []; for (let p = 0; p < P; p++) world.map(pt, p).forEach((v, k) => o.push(p + ':' + k + ':' + hashBytes(v))); return o.sort().join('|') }
  const present = (pt, p, id) => world.map(pt, p).has(id)
  const get = (pt, p, id) => world.map(pt, p).get(id)
  const pickLive = (pt, avoid = new Set()) => { for (let p = 0; p < P; p++) { const pp = (p * 7 + 3) % P; for (const k of world.map(pt, pp).keys()) if (!avoid.has(k)) return [pp, k] } }
  const allEq = () => { world.flush(); const k = keysOf(parts[0]); return parts.every((pt) => keysOf(pt) === k) }
  const svEq = () => parts.every((pt) => pt.docs.every((d, i) => Buffer.compare(Buffer.from(Y.encodeStateVector(d)), Buffer.from(Y.encodeStateVector(parts[0].docs[i]))) === 0))
  world.flush()
  check('convergence: 3 user replicas + server have identical content after churn', allEq())
  check('convergence: identical state vectors', svEq())
  check('integrity: every live stroke equals the bytes originally drawn', (() => { let bad = 0; for (let p = 0; p < P; p++) world.map(server, p).forEach((v, k) => { if (world.truth.get(k) !== hashBytes(v)) bad++ }); return bad === 0 })())
  check('cold load of server state: content identical', keysOf({ docs: server.docs.map((d) => { const f = new Y.Doc({ gc: true }); Y.applyUpdate(f, Y.encodeStateAsUpdate(d)); return f }) }) === keysOf(server))
  if (!hasUm) { check('undo checks skipped (no UndoManager variant)', true, 'n/a'); return res }
  // erase -> undo -> redo -> undo
  {
    const [p, id] = pickLive(X), h = hashBytes(get(X, p, id))
    world.erase(X, p, id); world.flush()
    check('erase removed the stroke on every replica', parts.every((pt) => !present(pt, p, id)))
    const u = world.undoLen(X)
    const ok = world.undo(X); world.flush()
    check('undo of an erase after heavy churn restores the stroke (content equal) on every replica', ok && parts.every((pt) => present(pt, p, id) && hashBytes(get(pt, p, id)) === h), `undoStack before=${u}`)
    world.redo(X); world.flush()
    check('redo erases it again on every replica', parts.every((pt) => !present(pt, p, id)))
    world.undo(X); world.flush()
    check('second undo restores it again (content equal)', parts.every((pt) => present(pt, p, id) && hashBytes(get(pt, p, id)) === h))
    check('state converged after the undo/redo round', allEq() && svEq())
  }
  // interleaved: two users erase concurrently, only own erase is undone
  {
    const [pa, a] = pickLive(X); const [pb, b] = pickLive(Y2, new Set([a]))
    const ha = hashBytes(get(X, pa, a)), hb = hashBytes(get(Y2, pb, b))
    world.erase(X, pa, a); world.erase(Y2, pb, b) // concurrent, no flush between
    world.flush()
    world.undo(X); world.flush()
    check('interleaved: X undo restores only X erase (a back, b still gone, content equal)', parts.every((pt) => present(pt, pa, a) && hashBytes(get(pt, pa, a)) === ha && !present(pt, pb, b)))
    world.undo(Y2); world.flush()
    check('interleaved: Y undo then restores b (content equal)', parts.every((pt) => present(pt, pb, b) && hashBytes(get(pt, pb, b)) === hb))
  }
  // concurrent erase of the SAME stroke by both users, then each undoes
  {
    const [p, id] = pickLive(X); const h = hashBytes(get(X, p, id))
    world.erase(X, p, id); world.erase(Y2, p, id); world.flush()
    world.undo(X); world.flush()
    check('double erase of one stroke by two users: X undo restores it', parts.every((pt) => present(pt, p, id) && hashBytes(get(pt, p, id)) === h))
    world.undo(Y2); world.flush()
    check('double erase: Y undo afterwards keeps convergence', allEq())
  }
  // stack cap + drain
  const cap = world.cfg.cap
  if (cap === 'splice' || cap === 'release') check(`undo stack bounded by cap ${CAP}`, world.undoLen(X) <= CAP && world.undoLen(Y2) <= CAP, `X=${world.undoLen(X)} Y=${world.undoLen(Y2)} redoX=${world.redoLen(X)}`)
  {
    let n = 0; while (n < 300 && world.undo(X)) n++
    world.flush()
    const e1 = allEq(), e2 = svEq(); check(`drain: ${n} consecutive undos by X (stack ${cap === 'none' ? 'unbounded, limited to 300' : 'capped'}) run without error and converge`, e1 && e2, 'undos=' + n + ' content=' + e1 + ' sv=' + e2 + ' sizes=' + parts.map((pt) => world.total(pt)).join('/') + ' pending=' + parts.map((pt) => (pt.docs[0].store.pendingStructs ? 1 : 0) + (pt.docs[0].store.pendingDs ? 1 : 0)).join('/'))
    let m = 0; while (m < 300 && world.redo(X)) m++
    world.flush()
    check(`drain: ${m} redos (the ${n} undos plus older redo entries) converge`, allEq() && svEq() && m > 0, `redos=${m}`)
  }
  check('final integrity: every live stroke equals the bytes originally drawn', (() => { let bad = 0; for (let p = 0; p < P; p++) world.map(server, p).forEach((v, k) => { if (world.truth.get(k) !== hashBytes(v)) bad++ }); return bad === 0 })())
  return res
}

// ---------------------------------------------------------------- one config
function runChild(cfg) {
  const rng = mulberry32(cfg.seed ?? 7)
  const N = cfg.N
  const base = mem()
  const world = makeWorld(cfg.layout, cfg, rng)
  const [X] = world.parts
  const users = world.parts.slice(0, USERS)
  // seed: N strokes from an untracked origin on user 0, spread over P pages
  for (let i = 0; i < N; i++) {
    const p = Math.floor((i * P) / N), packed = pack(genStroke(rng))
    const id = 'seed' + i.toString(36)
    world.truth.set(id, hashBytes(packed))
    X.docs[cfg.layout === 'board' ? 0 : p].transact(() => world.map(X, p).set(id, packed), 'seed')
  }
  world.flush()
  for (const k in world.upd) world.upd[k].length = 0 // do not count seeding as churn updates
  const ops = { erases: 0, redraws: 0, undos: 0, redos: 0, iterations: 0 }
  const rows = []
  const randStroke = (pt) => { for (let t = 0; t < 8; t++) { const p = Math.floor(rng() * P); const m = world.map(pt, p); if (m.size) { const keys = [...m.keys()]; return [p, keys[Math.floor(rng() * keys.length)]] } } return null }
  rows.push(checkpoint(world, '0x', ops, 0))
  let churnMs = 0
  const targets = CHECKPOINTS.slice(1).map((r) => Math.round(r * N))
  let ti = 0
  const t00 = performance.now()
  while (ti < targets.length) {
    const t0 = performance.now()
    const nAct = rng() < 0.2 ? 2 : 1
    const acting = [0, 1, 2].sort(() => rng() - 0.5).slice(0, nAct)
    let first = null
    for (const ui of acting) {
      const pt = users[ui]
      let tgt = randStroke(pt)
      if (nAct === 2 && first && rng() < 0.25 && world.map(pt, first[0]).has(first[1])) tgt = first // concurrent double-erase
      if (!tgt) continue
      first ??= tgt
      world.erase(pt, tgt[0], tgt[1]); ops.erases++
    }
    for (const ui of acting) {
      const pt = users[ui]
      if (pt.ums.length && rng() < 0.35) {
        if (world.undo(pt)) { ops.undos++; if (rng() < 0.5 && world.redo(pt)) ops.redos++ }
      }
    }
    world.flush()
    // restore the live count with fresh strokes (re-draw)
    while (world.total(users[0]) < N) { world.draw(users[Math.floor(rng() * USERS)], Math.floor(rng() * P), pack(genStroke(rng))); ops.redraws++; world.flush() }
    // undo of an erase brings a stroke back AND the redraw may overshoot: erase surplus
    while (world.total(users[0]) > N) { const t = randStroke(users[0]); world.erase(users[0], t[0], t[1]); ops.erases++; world.flush() }
    world.flush()
    ops.iterations++
    churnMs += performance.now() - t0
    if (ops.iterations >= targets[ti]) {
      const label = CHECKPOINTS[ti + 1] + 'x'
      const tCp = performance.now()
      const lm = mem()
      rows.push(checkpoint(world, label, ops, churnMs / ops.iterations))
      rows[rows.length - 1].processMemAfterGc = memDelta(base, lm)
      churnMs += 0; ti++
      // do not count checkpoint time
      void tCp
    }
  }
  const wall = (performance.now() - t00) / 1000
  const cx = checks(world)
  // retention experiment: what the undo stack holds, and what releasing it does to the LIVE doc vs a reload
  const retention = {}
  if (cfg.retention && X.ums.length) {
    retention.beforeClear = { clientStats: sumStats(X), stack: { undo: world.undoLen(X), redo: world.redoLen(X) } }
    X.ums.forEach((um) => um.clear())
    X.undoG.length = 0; X.redoG.length = 0
    const m = mem()
    retention.afterClear = { clientStats: sumStats(X), encodedClientV1: encodeAll(X).reduce((n, u) => n + u.length, 0), mem: memDelta(base, m) }
    const reload = X.docs.map((d) => { const f = new Y.Doc({ gc: true }); Y.applyUpdate(f, Y.encodeStateAsUpdate(d)); return f })
    const rs = {}; reload.forEach((d) => addStats(rs, structStats(d)))
    retention.afterReloadGcTrue = { stats: rs, encodedV1: reload.reduce((n, d) => n + Y.encodeStateAsUpdate(d).length, 0) }
  }
  return { cfg, wallSeconds: wall, rows, checks: cx, retention }
}
const sumStats = (pt) => { const s = {}; pt.docs.forEach((d) => addStats(s, structStats(d))); return s }

// ---------------------------------------------------------------- orchestrator
function usedGb() { try { return Number(execSync("free -g | awk '/Mem:/{print $3}'").toString().trim()) } catch { return 0 } }
async function waitForMemory() { while (usedGb() > 18) { console.log('  waiting for host memory (used ' + usedGb() + ' GB)'); await new Promise((r) => setTimeout(r, 15000)) } }
const runOne = (cfg) => new Promise((resolve, reject) => {
  const ch = spawn('node', ['--max-old-space-size=4096', '--expose-gc', new URL(import.meta.url).pathname, '--child', JSON.stringify(cfg)], { stdio: ['ignore', 'pipe', 'inherit'] })
  let out = ''; ch.stdout.on('data', (d) => (out += d))
  ch.on('exit', (c) => (c === 0 ? resolve(JSON.parse(out)) : reject(new Error('child failed ' + c + ' ' + JSON.stringify(cfg)))))
})

if (process.argv[2] === '--child') {
  process.stdout.write(JSON.stringify(runChild(JSON.parse(process.argv[3]))))
} else {
  const quick = process.argv[2] === 'quick'
  const sizes = quick ? [1000] : [1000, 5000, 10000]
  const cfgs = []
  for (const N of sizes) for (const layout of ['board', 'page']) for (const gc of [true, false]) cfgs.push({ name: `main-${layout}-${N}-gc${gc}`, N, layout, gc, cap: 'splice' })
  if (!quick) for (const layout of ['board', 'page']) for (const cap of ['noum', 'none', 'release']) cfgs.push({ name: `retain-${layout}-5000-gctrue-${cap}`, N: 5000, layout, gc: true, cap, retention: true })
  if (!quick) for (const layout of ['board', 'page']) cfgs.push({ name: `retain-${layout}-5000-gctrue-splice`, N: 5000, layout, gc: true, cap: 'splice', retention: true })
  fs.mkdirSync('results', { recursive: true })
  const all = []
  for (const cfg of cfgs) {
    await waitForMemory()
    const t = Date.now()
    process.stdout.write(`${cfg.name} ... `)
    const r = await runOne(cfg)
    fs.writeFileSync(`results/${cfg.name}.json`, JSON.stringify(r))
    all.push(r)
    const f = r.checks.filter((c) => !c.pass).length
    console.log(`${((Date.now() - t) / 1000).toFixed(0)}s, failed checks: ${f}`)
  }
  fs.writeFileSync(quick ? 'results/quick.json' : 'results.json', JSON.stringify(all, null, 1))
}
