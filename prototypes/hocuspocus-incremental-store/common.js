// PROTOTYPE (throwaway): shared bench plumbing (server start, clients, ping).
import * as Y from 'yjs'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import WebSocket from 'ws'
import { Server } from '@hocuspocus/server'
import { HocuspocusProvider } from '@hocuspocus/provider'
import { openDb, makeStore } from './store.js'

export const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
export const DEBOUNCE = 100, MAX_DEBOUNCE = 500, PACE_MS = 4

export async function waitFor(cond, timeout = 30000, step = 5) {
  const t = Date.now()
  while (!cond()) { if (Date.now() - t > timeout) throw new Error('waitFor timeout'); await sleep(step) }
}

export function scratchDir() {
  // not /tmp (tmpfs here): keep the sqlite file on the real disk next to the prototype, gitignored
  const base = path.join(path.dirname(new URL(import.meta.url).pathname), '.tmp-wipe-me')
  fs.mkdirSync(base, { recursive: true })
  return fs.mkdtempSync(path.join(base, 'run-'))
}

export async function startServer(dir, { compactMode = 'doc', debounce = DEBOUNCE, maxDebounce = MAX_DEBOUNCE } = {}) {
  const dbFile = path.join(dir, 'PROTOTYPE-wipe-me.sqlite')
  const db = openDb(dbFile)
  const store = makeStore(db, { compactMode })
  const server = new Server({ address: '127.0.0.1', port: 0, quiet: true, stopOnSignals: false, debounce, maxDebounce, extensions: [store.extension] })
  await server.listen(0)
  return { server, db, store, url: server.webSocketURL, dbFile, hp: server.hocuspocus }
}

export function connect(url, name, document) {
  return new Promise((resolve) => {
    const p = new HocuspocusProvider({ url, WebSocketPolyfill: WebSocket, name, document, onSynced: () => resolve(p) })
  })
}

export const waitUnloaded = (hp, name) => waitFor(() => !hp.documents.has(name), 30000, 5)

// round-trip ping through the real server on a tiny doc: client B writes a timestamp every 5 ms, client C observes it
export async function startPing(url, tag = 'x') {
  const name = 'none:ping-' + tag
  const dB = new Y.Doc(), dC = new Y.Doc()
  const pB = await connect(url, name, dB), pC = await connect(url, name, dC)
  const samples = [] // {at, lat (RTT), gap (time since previous arrival: shows event-loop stalls)}
  let last = 0
  dC.getMap('p').observe(() => { const t = dC.getMap('p').get('t'); const now = performance.now(); samples.push({ at: now, lat: now - t, gap: last ? now - last : 0 }); last = now })
  let stopped = false
  ;(async () => { while (!stopped) { dB.getMap('p').set('t', performance.now()); await sleep(5) } })()
  return { samples, async stop() { stopped = true; await sleep(30); pB.destroy(); pC.destroy() } }
}

export const stat = (a) => {
  if (!a.length) return null
  const s = [...a].sort((x, y) => x - y), q = (p) => s[Math.min(s.length - 1, Math.floor(p * s.length))]
  return { n: s.length, p50: q(0.5), p95: q(0.95), p99: q(0.99), max: s[s.length - 1], sum: s.reduce((x, y) => x + y, 0) }
}
