// PROTOTYPE (throwaway): real Hocuspocus over a local WebSocket (server on port 0, loopback, destroyed at the end).
// Measures fresh-client sync time and the per-save cost of the whole-doc rewrite, and shows subdocs do not sync.
import * as Y from 'yjs'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import WebSocket from 'ws'
import { DatabaseSync } from 'node:sqlite'
import { Server } from '@hocuspocus/server'
import { HocuspocusProvider, HocuspocusProviderWebsocket } from '@hocuspocus/provider'
import { genStrokes, buildBoard, median, newDoc, pack, genStroke, mulberry32, pageOf } from './lib.js'

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'aq16-hp-'))
const db = new DatabaseSync(path.join(tmp, 'PROTOTYPE-wipe-me.sqlite'))
db.exec('CREATE TABLE documents (name TEXT PRIMARY KEY, data BLOB)')
const put = db.prepare('INSERT INTO documents(name,data) VALUES (?,?) ON CONFLICT(name) DO UPDATE SET data=excluded.data')
const get = db.prepare('SELECT data FROM documents WHERE name=?')

const stores = [] // {name, encodeMs, writeMs, bytes}
const loads = []
const waiters = []
const ext = {
  extensionName: 'PrototypeSqlite',
  async onLoadDocument({ document, documentName }) {
    const t = performance.now()
    const row = get.get(documentName)
    if (row) Y.applyUpdate(document, new Uint8Array(row.data))
    loads.push({ name: documentName, ms: performance.now() - t })
  },
  async onStoreDocument({ document, documentName }) {
    const t0 = performance.now()
    const state = Y.encodeStateAsUpdate(document) // the whole doc, every save
    const t1 = performance.now()
    put.run(documentName, state)
    const t2 = performance.now()
    const rec = { name: documentName, encodeMs: t1 - t0, writeMs: t2 - t1, bytes: state.length }
    stores.push(rec)
    for (const w of waiters.splice(0)) w(rec)
  },
}
const nextStore = (name) => new Promise((res) => { const w = (rec) => (rec.name === name ? res(rec) : waiters.push(w)); waiters.push(w) })

const server = new Server({ address: '127.0.0.1', port: 0, quiet: true, stopOnSignals: false, debounce: 20, maxDebounce: 20, extensions: [ext] })
await server.listen(0)
const url = server.webSocketURL

function connect(name, document, wsProv) {
  return new Promise((resolve) => {
    const cfg = { name, document, onSynced: () => resolve(p) }
    if (wsProv) cfg.websocketProvider = wsProv; else { cfg.url = url; cfg.WebSocketPolyfill = WebSocket }
    const p = new HocuspocusProvider(cfg)
    if (wsProv) p.attach()
  })
}
const seed = (name, doc) => put.run(name, Y.encodeStateAsUpdate(doc))
const countStrokes = (doc) => [...doc.share.keys()].reduce((n, k) => n + doc.getMap(k).size, 0)
const REPS = +(process.env.REPS || 7)
const log = (...a) => process.env.DBG && console.error(...a)

export async function runHocuspocus(sizes = [1000, 3000, 5000, 10000]) {
  const out = { sync: [], save: [], subdoc: null, url: 'ws://127.0.0.1:<ephemeral>' }
  for (const N of sizes) {
    const strokes = genStrokes(N)
    // seeds: A (one doc, 5 page maps), C with 5 pages and with 20 pages
    seed(`A-${N}`, buildBoard('A', strokes, 5, []).docs[0])
    for (const P of [5, 20]) buildBoard('C', strokes, P, []).docs.forEach((d, p) => seed(`C-${N}-${P}-${p}`, d))
    const rows = [
      { layout: 'A', P: 5, what: 'whole board (one doc)', names: [`A-${N}`] },
      { layout: 'C', P: 5, what: 'one page of 5 (one doc)', names: [`C-${N}-5-0`] },
      { layout: 'C', P: 20, what: 'one page of 20 (one doc)', names: [`C-${N}-20-0`] },
      { layout: 'C', P: 20, what: 'all 20 pages (20 docs, one socket)', names: Array.from({ length: 20 }, (_, p) => `C-${N}-20-${p}`) },
    ]
    for (const r of rows) {
      const ts = [], serverLoad = []
      for (let i = 0; i < REPS + 1; i++) {
        log("rep", r.what, i); const l0 = loads.length
        const t = performance.now()
        let provs, docs
        if (r.names.length === 1) { docs = [new Y.Doc()]; provs = [await connect(r.names[0], docs[0])] }
        else {
          const ws = new HocuspocusProviderWebsocket({ url, WebSocketPolyfill: WebSocket })
          docs = r.names.map(() => new Y.Doc())
          provs = await Promise.all(r.names.map((n, k) => connect(n, docs[k], ws)))
        }
        ts.push(performance.now() - t)
        serverLoad.push(loads.slice(l0).reduce((a, b) => a + b.ms, 0))
        const got = docs.reduce((n, d) => n + countStrokes(d), 0)
        if (i === 0) r.strokesReceived = got
        provs.forEach((p) => p.destroy())
        await sleep(120) // let the server unload (and store) so every rep is a fresh server-side load too
      }
      ts.shift(); serverLoad.shift()
      out.sync.push({ N, layout: r.layout, P: r.P, what: r.what, ms: median(ts), serverLoadMs: median(serverLoad), strokesReceived: r.strokesReceived })
    }
    // per-save cost: one stroke added to a loaded doc, wait for the server store hook
    const saveRows = [
      { layout: 'A', P: 5, what: 'whole board (one doc)', name: `A-${N}`, map: (d) => d.getMap('strokes:0') },
      { layout: 'C', P: 5, what: 'one page of 5', name: `C-${N}-5-0`, map: (d) => d.getMap('strokes') },
      { layout: 'C', P: 20, what: 'one page of 20', name: `C-${N}-20-0`, map: (d) => d.getMap('strokes') },
    ]
    for (const r of saveRows) {
      await sleep(150)
      const doc = new Y.Doc(); const prov = await connect(r.name, doc)
      await sleep(100)
      const rng = mulberry32(N + 7), recs = [], e2e = [], upd = []
      doc.on('update', (u, o) => { if (o === 'mine') upd.push(u.length) })
      for (let i = 0; i < 11; i++) {
        const sp = nextStore(r.name), t = performance.now()
        doc.transact(() => r.map(doc).set('new' + i, pack(genStroke(rng))), 'mine')
        const rec = await sp
        recs.push(rec); e2e.push(performance.now() - t)
      }
      recs.shift(); e2e.shift(); upd.shift()
      out.save.push({ N, layout: r.layout, P: r.P, what: r.what, docBytesWritten: median(recs.map((x) => x.bytes)), updateBytes: median(upd), encodeMs: median(recs.map((x) => x.encodeMs)), writeMs: median(recs.map((x) => x.writeMs)), onStoreMs: median(recs.map((x) => x.encodeMs + x.writeMs)), strokeToStoredMs: median(e2e) })
      prov.destroy()
    }
    console.error(`hocuspocus N=${N} done`)
  }

  // ---- layout B on Hocuspocus: do subdoc contents sync? ----
  {
    const name = 'B-subdoc-test'
    const d1 = new Y.Doc(); const p1 = await connect(name, d1)
    const sd = new Y.Doc({ guid: 'page-0' }); d1.getMap('pages').set('page-0', sd)
    const strokes = genStrokes(100, 5)
    strokes.forEach((s) => sd.transact(() => sd.getMap('strokes').set(s.id, s.packed)))
    const rec = await nextStore(name)
    await sleep(200)
    const d2 = new Y.Doc(); const p2 = await connect(name, d2)
    await sleep(300)
    const sd2 = d2.getMap('pages').get('page-0')
    const before = sd2 ? sd2.getMap('strokes').size : null
    if (sd2) sd2.load()
    await sleep(500)
    const afterLoad = sd2 ? sd2.getMap('strokes').size : null
    const storedRoot = rec.bytes
    const subBytes = Y.encodeStateAsUpdate(sd).length
    // workaround: give the subdoc its own provider (document name = guid) => that is layout C with an index doc
    const sp1 = await connect('page-0-as-own-doc', sd)
    await sleep(100)
    const sp2 = await connect('page-0-as-own-doc', sd2)
    await sleep(300)
    const viaOwnProvider = sd2.getMap('strokes').size
    out.subdoc = { strokesWrittenToSubdoc: 100, client2SeesSubdocInRootMap: !!sd2, client2SubdocStrokes: before, client2SubdocStrokesAfterLoad: afterLoad, serverStoredRootDocBytes: storedRoot, subdocBytesNeverSentToServer: subBytes, client2SubdocStrokesWithItsOwnProviderPerSubdoc: viaOwnProvider }
    ;[p1, p2, sp1, sp2].forEach((p) => p.destroy())
  }
  return out
}

export async function shutdown() {
  await sleep(200)
  await server.destroy()
  db.close()
  fs.rmSync(tmp, { recursive: true, force: true })
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const r = await runHocuspocus(process.argv[2] ? process.argv.slice(2).map(Number) : [1000])
  await shutdown()
  console.log(JSON.stringify(r, null, 1))
  process.exit(0)
}
