// PROTOTYPE (throwaway): `npm run bench` => runs each size in its own node process, then the crash tests, writes results.json + RESULTS tables.
// `node bench.js --size N` runs one size (child mode).
import * as Y from 'yjs'
import fs from 'node:fs'
import path from 'node:path'
import { spawnSync, execSync } from 'node:child_process'
import { genStrokes, buildBoard, mulberry32, pageOf, median } from './lib.js'
import { loadFromStorage, digest, sameDigest, COUNT, BYTES } from './store.js'
import { sleep, waitFor, scratchDir, startServer, connect, waitUnloaded, startPing, stat, DEBOUNCE, MAX_DEBOUNCE, PACE_MS } from './common.js'

const here = path.dirname(new URL(import.meta.url).pathname)
const SIZES = [1000, 3000, 5000, 10000]
const BOARD_MAPS = [0, 1, 2, 3, 4].map((p) => 'strokes:' + p)
const r1 = (x) => Math.round(x * 10) / 10

function waitMem() {
  for (;;) {
    const used = +execSync("free -g | awk '/^Mem:/{print $3}'").toString().trim()
    if (used <= 18) return used
    console.error(`  memory used ${used} GB > 18, waiting...`); Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 15000)
  }
}

// ======================= orchestrator =======================
if (!process.argv.includes('--size')) {
  const out = { meta: { node: process.version, yjs: '13.6.x', debounce: DEBOUNCE, maxDebounce: MAX_DEBOUNCE, paceMs: PACE_MS, COUNT, BYTES, date: new Date().toISOString(), note: 'WSL2: numbers are relative' }, sizes: {}, crash: null }
  const only = process.argv.slice(2).map(Number).filter(Boolean)
  for (const N of only.length ? only : SIZES) {
    const used = waitMem(); console.error(`== size ${N} (mem used ${used} GB)`)
    const r = spawnSync('node', ['--max-old-space-size=4096', '--expose-gc', 'bench.js', '--size', String(N)], { cwd: here, encoding: 'utf8', maxBuffer: 1 << 28, stdio: ['ignore', 'pipe', 'inherit'] })
    const line = r.stdout.split('\n').find((l) => l.startsWith('RESULT '))
    if (!line) { console.error(r.stdout); throw new Error('size ' + N + ' failed') }
    out.sizes[N] = JSON.parse(line.slice(7))
  }
  console.error('== crash tests')
  const r = spawnSync('node', ['crash.js'], { cwd: here, encoding: 'utf8', stdio: ['ignore', 'pipe', 'inherit'] })
  out.crash = JSON.parse(r.stdout.split('\n').find((l) => l.startsWith('RESULT ')).slice(7))
  fs.writeFileSync(path.join(here, 'results.json'), JSON.stringify(out, null, 1))
  spawnSync('node', ['report.js'], { cwd: here, stdio: 'inherit' })
  fs.rmSync(path.join(here, '.tmp-wipe-me'), { recursive: true, force: true })
  process.exit(0)
}

// ======================= child: one size =======================
const N = +process.argv[process.argv.indexOf('--size') + 1]
const dir = scratchDir()
const S = await startServer(dir)
const { server, db, store, url, hp } = S
const res = { N, load: null, singleSave: [], sessions: [], hooks: null }
const writesFor = (names, from = 0) => store.writes.slice(from).filter((w) => names.includes(w.name))
const rowsOf = (name) => { const r = db.prepare('SELECT COUNT(*) c, COALESCE(SUM(LENGTH(data)),0) b FROM updates WHERE doc=?').get(name); return { rows: r.c, bytes: r.b } }
const strokes = genStrokes(N + 2000)
const base = strokes.slice(0, N), extra = strokes.slice(N)

// write all strokes through a real provider, as one update each (the "update log" a live board produces)
async function writeBoard(name, list, ps = 5) {
  const doc = new Y.Doc(); const prov = await connect(url, name, doc)
  const maps = Array.from({ length: ps }, (_, p) => doc.getMap('strokes:' + p))
  const before = store.seen.get(name) || 0
  list.forEach((s, i) => doc.transact(() => maps[pageOf(i, list.length, ps)].set(s.id, s.packed), 'me'))
  await waitFor(() => (store.seen.get(name) || 0) - before >= list.length, 120000)
  return { doc, prov, maps }
}
const coldOpen = async (name, reps = 3) => {
  const ts = [], sv = []
  for (let i = 0; i < reps + 1; i++) {
    const l0 = store.loads.length, t = performance.now(), d = new Y.Doc(), p = await connect(url, name, d)
    ts.push(performance.now() - t); sv.push(store.loads.slice(l0).reduce((a, b) => a + b.ms, 0))
    p.destroy(); await waitUnloaded(hp, name)
  }
  ts.shift(); sv.shift(); return { clientOpenMs: r1(median(ts)), serverLoadMs: r1(median(sv)) }
}
const timeIt = (f, reps = 3) => { const t = []; for (let i = 0; i < reps; i++) { const a = performance.now(); f(); t.push(performance.now() - a) } return r1(median(t)) }

// ---------- experiment L: load time, replay vs snapshot+tail, before/after compaction ----------
{
  const L = { N }
  const eraseCount = Math.floor(N / 10)
  for (const mode of ['doc', 'merge']) {
    const name = mode === 'doc' ? `ln:${N}` : `ln:m${N}`
    let w
    if (mode === 'doc') {
      w = await writeBoard(name, base)
      // erase 10% of strokes (one update each)
      const keys = [...w.maps[0].keys()]; const rng = mulberry32(9)
      const before = store.seen.get(name)
      for (let i = 0; i < eraseCount; i++) { const m = w.maps[Math.floor(rng() * 5)]; const ks = [...m.keys()]; w.doc.transact(() => m.delete(ks[Math.floor(rng() * ks.length)]), 'me') }
      await waitFor(() => store.seen.get(name) - before >= eraseCount, 120000)
      w.prov.destroy(); await waitUnloaded(hp, name)
      L.rows = rowsOf(name)
      L.liveStateBytes = Y.encodeStateAsUpdate(w.doc).length
      L.liveDigest = digest(w.doc, BOARD_MAPS)
      L.updatesAppliedToWriter = N + eraseCount
      // copy the log for the merge-mode compaction run
      db.exec(`INSERT INTO updates(doc,data) SELECT 'ln:m${N}', data FROM updates WHERE doc='${name}' ORDER BY id`)
      L.replayDirectMs = timeIt(() => loadFromStorage(db, name, { mode: 'replay' }))
      L.mergeThenApplyDirectMs = timeIt(() => loadFromStorage(db, name, { mode: 'merge' }))
      L.hocuspocusOpenBeforeCompaction = await coldOpen(name)
      L.correct_replayEqualsLive = sameDigest(digest(loadFromStorage(db, name), BOARD_MAPS), L.liveDigest)
      L.correct_mergeEqualsLive = sameDigest(digest(loadFromStorage(db, name, { mode: 'merge' }), BOARD_MAPS), L.liveDigest)
      L.liveDoc = w.doc
    }
    // compaction on a real server doc while a ping pair measures other connections
    store.compactMode = mode
    const doc = new Y.Doc(), prov = await connect(url, name, doc)
    const ping = await startPing(url, 'L' + mode); await sleep(300)
    const nBefore = store.compactions.length, tStart = performance.now()
    store.compact(name, 'manual', hp.documents.get(name))
    const c = store.compactions[nBefore]
    await sleep(300)
    const around = ping.samples.filter((s) => s.at >= c.t0 - 5 && s.at <= c.t1 + 60).map((s) => s.gap)
    const calm = ping.samples.filter((s) => s.at < c.t0 - 5).map((s) => s.gap)
    await ping.stop(); prov.destroy(); await waitUnloaded(hp, name)
    const after = {
      mode, compactMs: r1(c.ms), snapshotBytes: c.snapBytes, rowsMerged: c.rowsMerged, rowsLeft: rowsOf(name).rows,
      pingGapCalmP50Ms: r1(stat(calm).p50), pingGapMaxDuringCompactionMs: r1(Math.max(...around)),
      directLoadMs: timeIt(() => loadFromStorage(db, name)),
      hocuspocusOpen: await coldOpen(name),
      correct_equalsLive: sameDigest(digest(loadFromStorage(db, name), BOARD_MAPS), L.liveDigest),
    }
    // snapshot + 100-update tail
    const w2 = await writeBoard(name, extra.slice(0, 100)); const tail = rowsOf(name); w2.prov.destroy(); await waitUnloaded(hp, name)
    after.tailRows = tail.rows; after.tailBytes = tail.bytes
    after.hocuspocusOpenSnapshotPlusTail = await coldOpen(name)
    after.directLoadSnapshotPlusTailMs = timeIt(() => loadFromStorage(db, name))
    const live2 = new Y.Doc(); const p2 = await connect(url, name, live2)
    after.correct_snapshotPlusTailEqualsLive = sameDigest(digest(loadFromStorage(db, name), BOARD_MAPS), digest(live2, BOARD_MAPS))
    p2.destroy(); await waitUnloaded(hp, name)
    L['compact_' + mode] = after
  }
  delete L.liveDoc
  res.load = L
  console.error(`N=${N} load experiment done`)
}

// ---------- seeding for session variants ----------
const KINDS = ['full', 'pg', 'lc', 'lb', 'ld', 'lt', 'none']
const nameOf = (k, p) => (k === 'pg' ? `pg:${N}:${p}` : `${k}:s${N}`)
const board = buildBoard('A', base, 5, []).docs[0]
const pages = buildBoard('C', base, 20, []).docs
for (const k of KINDS) {
  if (k === 'pg') pages.forEach((d, p) => store.q.putDoc.run(nameOf(k, p), Y.encodeStateAsUpdate(d)))
  else if (k === 'full') store.q.putDoc.run(nameOf(k), Y.encodeStateAsUpdate(board))
  else if (k !== 'none') store.q.putSnap.run(nameOf(k), Y.encodeStateAsUpdate(board))
}
store.compactMode = 'doc'

// ---------- per-save cost for one added stroke (steady state, like the sync spike) ----------
for (const k of ['full', 'pg', 'ld', 'lt']) {
  const name = nameOf(k, 0), doc = new Y.Doc(), prov = await connect(url, name, doc)
  const map = doc.getMap(k === 'pg' ? 'strokes' : 'strokes:0'), recs = [], upd = []
  doc.on('update', (u, o) => { if (o === 'me') upd.push(u.length) })
  for (let i = 0; i < 6; i++) {
    const n0 = store.writes.length
    doc.transact(() => map.set('single' + i, extra[1900 + i].packed), 'me')
    await waitFor(() => writesFor([name], n0).length > 0, 10000)
    await sleep(20)
    recs.push(writesFor([name], n0).reduce((a, w) => ({ bytes: a.bytes + w.bytes, disk: a.disk + w.disk, ms: a.ms + w.ms + (w.encodeMs || 0) }), { bytes: 0, disk: 0, ms: 0 }))
  }
  recs.shift(); upd.shift()
  res.singleSave.push({ kind: k, updateBytes: median(upd), bytesWrittenPerSave: median(recs.map((r) => r.bytes)), walBytesPerSave: median(recs.map((r) => r.disk)), saveMs: r1(median(recs.map((r) => r.ms))) })
  prov.destroy(); await waitUnloaded(hp, name)
}
console.error(`N=${N} single-save done`)

// ---------- experiment S: a student writing 2k strokes, ~10% erase/undo, two sessions with disconnect/reconnect ----------
async function runVariant(kind) {
  const rng = mulberry32(1234)
  const names = kind === 'pg' ? Array.from({ length: 20 }, (_, p) => nameOf(kind, p)) : [nameOf(kind)]
  const v = { kind, sessions: [] }
  const w0 = store.writes.length, c0 = store.compactions.length
  const pingAll = []
  for (const si of [1, 2]) {
    const targets = kind === 'pg' ? [names[2 * si - 2], names[2 * si - 1]] : names
    const items = []
    for (const n of targets) {
      const doc = new Y.Doc(), prov = await connect(url, n, doc)
      const maps = kind === 'pg' ? [doc.getMap('strokes')] : BOARD_MAPS.map((m) => doc.getMap(m))
      const um = new Y.UndoManager(maps, { trackedOrigins: new Set(['me']), captureTimeout: 0 })
      let sent = 0
      doc.on('update', (u, o) => { if (o !== prov) sent++ })
      items.push({ n, doc, prov, maps, um, get sent() { return sent }, seen0: store.seen.get(n) || 0 })
    }
    const ping = await startPing(url, `${kind}${si}`); await sleep(100)
    const sw0 = store.writes.length, sc0 = store.compactions.length
    const series = []
    const t0 = performance.now()
    let erases = 0, undos = 0
    for (let j = 0; j < 1000; j++) {
      const sidx = (si - 1) * 1000 + j
      const it = kind === 'pg' ? items[Math.floor(j / 500)] : items[0]
      const map = kind === 'pg' ? it.maps[0] : it.maps[Math.floor(sidx / 200) % 5]
      if (j > 0 && rng() < 0.1) {
        if (rng() < 0.5) { const ks = [...map.keys()]; if (ks.length) { it.doc.transact(() => map.delete(ks[Math.floor(rng() * ks.length)]), 'me'); erases++ } }
        else if (it.um.undoStack.length) { it.um.undo(); undos++ }
      }
      it.doc.transact(() => map.set(extra[sidx].id, extra[sidx].packed), 'me')
      if (kind !== 'none' && kind !== 'full' && kind !== 'pg' && j % 100 === 99) { const r = rowsOf(names[0]); series.push({ afterStrokes: j + 1, logRows: r.rows, logBytes: r.bytes }) }
      await sleep(PACE_MS)
    }
    const sessionMs = performance.now() - t0
    await waitFor(() => items.every((it) => (store.seen.get(it.n) || 0) - it.seen0 >= it.sent), 60000)
    await ping.stop()
    const live = items.map((it) => it.doc)
    items.forEach((it) => it.prov.destroy())
    for (const it of items) await waitUnloaded(hp, it.n)
    const myWrites = writesFor(names, sw0), myComp = store.compactions.slice(sc0).filter((c) => names.includes(c.name))
    const saveW = myWrites.filter((w) => w.op !== 'compact')
    const compW = myWrites.filter((w) => w.op === 'compact')
    // correctness: reload from storage only and compare with the live client doc(s)
    let correct = true, detail = []
    if (kind !== 'none') items.forEach((it, i) => {
      const mapsN = kind === 'pg' ? ['strokes'] : BOARD_MAPS
      const a = digest(loadFromStorage(db, it.n), mapsN), b = digest(it.doc, mapsN)
      const ok = sameDigest(a, b); correct = correct && ok; detail.push({ doc: it.n, ok, strokesStored: a.strokes, strokesLive: b.strokes })
    })
    const ks = kind === 'pg' ? targets : names
    const left = ks.reduce((a, n) => { const r = rowsOf(n); return { rows: a.rows + r.rows, bytes: a.bytes + r.bytes } }, { rows: 0, bytes: 0 })
    const pa = ping.samples.map((s) => s.lat), pg = ping.samples.map((s) => s.gap)
    const compWin = myComp.flatMap((c) => ping.samples.filter((s) => s.at >= c.t0 - 5 && s.at <= c.t1 + 60).map((s) => s.gap))
    v.sessions.push({
      session: si, durationMs: Math.round(sessionMs), erases, undos, strokesAdded: 1000,
      saves: saveW.length, bytesWritten: saveW.reduce((a, w) => a + w.bytes, 0), walBytesWritten: saveW.reduce((a, w) => a + w.disk, 0),
      bytesPerSaveMedian: Math.round(median(saveW.map((w) => w.bytes)) || 0),
      walBytesPerSaveMedian: Math.round(median(saveW.map((w) => w.disk)) || 0),
      writeMs: stat(saveW.map((w) => w.ms + (w.encodeMs || 0))),
      compactions: myComp.map((c) => ({ trigger: c.trigger, ms: r1(c.ms), rows: c.rowsMerged, snapBytes: c.snapBytes })),
      compactionBytesWritten: compW.reduce((a, w) => a + w.bytes, 0), compactionWalBytes: compW.reduce((a, w) => a + w.disk, 0),
      logLeftAfterSession: left, growthSeries: series,
      pingMs: stat(pa), pingGapMs: stat(pg), pingMaxDuringCompactionMs: compWin.length ? r1(Math.max(...compWin)) : null,
      correct_reloadFromStorageEqualsLive: kind === 'none' ? 'n/a' : correct, correctDetail: detail.slice(0, 3),
    })
  }
  const all = writesFor(names, w0)
  v.totalBytesWritten = all.reduce((a, w) => a + w.bytes, 0)
  v.totalBytesPerStroke = Math.round(v.totalBytesWritten / 2000)
  v.totalWalBytes = all.reduce((a, w) => a + w.disk, 0)
  v.totalWalBytesPerStroke = Math.round(v.totalWalBytes / 2000)
  v.loadsServerMs = store.loads.filter((l) => names.includes(l.name)).slice(-4).map((l) => ({ ms: r1(l.ms), rows: l.rows }))
  return v
}
for (const k of KINDS) { res.sessions.push(await runVariant(k)); console.error(`N=${N} session variant ${k} done`) }
res.hooks = store.hookInfo.filter((h) => h.documentName.startsWith('ld:')).slice(0, 4)

await sleep(200)
await server.destroy(); db.close()
fs.rmSync(dir, { recursive: true, force: true })
console.log('RESULT ' + JSON.stringify(res))
process.exit(0)
