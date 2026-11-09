// PROTOTYPE (throwaway): crash tests. A child process runs a real Hocuspocus server + client, writes strokes, then SIGKILLs itself
// (no unload, no flush, no compaction). The parent reopens the sqlite file and reloads from storage only.
import * as Y from 'yjs'
import fs from 'node:fs'
import path from 'node:path'
import { spawnSync } from 'node:child_process'
import { genStrokes, buildBoard, mulberry32 } from './lib.js'
import { openDb, loadFromStorage, digest, sameDigest } from './store.js'
import { startServer, connect, scratchDir, waitFor, sleep } from './common.js'

const BOARD_MAPS = [0, 1, 2, 3, 4].map((p) => 'strokes:' + p)
const BASE = 1000, ADD = 600
const here = path.dirname(new URL(import.meta.url).pathname)

if (process.argv[2] === '--child') {
  const [, , , mode, dir, expectedFile] = process.argv
  const kind = { 'log-per-update': 'ld', 'log-compacted-midway': 'lc', 'log-batched': 'lt', 'full-rewrite': 'full', 'log-kill-inside-compaction': 'ld' }[mode]
  const name = `${kind}:crash`
  const S = await startServer(dir)
  const strokes = genStrokes(BASE + ADD)
  const board = buildBoard('A', strokes.slice(0, BASE), 5, []).docs[0]
  if (kind === 'full') S.store.q.putDoc.run(name, Y.encodeStateAsUpdate(board)); else S.store.q.putSnap.run(name, Y.encodeStateAsUpdate(board))
  if (mode === 'log-kill-inside-compaction') S.store.crashBeforeCommit = true
  const doc = new Y.Doc(), prov = await connect(S.url, name, doc)
  const maps = BOARD_MAPS.map((m) => doc.getMap(m)), rng = mulberry32(5)
  let sent = 0
  doc.on('update', (u, o) => { if (o !== prov) sent++ })
  for (let i = 0; i < ADD; i++) {
    const m = maps[i % 5]
    if (rng() < 0.1) { const ks = [...m.keys()]; doc.transact(() => m.delete(ks[Math.floor(rng() * ks.length)]), 'me') }
    doc.transact(() => m.set(strokes[BASE + i].id, strokes[BASE + i].packed), 'me')
    await sleep(2)
  }
  await waitFor(() => (S.store.seen.get(name) || 0) >= sent, 30000)
  fs.writeFileSync(expectedFile, JSON.stringify(digest(doc, BOARD_MAPS)))
  if (mode === 'log-kill-inside-compaction') { prov.destroy(); await sleep(2000); process.exit(3) } // compaction on disconnect SIGKILLs before COMMIT
  process.kill(process.pid, 'SIGKILL')
}

const dir = scratchDir()
const out = []
for (const mode of ['log-per-update', 'log-compacted-midway', 'log-batched', 'full-rewrite', 'log-kill-inside-compaction']) {
  const d = path.join(dir, mode); fs.mkdirSync(d)
  const ef = path.join(d, 'expected.json')
  const r = spawnSync('node', ['crash.js', '--child', mode, d, ef], { cwd: here, encoding: 'utf8' })
  const expected = JSON.parse(fs.readFileSync(ef, 'utf8'))
  const db = openDb(path.join(d, 'PROTOTYPE-wipe-me.sqlite'))
  const kind = { 'log-per-update': 'ld', 'log-compacted-midway': 'lc', 'log-batched': 'lt', 'full-rewrite': 'full', 'log-kill-inside-compaction': 'ld' }[mode]
  const name = `${kind}:crash`
  const got = digest(loadFromStorage(db, name), BOARD_MAPS)
  const rows = db.prepare('SELECT COUNT(*) c FROM updates WHERE doc=?').get(name).c
  const snap = db.prepare('SELECT LENGTH(data) l FROM snapshots WHERE doc=?').get(name)
  db.close()
  out.push({ mode, childSignal: r.signal, expectedStrokes: expected.strokes, recoveredStrokes: got.strokes, logRowsLeft: rows, snapshotBytes: snap?.l ?? null, svEqual: got.sv === expected.sv, contentEqual: got.content === expected.content, result: sameDigest(got, expected) ? 'PASS' : 'FAIL' })
}
fs.rmSync(dir, { recursive: true, force: true })
console.log('RESULT ' + JSON.stringify(out))
process.exit(0)
