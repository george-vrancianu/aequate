// PROTOTYPE (throwaway): SQLite stores for Hocuspocus, written as plain extensions (no mocking).
// Doc-name prefix picks the store kind:
//   full:  stock Database-extension style, whole Y.encodeStateAsUpdate rewritten on onStoreDocument
//   pg:    same full rewrite, but the board is split one doc per page (just a naming convention)
//   lc:    update log (one row per onChange update), compact when rows >= COUNT
//   lb:    update log, compact when log bytes >= BYTES
//   ld:    update log, compact only when the last client disconnects
//   ln:    update log, never compact (replay baseline)
//   lt:    log, but batched: onChange queues, onStoreDocument appends ONE merged row (debounced); compact on disconnect
//   none:  no persistence
import * as Y from 'yjs'
import { DatabaseSync } from 'node:sqlite'
import crypto from 'node:crypto'

export const COUNT = 500
export const BYTES = 512 * 1024
const kindOf = (name) => name.split(':')[0]

export function openDb(file) {
  const db = new DatabaseSync(file)
  db.exec('PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;')
  db.exec(`CREATE TABLE IF NOT EXISTS documents (name TEXT PRIMARY KEY, data BLOB);
           CREATE TABLE IF NOT EXISTS snapshots (doc TEXT PRIMARY KEY, data BLOB);
           CREATE TABLE IF NOT EXISTS updates (id INTEGER PRIMARY KEY AUTOINCREMENT, doc TEXT NOT NULL, data BLOB NOT NULL);
           CREATE INDEX IF NOT EXISTS updates_doc ON updates(doc, id);`)
  return db
}

// ---- read side, usable without a server (used for "reload from storage only" checks) ----
export function loadFromStorage(db, name, { mode = 'replay' } = {}) {
  const doc = new Y.Doc()
  const kind = kindOf(name)
  if (kind === 'full' || kind === 'pg') {
    const r = db.prepare('SELECT data FROM documents WHERE name=?').get(name)
    if (r) Y.applyUpdate(doc, new Uint8Array(r.data))
    return doc
  }
  const snap = db.prepare('SELECT data FROM snapshots WHERE doc=?').get(name)
  const rows = db.prepare('SELECT data FROM updates WHERE doc=? ORDER BY id').all(name)
  if (mode === 'merge') {
    const parts = rows.map((r) => new Uint8Array(r.data))
    if (snap) parts.unshift(new Uint8Array(snap.data))
    if (parts.length) Y.applyUpdate(doc, Y.mergeUpdates(parts))
    return doc
  }
  if (snap) Y.applyUpdate(doc, new Uint8Array(snap.data))
  for (const r of rows) Y.applyUpdate(doc, new Uint8Array(r.data))
  return doc
}

// canonical content digest of the stroke maps (key + packed bytes), plus the state vector
export function digest(doc, mapNames) {
  const h = crypto.createHash('sha1')
  let strokes = 0
  for (const n of mapNames) {
    const m = doc.getMap(n)
    h.update('#' + n)
    for (const k of [...m.keys()].sort()) { h.update(k); h.update(m.get(k)); strokes++ }
  }
  return { strokes, content: h.digest('hex').slice(0, 12), sv: Buffer.from(Y.encodeStateVector(doc)).toString('hex') }
}
export const sameDigest = (a, b) => a.sv === b.sv && a.content === b.content && a.strokes === b.strokes

// ---- the extension ----
export function makeStore(db, opts = {}) {
  const q = {
    putDoc: db.prepare('INSERT INTO documents(name,data) VALUES (?,?) ON CONFLICT(name) DO UPDATE SET data=excluded.data'),
    getDoc: db.prepare('SELECT data FROM documents WHERE name=?'),
    getSnap: db.prepare('SELECT data FROM snapshots WHERE doc=?'),
    putSnap: db.prepare('INSERT INTO snapshots(doc,data) VALUES (?,?) ON CONFLICT(doc) DO UPDATE SET data=excluded.data'),
    tail: db.prepare('SELECT id,data FROM updates WHERE doc=? ORDER BY id'),
    ins: db.prepare('INSERT INTO updates(doc,data) VALUES (?,?)'),
    del: db.prepare('DELETE FROM updates WHERE doc=? AND id<=?'),
    maxId: db.prepare('SELECT COALESCE(MAX(id),0) AS m FROM updates WHERE doc=?'),
  }
  const s = {
    writes: [],   // {name, op:'save'|'append'|'compact', bytes, ms}
    loads: [],    // {name, ms, rows}
    compactions: [], // {name, trigger, t0, t1, ms, rowsMerged, snapBytes, mode}
    seen: new Map(), // docName -> number of onChange calls
    hookInfo: [],    // observations for the report
    compactMode: opts.compactMode || 'doc', // 'doc' = encodeStateAsUpdate(live doc); 'merge' = Y.mergeUpdates(snapshot + rows)
    crashBeforeCommit: false,
    q,
  }
  const st = new Map() // per doc state for log kinds: {rows, bytes, compacting, queue}
  const state = (name) => { let x = st.get(name); if (!x) st.set(name, (x = { rows: 0, bytes: 0, compacting: false, queue: [] })); return x }

  function compact(name, trigger, document) {
    const x = state(name)
    const t0 = performance.now()
    const wall0 = Date.now()
    db.exec('BEGIN IMMEDIATE')
    const maxId = q.maxId.get(name).m
    let merged, n = 0
    if (s.compactMode === 'merge') {
      const parts = []
      const snap = q.getSnap.get(name); if (snap) parts.push(new Uint8Array(snap.data))
      for (const r of q.tail.all(name)) { if (r.id <= maxId) { parts.push(new Uint8Array(r.data)); n++ } }
      merged = Y.mergeUpdates(parts)
    } else {
      n = x.rows
      merged = Y.encodeStateAsUpdate(document) // live doc already contains every row <= maxId
    }
    q.putSnap.run(name, merged)
    q.del.run(name, maxId)
    if (s.crashBeforeCommit) process.kill(process.pid, 'SIGKILL') // simulated crash inside the compaction transaction
    db.exec('COMMIT')
    const t1 = performance.now()
    x.rows = 0; x.bytes = 0
    s.compactions.push({ name, trigger, t0: performance.now() - (t1 - t0), t1, wall0, ms: t1 - t0, rowsMerged: n, snapBytes: merged.length, mode: s.compactMode })
    s.writes.push({ name, op: 'compact', bytes: merged.length, ms: t1 - t0 })
  }
  s.compact = compact

  const maybeCompact = (name, document) => {
    const x = state(name), k = kindOf(name)
    let trig = null
    if (k === 'lc' && x.rows >= COUNT) trig = 'count'
    if (k === 'lb' && x.bytes >= BYTES) trig = 'bytes'
    if (trig && !x.compacting) {
      x.compacting = true
      setImmediate(() => { try { compact(name, trig, document) } finally { x.compacting = false } })
    }
  }

  s.extension = {
    extensionName: 'PrototypeSqliteStores',
    async onLoadDocument({ document, documentName }) {
      const t = performance.now(); const k = kindOf(documentName); let rows = 0
      if (k === 'full' || k === 'pg') {
        const r = q.getDoc.get(documentName); if (r) Y.applyUpdate(document, new Uint8Array(r.data))
      } else if (k !== 'none') {
        const snap = q.getSnap.get(documentName)
        if (snap) Y.applyUpdate(document, new Uint8Array(snap.data))
        const x = state(documentName); x.rows = 0; x.bytes = 0
        for (const r of q.tail.all(documentName)) { Y.applyUpdate(document, new Uint8Array(r.data)); rows++; x.rows++; x.bytes += r.data.length }
      }
      s.loads.push({ name: documentName, ms: performance.now() - t, rows })
    },
    // onChange: called from Document.onUpdate -> Hocuspocus.handleDocumentUpdate (not awaited), payload.update = the v1 update bytes
    async onChange({ document, documentName, update }) {
      s.seen.set(documentName, (s.seen.get(documentName) || 0) + 1)
      const k = kindOf(documentName)
      if (k === 'lt') { state(documentName).queue.push(update); return }
      if (k !== 'lc' && k !== 'lb' && k !== 'ld' && k !== 'ln') return
      const t = performance.now()
      q.ins.run(documentName, update)
      s.writes.push({ name: documentName, op: 'append', bytes: update.length, ms: performance.now() - t })
      const x = state(documentName); x.rows++; x.bytes += update.length
      maybeCompact(documentName, document)
    },
    async onStoreDocument({ document, documentName }) {
      const k = kindOf(documentName)
      if (k === 'full' || k === 'pg') {
        const t0 = performance.now()
        const data = Y.encodeStateAsUpdate(document)
        const t1 = performance.now()
        q.putDoc.run(documentName, data)
        const t2 = performance.now()
        s.writes.push({ name: documentName, op: 'save', bytes: data.length, ms: t2 - t1, encodeMs: t1 - t0 })
      } else if (k === 'lt') {
        const x = state(documentName)
        if (!x.queue.length) return
        const batch = x.queue.splice(0)
        const merged = Y.mergeUpdates(batch)
        const t = performance.now()
        q.ins.run(documentName, merged)
        s.writes.push({ name: documentName, op: 'append', bytes: merged.length, ms: performance.now() - t, batched: batch.length })
        x.rows++; x.bytes += merged.length
      }
    },
    async onDisconnect({ document, documentName, clientsCount }) {
      s.hookInfo.push({ hook: 'onDisconnect', documentName, clientsCount })
      const k = kindOf(documentName)
      if ((k === 'ld' || k === 'lt') && clientsCount === 0) {
        // for lt, flush the queue first so the snapshot is consistent with the log
        if (k === 'lt') await s.extension.onStoreDocument({ document, documentName })
        compact(documentName, 'disconnect', document)
      }
    },
  }
  return s
}
