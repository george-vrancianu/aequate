// PROTOTYPE (throwaway): in-browser measurements against the tablet server. No framework.
import * as Y from 'yjs'
import { HocuspocusProvider, HocuspocusProviderWebsocket } from '@hocuspocus/provider'
import { unpack, median, pct } from '../lib.js'

const PAGES = 20
const SIZES = [1000, 3000, 5000, 10000]
const REPS = 3
const $ = (id) => document.getElementById(id)
const wsUrl = (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/collab'
const docName = (size, layout, p) => (layout === 'board' ? `t-${size}-board` : `t-${size}-page-${p}`)
const mapOf = (doc, layout, p) => doc.getMap(layout === 'board' ? 'strokes:' + p : 'strokes')
const now = () => performance.now()
const hasMem = !!(performance && performance.memory && performance.memory.usedJSHeapSize)
// performance.memory is bucketed/stale unless Chromium runs with --enable-precise-memory-info (only the desktop verify run does; add ?precise to the URL to declare that). On a tablet it is not.
const preciseMemory = new URLSearchParams(location.search).has('precise')
const heapMB = () => (hasMem ? +(performance.memory.usedJSHeapSize / 1048576).toFixed(1) : null)
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const raf = () => new Promise((r) => requestAnimationFrame(() => r()))
const r1 = (x) => (x == null ? null : Math.round(x * 100) / 100)
const get = async (path) => { const r = await fetch(path, { cache: 'no-store' }); const j = await r.json(); if (!r.ok) throw new Error(j.error || r.status); return j }

let size = 1000, layout = 'board', busy = false
const results = []
const device = () => ({
  userAgent: navigator.userAgent, platform: navigator.platform, hardwareConcurrency: navigator.hardwareConcurrency ?? null,
  deviceMemoryGB: navigator.deviceMemory ?? null, screen: `${screen.width}x${screen.height}`, devicePixelRatio: window.devicePixelRatio,
  connection: navigator.connection ? { effectiveType: navigator.connection.effectiveType, downlink: navigator.connection.downlink, rtt: navigator.connection.rtt } : null,
  performanceMemoryAvailable: hasMem, preciseMemory: hasMem && preciseMemory, secureContext: window.isSecureContext, serverHost: location.host, when: new Date().toISOString(),
})
$('memnote').textContent = hasMem ? (preciseMemory ? 'JS heap: performance.memory is available (Chromium, precise-memory-info on).' : 'JS heap: performance.memory exists but is coarse (bucketed, can be stale) without --enable-precise-memory-info, so heap numbers are marked (coarse) and should not be used for sizing.') : 'JS heap: performance.memory does NOT exist in this browser (iOS Safari and Firefox), so heap numbers will be blank. Use "deviceMemoryGB"/the OS if you need memory.'

function log(s) { const el = $('log'); el.textContent += s + '\n'; el.scrollTop = el.scrollHeight }

// ---- open a board (one doc, or 20 page docs over one shared socket) and time until every doc is synced
async function openDocs(names, shared = true) {
  const t0 = now()
  const docs = names.map(() => new Y.Doc())
  const ws = new HocuspocusProviderWebsocket({ url: wsUrl })
  const provs = []
  await Promise.all(names.map((name, i) => new Promise((resolve, reject) => {
    const p = new HocuspocusProvider({ name, document: docs[i], websocketProvider: ws, onSynced: () => resolve(), onClose: () => {} })
    provs.push(p); p.attach()
    setTimeout(() => reject(new Error('sync timeout for ' + name)), 120000)
  })))
  return { ms: now() - t0, docs, provs, ws, close() { provs.forEach((p) => p.destroy()); ws.destroy(); docs.forEach((d) => d.destroy()) } }
}
const boardNames = (sz, lay) => (lay === 'board' ? [docName(sz, 'board')] : Array.from({ length: PAGES }, (_, p) => docName(sz, 'page', p)))

// ---- render: decode packed strokes and draw simple paths to the canvas. returns {strokes, decodeMs, drawMs, points}
function renderStrokes(entries) {
  const cv = $('cv'), ctx = cv.getContext('2d')
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, cv.width, cv.height)
  ctx.setTransform(cv.width / 2000, 0, 0, cv.height / 3000, 0, 0)
  ctx.lineWidth = 2; ctx.strokeStyle = '#123'; ctx.lineJoin = 'round'
  const t0 = now()
  const dec = entries.map((v) => unpack(v))
  const t1 = now()
  let pts = 0
  for (const s of dec) { ctx.beginPath(); ctx.moveTo(s.x[0], s.y[0]); for (let i = 1; i < s.x.length; i++) ctx.lineTo(s.x[i], s.y[i]); ctx.stroke(); pts += s.x.length }
  ctx.getImageData(0, 0, 1, 1) // force the draw to complete (GPU canvases are lazy)
  const t2 = now()
  return { strokes: dec.length, points: pts, decodeMs: r1(t1 - t0), drawMs: r1(t2 - t1), totalMs: r1(t2 - t0) }
}
const collect = (docs, lay, onlyPage0) => {
  const out = []
  if (lay === 'board') { for (let p = onlyPage0 ? 0 : 0; p < (onlyPage0 ? 1 : PAGES); p++) mapOf(docs[0], 'board', p).forEach((v) => out.push(v)) }
  else for (let d = 0; d < (onlyPage0 ? 1 : docs.length); d++) mapOf(docs[d], 'page', d).forEach((v) => out.push(v))
  return out
}
const docBytes = (docs) => docs.reduce((n, d) => n + Y.encodeStateAsUpdate(d).length, 0)

async function measure(sz, lay) {
  log(`--- measuring ${sz} strokes, layout ${lay === 'board' ? 'one doc per board' : 'one doc per page (20)'}`)
  const names = boardNames(sz, lay)
  const row = { size: sz, layout: lay, docs: names.length, reps: REPS }
  // network RTT to the server (HTTP)
  const rtts = []
  for (let i = 0; i < 8; i++) { const t = now(); await get('/ping'); rtts.push(now() - t) }
  row.httpRttMs = r1(median(rtts))
  // 1. sync + open the whole board, fresh docs each time
  const runs = []
  let heapBefore = heapMB()
  for (let i = 0; i < REPS; i++) {
    log(`sync whole board, run ${i + 1}/${REPS}`)
    const o = await openDocs(names)
    runs.push(o.ms)
    if (i < REPS - 1) { o.close(); await sleep(300) } else row._open = o
  }
  const open = row._open; delete row._open
  row.syncWholeBoardMs = { median: r1(median(runs)), runs: runs.map(r1) }
  row.docBytesEncoded = docBytes(open.docs)
  row.strokesLoaded = collect(open.docs, lay, false).length
  const heapAfterOpen = heapMB()
  // 2. open ONE page on its own (page layout: the page-0 doc; board layout: the same single doc, so equal to the above)
  const pr = []
  for (let i = 0; i < REPS; i++) {
    const o = await openDocs([lay === 'board' ? docName(sz, 'board') : docName(sz, 'page', 0)])
    pr.push(o.ms); o.close(); await sleep(200)
  }
  row.openOnePageMs = { median: r1(median(pr)), runs: pr.map(r1), note: lay === 'board' ? 'same doc as whole board (opening a page needs the whole board)' : 'page-0 doc only' }
  // 3. render
  await raf()
  const one = collect(open.docs, lay, true)
  const rp = []; for (let i = 0; i < REPS; i++) rp.push(renderStrokes(one))
  const rb = []; const all = collect(open.docs, lay, false); for (let i = 0; i < REPS; i++) rb.push(renderStrokes(all))
  const med = (arr, k) => r1(median(arr.map((x) => x[k])))
  row.renderPage = { strokes: rp[0].strokes, points: rp[0].points, decodeMs: med(rp, 'decodeMs'), drawMs: med(rp, 'drawMs'), totalMs: med(rp, 'totalMs') }
  row.renderWholeBoard = { strokes: rb[0].strokes, points: rb[0].points, decodeMs: med(rb, 'decodeMs'), drawMs: med(rb, 'drawMs'), totalMs: med(rb, 'totalMs') }
  const heapAfterRender = heapMB()
  // 4. remote stroke updates streamed by the server into page 0 of this board
  const applyMs = [], obsMs = []
  let remote = false, t0 = 0
  const target = open.docs[0], tmap = mapOf(target, lay, 0)
  target.on('beforeAllTransactions', () => { t0 = now() })
  target.on('afterTransaction', (tr) => { if (!tr.local) remote = true })
  target.on('afterAllTransactions', () => { if (remote) { applyMs.push(now() - t0); remote = false } })
  const cv = $('cv'), ctx = cv.getContext('2d')
  tmap.observe((ev) => {
    const t = now()
    ev.changes.keys.forEach((ch, key) => { if (ch.action === 'add') { const s = unpack(tmap.get(key)); ctx.beginPath(); ctx.moveTo(s.x[0], s.y[0]); for (let i = 1; i < s.x.length; i++) ctx.lineTo(s.x[i], s.y[i]); ctx.stroke() } })
    obsMs.push(now() - t)
  })
  log('stream 100 strokes from the server (30 ms apart)')
  const before = tmap.size
  await get(`/stream?size=${sz}&layout=${lay}&count=100&interval=30`)
  await sleep(600)
  const arrived = applyMs.length
  const k = (a) => ({ n: a.length, median: r1(median(a)), p95: r1(pct(a, 0.95)), max: r1(Math.max(...a)) })
  row.remoteStrokeApply = arrived ? { ...k(applyMs), note: 'ms per remote update inside Yjs: beforeAllTransactions to afterAllTransactions, includes the observer below' } : { n: 0 }
  row.remoteStrokeObserverDecodeDraw = obsMs.length ? { ...k(obsMs), note: 'part of the above: unpack one stroke and draw its path' } : { n: 0 }
  row.remoteStrokesNote = 'server sends 100 single-stroke adds, then one transaction deleting them again (so n is about 101)'
  row.heapMB = hasMem ? { preciseMemory, beforeOpen: heapBefore, afterOpen: heapAfterOpen, afterRender: heapAfterRender, afterStream: heapMB() } : null
  open.close()
  log(`done: sync ${row.syncWholeBoardMs.median} ms, one page ${row.openOnePageMs.median} ms, apply/stroke median ${row.remoteStrokeApply.median} ms, render whole ${row.renderWholeBoard.totalMs} ms`)
  return row
}

function renderTable() {
  const rows = results
  const h = ['size', 'layout', 'sync+open whole board ms', 'open one page ms', 'apply per remote stroke ms (med / p95 / max, n)', 'render page ms (n)', 'render whole board ms (n)', 'doc bytes', 'heap MB (open / render)']
  let s = '<table><tr>' + h.map((x) => '<th>' + x + '</th>').join('') + '</tr>'
  for (const r of rows) {
    s += '<tr>' + [r.size, r.layout, r.syncWholeBoardMs.median, r.openOnePageMs.median,
      r.remoteStrokeApply.n ? `${r.remoteStrokeApply.median} / ${r.remoteStrokeApply.p95} / ${r.remoteStrokeApply.max}, ${r.remoteStrokeApply.n}` : 'none arrived',
      `${r.renderPage.totalMs} (${r.renderPage.strokes})`, `${r.renderWholeBoard.totalMs} (${r.renderWholeBoard.strokes})`, r.docBytesEncoded,
      r.heapMB ? `${r.heapMB.afterOpen} / ${r.heapMB.afterRender}${r.heapMB.preciseMemory ? '' : ' (coarse)'}` : 'n/a'].map((x) => '<td>' + x + '</td>').join('') + '</tr>'
  }
  $('tbl').innerHTML = s + '</table>'
  $('json').value = JSON.stringify({ prototype: 'yjs-churn-and-tablet', device: device(), results }, null, 1)
}

async function seedSel(sz = size, lay = layout) { log(`seeding ${sz} strokes (${lay}) on the server...`); const r = await get(`/seed?size=${sz}&layout=${lay}`); log(r.already ? 'already seeded' : `seeded in ${r.ms} ms`) }
async function runSel(sz = size, lay = layout) { await seedSel(sz, lay); results.push(await measure(sz, lay)); renderTable() }
const guard = (fn) => async () => { if (busy) return; busy = true; document.querySelectorAll('button').forEach((b) => (b.disabled = true)); try { await fn() } catch (e) { log('ERROR: ' + (e.message || e)) } finally { busy = false; document.querySelectorAll('button').forEach((b) => (b.disabled = false)) } }

function toggles() {
  $('sizes').innerHTML = ''; $('layouts').innerHTML = ''
  SIZES.forEach((n) => { const b = document.createElement('button'); b.textContent = n / 1000 + 'k'; b.className = n === size ? 'on' : ''; b.onclick = () => { size = n; toggles() }; $('sizes').appendChild(b) })
  ;[['board', 'one doc per board'], ['page', 'one doc per page (20)']].forEach(([v, t]) => { const b = document.createElement('button'); b.textContent = t; b.className = v === layout ? 'on' : ''; b.onclick = () => { layout = v; toggles() }; $('layouts').appendChild(b) })
}
toggles()
$('seed').onclick = guard(() => seedSel())
$('run').onclick = guard(() => runSel())
$('all').onclick = guard(async () => { for (const n of SIZES) for (const l of ['board', 'page']) { await runSel(n, l); await sleep(500) } })
$('clear').onclick = () => { results.length = 0; $('tbl').innerHTML = ''; $('json').value = ''; $('log').textContent = '' }
$('copy').onclick = async () => {
  const ta = $('json'); ta.value = ta.value || JSON.stringify({ device: device(), results }, null, 1)
  let ok = false
  try { if (navigator.clipboard && window.isSecureContext) { await navigator.clipboard.writeText(ta.value); ok = true } } catch {}
  if (!ok) { ta.removeAttribute('readonly'); ta.focus(); ta.select(); ta.setSelectionRange(0, ta.value.length); try { ok = document.execCommand('copy') } catch {}; ta.setAttribute('readonly', '') }
  $('copystatus').textContent = ok ? 'copied' : 'clipboard blocked here: the JSON is selected in the box below, use the iPad Copy bubble'
}
window.__results = results // for the headless verification
window.__run = (sz, lay) => runSel(sz, lay)
log('ready. Server: ' + location.host)
