// PROTOTYPE (throwaway): per-user undo correctness with two simulated clients, per layout A/B/C.
// Updates are exchanged through manual queues so that edits really interleave/are concurrent.
import * as Y from 'yjs'
import { mulberry32 } from './lib.js'

const PAGES = 3
const bytes = (n) => new Uint8Array([n & 255, 1, 2, 3])

function stackCap(um, cap) {
  um.on('stack-item-added', ({ type }) => {
    const st = type === 'undo' ? um.undoStack : um.redoStack
    if (st.length > cap) st.splice(0, st.length - cap) // drop oldest entries
  })
}

// two clients + relays. returns {X, Y, flush(), deliverSome(rng)}
function setup(layout, cap) {
  const links = [] // {xq, yq, x, y}
  const link = (dx, dy) => {
    const l = { xq: [], yq: [], dx, dy }
    dx.on('update', (u, o) => { if (o !== 'remote') l.xq.push(u) })
    dy.on('update', (u, o) => { if (o !== 'remote') l.yq.push(u) })
    links.push(l)
    return l
  }
  const mk = (id, docs) => {
    const origin = 'user-' + id
    const c = { id, origin, docs, ums: [], undoG: [], redoG: [], busy: false }
    const track = (d, types) => {
      const um = new Y.UndoManager(types, { trackedOrigins: new Set([origin]), captureTimeout: 0 })
      stackCap(um, cap)
      return um
    }
    if (layout === 'A') {
      c.ums = [new Y.UndoManager(Array.from({ length: PAGES }, (_, p) => docs[0].getMap('strokes:' + p)), { trackedOrigins: new Set([origin]), captureTimeout: 0 })]
      stackCap(c.ums[0], cap)
    } else {
      c.ums = docs.map((d) => track(d, d.getMap('strokes')))
      c.ums.forEach((um, p) => um.on('stack-item-added', ({ type }) => {
        if (type !== 'undo' || c.busy) return
        c.undoG.push(p); c.redoG.length = 0
        if (c.undoG.length > cap) c.undoG.splice(0, c.undoG.length - cap)
      }))
    }
    c.map = (p) => layout === 'A' ? c.docs[0].getMap('strokes:' + p) : c.docs[p].getMap('strokes')
    c.draw = (p, id) => c.docs[layout === 'A' ? 0 : p].transact(() => c.map(p).set(id, bytes(id.length)), origin)
    c.erase = (p, id) => c.docs[layout === 'A' ? 0 : p].transact(() => c.map(p).delete(id), origin)
    c.keys = () => { const o = []; for (let p = 0; p < PAGES; p++) c.map(p).forEach((_, k) => o.push(p + ':' + k)); return o.sort() }
    c.undo = () => {
      if (layout === 'A') return c.ums[0].undo()
      const p = c.undoG.pop(); if (p === undefined) return null
      c.busy = true; const r = c.ums[p].undo(); c.busy = false; c.redoG.push(p); return r
    }
    c.redo = () => {
      if (layout === 'A') return c.ums[0].redo()
      const p = c.redoG.pop(); if (p === undefined) return null
      c.busy = true; const r = c.ums[p].redo(); c.busy = false; c.undoG.push(p); return r
    }
    c.undoLen = () => layout === 'A' ? c.ums[0].undoStack.length : c.undoG.length
    c.pageUndoLen = (p) => c.ums[layout === 'A' ? 0 : p].undoStack.length
    c.redoLen = () => layout === 'A' ? c.ums[0].redoStack.length : c.redoG.length
    return c
  }
  let X, Yc
  if (layout === 'A') {
    const dx = new Y.Doc(), dy = new Y.Doc(); dx.clientID = 11; dy.clientID = 22
    link(dx, dy)
    X = mk('X', [dx]); Yc = mk('Y', [dy])
  } else if (layout === 'C') {
    const dxs = [], dys = []
    for (let p = 0; p < PAGES; p++) { const dx = new Y.Doc({ guid: 'page-' + p }), dy = new Y.Doc({ guid: 'page-' + p }); dx.clientID = 11; dy.clientID = 22; link(dx, dy); dxs.push(dx); dys.push(dy) }
    X = mk('X', dxs); Yc = mk('Y', dys)
  } else { // B: root doc with subdocs; Y learns the subdoc guids from the root, then each subdoc pair is linked
    const rx = new Y.Doc(), ry = new Y.Doc(); rx.clientID = 11; ry.clientID = 22
    const rl = link(rx, ry)
    const dxs = []
    for (let p = 0; p < PAGES; p++) { const sd = new Y.Doc({ guid: 'page-' + p }); sd.clientID = 11; rx.getMap('pages').set('page-' + p, sd); dxs.push(sd) }
    rl.xq.forEach((u) => Y.applyUpdate(ry, u, 'remote')); rl.xq.length = 0
    const dys = []
    for (let p = 0; p < PAGES; p++) { const sd = ry.getMap('pages').get('page-' + p); sd.clientID = 22; link(dxs[p], sd); dys.push(sd) }
    X = mk('X', dxs); Yc = mk('Y', dys)
  }
  const deliver = (l, dir, count) => {
    const q = dir ? l.xq : l.yq, target = dir ? l.dy : l.dx
    const n = count ?? q.length
    for (let i = 0; i < n && q.length; i++) Y.applyUpdate(target, q.shift(), 'remote')
  }
  return {
    X, Y: Yc,
    flush: () => { for (let k = 0; k < 3; k++) for (const l of links) { deliver(l, true); deliver(l, false) } },
    // deliver a random amount from random queues (updates arrive late, in order per direction)
    some: (rng) => { for (const l of links) { if (rng() < 0.4) deliver(l, true, 1 + Math.floor(rng() * 3)); if (rng() < 0.4) deliver(l, false, 1 + Math.floor(rng() * 3)) } },
  }
}

export function runUndoChecks(layout) {
  const res = []
  const check = (name, pass, detail) => res.push({ name, pass: !!pass, detail })
  const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b)

  // 1+2: interleaving, per-user undo isolation, redo
  {
    const s = setup(layout, 100), A = s.X, B = s.Y
    A.draw(0, 'a1'); A.draw(1, 'a2'); B.draw(0, 'b1')      // concurrent, unsynced
    A.draw(0, 'a3'); B.draw(1, 'b2'); B.draw(0, 'b3')
    s.flush()
    A.draw(2, 'a4'); s.flush(); B.draw(0, 'b4'); s.flush()
    const bBefore = B.keys().filter((k) => k.includes(':b'))
    A.undo(); A.undo()
    const aHas = A.keys()
    check('A undo x2 removes only A last two strokes (a4,a3), before sync', !aHas.some((k) => /:a[34]$/.test(k)) && ['0:a1', '1:a2', '0:b1', '1:b2', '0:b3', '0:b4'].every((k) => aHas.includes(k)), aHas.join(','))
    s.flush()
    check('after sync B still has all of B strokes; B view equals A view', eq(B.keys().filter((k) => k.includes(':b')), bBefore) && eq(A.keys(), B.keys()), B.keys().join(','))
    B.undo()
    s.flush()
    check('B undo removes only b4, all A strokes remain', !A.keys().includes('0:b4') && ['0:a1', '1:a2', '0:b1', '1:b2', '0:b3'].every((k) => A.keys().includes(k)) && eq(A.keys(), B.keys()), A.keys().join(','))
    A.redo(); s.flush()
    check('A redo brings back a3 (not a4) in both docs', A.keys().includes('0:a3') && !A.keys().includes('2:a4') && eq(A.keys(), B.keys()), A.keys().join(','))
    A.redo(); s.flush()
    check('A second redo brings back a4; B stroke b4 stays undone', A.keys().includes('2:a4') && !A.keys().includes('0:b4') && eq(A.keys(), B.keys()), A.keys().join(','))
    A.undo(); A.draw(0, 'a5')
    check('new stroke after undo clears A redo stack', A.redoLen() === 0, 'redoLen=' + A.redoLen())
  }
  // 3: stack cap
  {
    const cap = 5, s = setup(layout, cap), A = s.X, B = s.Y
    for (let i = 1; i <= 12; i++) { A.draw(0, 'a' + i); if (i % 4 === 0) B.draw(0, 'b' + i / 4) }
    s.flush()
    check(`undo stack capped at ${cap} after 12 strokes (stack length)`, A.undoLen() === cap && A.pageUndoLen(0) === cap, 'undoLen=' + A.undoLen() + ' pageUndoLen=' + A.pageUndoLen(0))
    for (let i = 0; i < 12; i++) A.undo()
    const k = A.keys()
    const removed = []; for (let i = 1; i <= 12; i++) if (!k.includes('0:a' + i)) removed.push('a' + i)
    check('cap drops the oldest: only a8..a12 undoable, a1..a7 stay; B strokes untouched', eq([...removed].sort(), ['a10', 'a11', 'a12', 'a8', 'a9']) && ['b1', 'b2', 'b3'].every((b) => k.includes('0:' + b)), 'removed=' + [...removed].sort().join(','))
    check(`redo stack holds exactly the ${cap} capped entries after 12 undo attempts (redo entries come from the capped undo stack, so the redo trim cannot trigger separately)`, A.redoLen() <= cap && A.redoLen() === cap, 'redoLen=' + A.redoLen())
    for (let i = 0; i < 12; i++) A.redo()
    check('full redo restores the 5 undone strokes', ['a8', 'a9', 'a10', 'a11', 'a12'].every((a) => A.keys().includes('0:' + a)), '')
  }
  // 5: undo of a stroke already erased by the other user
  {
    const s = setup(layout, 100), A = s.X, B = s.Y
    A.draw(0, 'a1'); s.flush(); B.erase(0, 'a1'); s.flush()
    let threw = false; try { A.undo() } catch (e) { threw = true }
    s.flush()
    check('A undo of a stroke B already erased does not throw, does not resurrect it, docs converge', !threw && !A.keys().includes('0:a1') && eq(A.keys(), B.keys()), A.keys().join(','))
    A.draw(0, 'a2'); s.flush(); B.erase(0, 'a2'); s.flush(); B.undo(); s.flush()
    check('B undo of its erase restores A stroke a2 in both docs', A.keys().includes('0:a2') && eq(A.keys(), B.keys()), A.keys().join(','))
  }
  // 4: randomised concurrent run, invariant + convergence
  {
    let violations = 0, nonConv = 0, ops = 0, runs = 25
    for (let seed = 1; seed <= runs; seed++) {
      const rng = mulberry32(seed), s = setup(layout, 8)
      const cl = [s.X, s.Y]; let n = 0
      for (let i = 0; i < 300; i++) {
        const c = cl[rng() < 0.5 ? 0 : 1], r = rng(), other = c === s.X ? s.Y : s.X
        ops++
        if (r < 0.5) c.draw(Math.floor(rng() * PAGES), c.id + (n++))
        else if (r < 0.62) { const mine = c.keys().filter((k) => k.split(':')[1].startsWith(c.id)); if (mine.length) { const k = mine[Math.floor(rng() * mine.length)].split(':'); c.erase(+k[0], k[1]) } }
        else if (r < 0.7) { const theirs = c.keys().filter((k) => k.split(':')[1].startsWith(other.id)); if (theirs.length) { const k = theirs[Math.floor(rng() * theirs.length)].split(':'); c.erase(+k[0], k[1]) } }
        else if (r < 0.86) { const before = c.keys(); c.undo(); const after = c.keys(); const removed = before.filter((k) => !after.includes(k)); if (removed.some((k) => !k.split(':')[1].startsWith(c.id))) violations++ }
        else c.redo()
        if (rng() < 0.5) s.some(rng)
      }
      s.flush()
      if (!eq(s.X.keys(), s.Y.keys())) nonConv++
      // byte-level state equality too
      for (let p = 0; p < (layout === 'A' ? 1 : PAGES); p++) {
        const a = s.X.docs[p], b = s.Y.docs[p]
        if (!eq([...Y.encodeStateVector(a)], [...Y.encodeStateVector(b)])) nonConv++
        const ma = [], mb = []
        for (let q = 0; q < PAGES; q++) { if (layout === 'A' || q === p) { s.X.map(q).forEach((v, k) => ma.push(k + ':' + v.join('.'))); s.Y.map(q).forEach((v, k) => mb.push(k + ':' + v.join('.'))) } }
        if (!eq(ma.sort(), mb.sort())) nonConv++
      }
    }
    check(`random run (${runs} seeds x 300 ops: draw/erase own/erase other's/undo/redo, delayed delivery, cap 8): undo never removed the other user's strokes`, violations === 0, `violations=${violations} over ${ops} ops`)
    check('random run: both clients converge (identical state vectors and stroke bytes) after final exchange', nonConv === 0, `non-converged=${nonConv}`)
  }
  // layout-specific: UndoManager scope
  const notes = []
  if (layout === 'B') {
    const root = new Y.Doc(), pages = root.getMap('pages'), sd = new Y.Doc({ guid: 'p' }); pages.set('p', sd)
    const um = new Y.UndoManager(pages, { trackedOrigins: new Set(['u']), captureTimeout: 0 })
    sd.transact(() => sd.getMap('strokes').set('s', bytes(1)), 'u')
    check('B: UndoManager on the ROOT doc scope does not see subdoc edits (undoStack stays 0); needs one UndoManager per subdoc', um.undoStack.length === 0, 'rootUM undoStack=' + um.undoStack.length)
    const um2 = new Y.UndoManager(sd.getMap('strokes'), { trackedOrigins: new Set(['u']), captureTimeout: 0 })
    sd.transact(() => sd.getMap('strokes').set('t', bytes(1)), 'u'); um2.undo()
    check('B: UndoManager scoped to the subdoc map works for that page', !sd.getMap('strokes').has('t') && sd.getMap('strokes').has('s'), '')
  }
  if (layout === 'C' || layout === 'B') notes.push('No single UndoManager spans several Y.Docs (an UndoManager binds to one doc: typeScope[0].doc). Cross-page undo order needs an app-level stack of page ids on top of one UndoManager per page (done in this test; global ordering and the cap are then app responsibilities).')
  if (layout === 'A') notes.push('One UndoManager spans all pages natively; undo order across pages is automatic.')
  return { checks: res, notes }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  for (const l of ['A', 'B', 'C']) { const r = runUndoChecks(l); console.log('--', l); r.checks.forEach((c) => console.log(c.pass ? 'PASS' : 'FAIL', c.name, '|', c.detail)); r.notes.forEach((n) => console.log('note:', n)) }
}
